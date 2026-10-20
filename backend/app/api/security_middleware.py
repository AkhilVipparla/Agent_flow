from __future__ import annotations

from app.config import settings

_SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
    # API responses hold one user's private data; never let a shared cache keep them.
    (b"cache-control", b"no-store"),
]
_PROBE_PATHS = ("/health", "/ready")
_HSTS = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")


def _request_scheme(scope) -> str:
    if settings.trust_proxy_headers:
        for name, value in scope["headers"]:
            if name == b"x-forwarded-proto" and value:
                return value.decode("latin-1").split(",")[0].strip().lower()
    return scope.get("scheme", "http")


class SecurityMiddleware:
    """Enforces HTTPS in production and adds security headers to every response."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Platform health checks hit the container over plain HTTP, so /health is exempt.
        if settings.is_production and scope["path"] not in _PROBE_PATHS and _request_scheme(scope) != "https":
            host = next((v.decode("latin-1") for k, v in scope["headers"] if k == b"host"), "")
            query = scope.get("query_string", b"").decode("latin-1")
            location = f"https://{host}{scope['path']}" + (f"?{query}" if query else "")
            await send({"type": "http.response.start", "status": 308,
                        "headers": [(b"location", location.encode("latin-1"))]})
            await send({"type": "http.response.body", "body": b""})
            return

        async def send_with_headers(message) -> None:
            if message["type"] == "http.response.start":
                existing = {k.lower() for k, _ in message.get("headers", [])}
                extra = [h for h in _SECURITY_HEADERS if h[0] not in existing]
                if settings.is_production:
                    extra.append(_HSTS)
                message = {**message, "headers": [*message.get("headers", []), *extra]}
            await send(message)

        await self.app(scope, receive, send_with_headers)
