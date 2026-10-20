from __future__ import annotations

import asyncio
import json
import re
from urllib.parse import urlsplit

from app.config import settings
from app.services.net_guard import HostNotAllowedError, assert_public_host
from app.services.request_context import (
    ANONYMOUS_OWNER,
    LLMCredentials,
    customer_db_url,
    llm_credentials,
    use_demo_db,
    visitor_id,
)

_HEADERS = {
    b"x-llm-base-url": "base_url",
    b"x-llm-api-key": "api_key",
    b"x-llm-model": "model",
    b"x-db-url": "db_url",
    b"x-visitor-id": "visitor_id",
    b"x-use-demo-db": "use_demo_db",
}

# Browser-generated random UUID. Unguessable, so it acts as the visitor's private key.
_VISITOR_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class CredentialsMiddleware:
    """Reads the visitor's LLM key / database URL from request headers into ContextVars.

    Pure ASGI (not BaseHTTPMiddleware) so the ContextVars are visible to the route
    handler and to tasks it spawns. Values are never logged or stored.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        found: dict[str, str] = {}
        for name, value in scope["headers"]:
            key = _HEADERS.get(name)
            if key and value:
                found[key] = value.decode("latin-1").strip()

        error = None
        creds = None
        owner = ANONYMOUS_OWNER
        raw_owner = found.get("visitor_id", "").lower()
        if raw_owner:
            if _VISITOR_ID_RE.match(raw_owner):
                owner = raw_owner
            else:
                error = "Invalid X-Visitor-Id."
        elif settings.require_visitor_id and scope["method"] != "OPTIONS" and scope["path"] != "/health":
            error = "Missing X-Visitor-Id."
        if not error and found.get("api_key"):
            base_url = found.get("base_url") or "https://api.openai.com/v1"
            model = found.get("model")
            parts = urlsplit(base_url)
            if not model:
                error = "Set a model name in Settings."
            elif parts.scheme not in ("http", "https") or not parts.hostname:
                error = "LLM base URL must start with http:// or https://."
            else:
                default_port = 443 if parts.scheme == "https" else 80
                try:
                    await asyncio.to_thread(assert_public_host, parts.hostname, parts.port or default_port)
                    creds = LLMCredentials(base_url=base_url.rstrip("/"), api_key=found["api_key"], model=model)
                except HostNotAllowedError as exc:
                    error = f"LLM base URL: {str(exc).lower()}"

        if error:
            body = json.dumps({"detail": error}).encode()
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"access-control-allow-origin", b"*"),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        llm_token = llm_credentials.set(creds)
        db_token = customer_db_url.set(found.get("db_url"))
        owner_token = visitor_id.set(owner)
        demo_token = use_demo_db.set(found.get("use_demo_db") == "1")
        try:
            await self.app(scope, receive, send)
        finally:
            use_demo_db.reset(demo_token)
            visitor_id.reset(owner_token)
            customer_db_url.reset(db_token)
            llm_credentials.reset(llm_token)
