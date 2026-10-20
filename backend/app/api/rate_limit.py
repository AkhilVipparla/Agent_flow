from __future__ import annotations

import json
import math
import time
from collections import defaultdict, deque

from app.config import settings

_MINUTE = 60.0
_HOUR = 3600.0
_MAX_TRACKED_KEYS = 20_000


def _client_ip(scope) -> str:
    if settings.trust_proxy_headers:
        for name, value in scope["headers"]:
            if name == b"x-forwarded-for" and value:
                # First hop is the original client; later hops are our own proxies.
                return value.decode("latin-1").split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


def _rules_for(method: str, path: str) -> list[tuple[str, int, float]]:
    """(bucket name, max requests, window seconds) that apply to this request."""
    if method == "OPTIONS" or path == "/health":
        return []
    rules = [("all", settings.rate_limit_per_minute, _MINUTE)]
    if method == "POST" and path == "/query":
        rules += [
            ("query-min", settings.rate_limit_query_per_minute, _MINUTE),
            ("query-hour", settings.rate_limit_query_per_hour, _HOUR),
        ]
    elif method == "POST" and path == "/documents/upload":
        rules.append(("upload-hour", settings.rate_limit_upload_per_hour, _HOUR))
    elif method == "POST" and path == "/settings/test":
        rules.append(("test-min", settings.rate_limit_test_per_minute, _MINUTE))
    return rules


class RateLimitMiddleware:
    """In-memory sliding-window limiter keyed by client IP.

    Keyed by IP rather than visitor ID on purpose: a visitor ID is client-chosen,
    so keying on it would let anyone dodge the limit by sending a new one.
    State is per server process; run behind a shared store (e.g. Redis) if you
    scale to several instances.
    """

    def __init__(self, app) -> None:
        self.app = app
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def _check(self, ip: str, rules: list[tuple[str, int, float]]) -> int | None:
        """Record the request; return seconds to wait if any rule is exceeded."""
        now = time.monotonic()
        if len(self._hits) > _MAX_TRACKED_KEYS:
            self._hits.clear()  # crude memory bound against many-IP floods
        wait = 0.0
        # Check every rule before recording, so a rejected request doesn't use up quota.
        for name, limit, window in rules:
            hits = self._hits[(ip, name)]
            while hits and now - hits[0] >= window:
                hits.popleft()
            if len(hits) >= limit:
                wait = max(wait, window - (now - hits[0]))
        if wait > 0:
            return max(1, math.ceil(wait))
        for name, _limit, _window in rules:
            self._hits[(ip, name)].append(now)
        return None

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or not settings.rate_limit_enabled:
            await self.app(scope, receive, send)
            return

        rules = _rules_for(scope["method"], scope["path"])
        retry_after = self._check(_client_ip(scope), rules) if rules else None
        if retry_after is None:
            await self.app(scope, receive, send)
            return

        body = json.dumps({"detail": f"Too many requests. Try again in {retry_after} seconds."}).encode()
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"application/json"),
                (b"retry-after", str(retry_after).encode()),
                (b"access-control-allow-origin", b"*"),
            ],
        })
        await send({"type": "http.response.body", "body": body})
