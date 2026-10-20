"""Structured logging and per-request tracing.

Every request gets an ID (accepted from the caller or generated), returned in the
`X-Request-ID` header and attached to every log line written while handling it, so one
user report can be traced through the logs. In production logs are single-line JSON that
log platforms can index; in development they stay human-readable.

Deliberately never logged: request or response bodies, headers (they carry API keys and
database passwords), cookies, and query strings.
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime

from app.config import settings

request_id: ContextVar[str] = ContextVar("request_id", default="-")

# Callers may supply their own ID (e.g. from a load balancer); accept only a safe shape so
# it can't be used to forge log lines.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for key in ("method", "path", "status", "duration_ms", "user"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())
    if settings.is_production:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)-5s %(name)s [%(request_id)s] %(message)s"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    # We log one access line per request ourselves, with the request ID; silence uvicorn's
    # duplicate (which also includes query strings).
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn.error").handlers = []


_access_log = logging.getLogger("app.access")


class RequestContextMiddleware:
    """Assigns the request ID and writes one access-log line per request."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied = next((v.decode("latin-1") for k, v in scope["headers"] if k == b"x-request-id"), "")
        rid = supplied if _VALID_REQUEST_ID.match(supplied) else uuid.uuid4().hex
        token = request_id.set(rid)
        started = time.perf_counter()
        status = 500

        async def send_with_id(message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message = {**message, "headers": [*message.get("headers", []), (b"x-request-id", rid.encode())]}
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            user = scope.get("user")
            # Health probes fire every few seconds; logging them only buries real traffic.
            if scope["path"] not in ("/health", "/ready"):
                _access_log.info(
                    "%s %s -> %s",
                    scope["method"],
                    scope["path"],
                    status,
                    extra={
                        "method": scope["method"],
                        "path": scope["path"],
                        "status": status,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                        "user": user.id[:8] if user else None,
                    },
                )
            request_id.reset(token)
