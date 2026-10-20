"""Per-request user identity and credentials (bring-your-own LLM key and database).

The browser sends these as headers on every request; a middleware stores them in
ContextVars for the lifetime of the request. asyncio tasks copy the context when
created, so background research runs keep the identity and credentials of the
request that started them. Nothing here is persisted or logged.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

# Owner value when no user is logged in. Never matches a real user id, and the auth
# middleware rejects unauthenticated requests before any data is touched.
ANONYMOUS_OWNER = "anonymous"


@dataclass(frozen=True)
class LLMCredentials:
    base_url: str
    api_key: str
    model: str


llm_credentials: ContextVar[LLMCredentials | None] = ContextVar("llm_credentials", default=None)
# Why the LLM headers were unusable (e.g. key without a model), or None. Reported only where
# the LLM is needed, instead of failing every request.
llm_config_error: ContextVar[str | None] = ContextVar("llm_config_error", default=None)
customer_db_url: ContextVar[str | None] = ContextVar("customer_db_url", default=None)
use_demo_db: ContextVar[bool] = ContextVar("use_demo_db", default=False)
tavily_api_key: ContextVar[str | None] = ContextVar("tavily_api_key", default=None)
user_id: ContextVar[str] = ContextVar("user_id", default=ANONYMOUS_OWNER)


def current_owner() -> str:
    """The logged-in user whose data the current request may read and write."""
    return user_id.get()
