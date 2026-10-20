from __future__ import annotations

import json
import logging
from urllib.parse import urlsplit

from app.config import settings
from app.services.auth_service import user_for_session
from app.services.postgres_service import get_database_service
from app.services.request_context import user_id

logger = logging.getLogger(__name__)

# Reachable without logging in. Everything else requires a valid session.
_PUBLIC = {
    ("GET", "/health"),
    ("GET", "/ready"),
    ("GET", "/auth/session"),
    ("POST", "/auth/login"),
    ("POST", "/auth/signup"),
    ("POST", "/auth/logout"),
}
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def session_cookie_name() -> str:
    # The __Host- prefix makes browsers insist on Secure + Path=/ + no Domain attribute.
    return "__Host-agentflow_session" if settings.is_production else "agentflow_session"


def read_session_token(headers: list[tuple[bytes, bytes]]) -> str:
    """Find our session cookie, ignoring every other cookie in the header.

    Parsed by hand on purpose. Browsers share cookies across ports on `localhost`, so the
    header often carries cookies from unrelated apps, some with values a strict parser
    (http.cookies.SimpleCookie) rejects, and it then discards the whole header, including
    ours, which signs the user out for no visible reason.
    """
    wanted = session_cookie_name()
    for name, value in headers:
        if name != b"cookie":
            continue
        for pair in value.decode("latin-1").split(";"):
            key, sep, token = pair.strip().partition("=")
            if sep and key == wanted:
                return token.strip().strip('"')
    return ""


def _origin_allowed(headers: list[tuple[bytes, bytes]]) -> bool:
    """CSRF defence for state-changing requests: a browser always sends Origin on
    cross-site POST/DELETE, so reject any origin we don't recognise. Requests with no
    Origin (curl, server-to-server) aren't browser CSRF and are let through."""
    for name, value in headers:
        if name == b"origin":
            origin = value.decode("latin-1").strip().rstrip("/")
            parts = urlsplit(origin)
            normalised = f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else origin
            return normalised in settings.origins
    return True


async def _reject(send, status: int, detail: str) -> None:
    body = json.dumps({"detail": detail}).encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [(b"content-type", b"application/json")],
    })
    await send({"type": "http.response.body", "body": body})


class AuthMiddleware:
    """Resolves the session cookie to a user and scopes the request to that user.

    Sets the user_id ContextVar (which every data query filters on) and puts the user
    on scope["user"]. Unauthenticated requests to protected routes get a 401 before any
    route code runs, so no handler can forget to check.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method, path = scope["method"], scope["path"]
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        if method in _UNSAFE_METHODS and not _origin_allowed(scope["headers"]):
            await _reject(send, 403, "Request origin not allowed.")
            return

        user = None
        token = read_session_token(scope["headers"])
        if token:
            try:
                user = await user_for_session(get_database_service(), token)
            except Exception:
                logger.exception("Session lookup failed")
                await _reject(send, 503, "Service temporarily unavailable.")
                return

        if user is None and (method, path) not in _PUBLIC:
            await _reject(send, 401, "Not authenticated.")
            return

        scope["user"] = user
        ctx_token = user_id.set(user.id if user else "anonymous")
        try:
            await self.app(scope, receive, send)
        finally:
            user_id.reset(ctx_token)
