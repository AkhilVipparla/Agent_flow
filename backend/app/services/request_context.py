"""Per-request visitor identity and credentials (bring-your-own LLM key and database).

The browser sends these as headers on every request; a middleware stores them in
ContextVars for the lifetime of the request. asyncio tasks copy the context when
created, so background research runs keep the identity and credentials of the
request that started them. Nothing here is persisted or logged.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

# Owner used when a request carries no visitor ID (local development, tests).
ANONYMOUS_OWNER = "anonymous"


@dataclass(frozen=True)
class LLMCredentials:
    base_url: str
    api_key: str
    model: str


llm_credentials: ContextVar[LLMCredentials | None] = ContextVar("llm_credentials", default=None)
customer_db_url: ContextVar[str | None] = ContextVar("customer_db_url", default=None)
use_demo_db: ContextVar[bool] = ContextVar("use_demo_db", default=False)
visitor_id: ContextVar[str] = ContextVar("visitor_id", default=ANONYMOUS_OWNER)


def current_owner() -> str:
    """The visitor whose data the current request may read and write."""
    return visitor_id.get()
