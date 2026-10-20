from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

from app.services.net_guard import HostNotAllowedError, assert_public_host
from app.services.request_context import (
    LLMCredentials,
    customer_db_url,
    llm_config_error,
    llm_credentials,
    tavily_api_key,
    use_demo_db,
)

_HEADERS = {
    b"x-llm-base-url": "base_url",
    b"x-llm-api-key": "api_key",
    b"x-llm-model": "model",
    b"x-db-url": "db_url",
    b"x-use-demo-db": "use_demo_db",
    b"x-tavily-api-key": "tavily_api_key",
}


async def _parse_llm(found: dict[str, str]) -> tuple[LLMCredentials | None, str | None]:
    """Turn the LLM headers into credentials, or a message saying what is missing or unsafe."""
    if not found.get("api_key"):
        return None, None
    base_url = found.get("base_url") or "https://api.openai.com/v1"
    model = found.get("model")
    parts = urlsplit(base_url)
    if not model:
        return None, "You saved an API key but no model. Choose a model in Settings."
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None, "The LLM base URL must start with http:// or https://."
    default_port = 443 if parts.scheme == "https" else 80
    try:
        await asyncio.to_thread(assert_public_host, parts.hostname, parts.port or default_port)
    except HostNotAllowedError as exc:
        return None, f"LLM base URL: {str(exc).lower()}"
    return LLMCredentials(base_url=base_url.rstrip("/"), api_key=found["api_key"], model=model), None


class CredentialsMiddleware:
    """Reads the user's LLM key / Tavily key / database URL from request headers into ContextVars.

    Pure ASGI (not BaseHTTPMiddleware) so the ContextVars are visible to the route
    handler and to tasks it spawns. Values are never logged or stored.

    A half-finished LLM setting (a key but no model, say) must NOT fail the request: these
    headers ride on every call, so rejecting here made lists, counts and every page return an
    error, not just research. The problem is recorded instead, and reported only where the LLM
    is actually needed (starting research, the Settings connection test).
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

        creds, problem = await _parse_llm(found)

        llm_token = llm_credentials.set(creds)
        problem_token = llm_config_error.set(problem)
        db_token = customer_db_url.set(found.get("db_url"))
        tavily_token = tavily_api_key.set(found.get("tavily_api_key") or None)
        demo_token = use_demo_db.set(found.get("use_demo_db") == "1")
        try:
            await self.app(scope, receive, send)
        finally:
            use_demo_db.reset(demo_token)
            tavily_api_key.reset(tavily_token)
            customer_db_url.reset(db_token)
            llm_config_error.reset(problem_token)
            llm_credentials.reset(llm_token)
