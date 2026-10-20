"""Which evidence agents can actually run for the current request.

The planner only offers agents that can run, so a user without a web-search key or a
database never triggers a step that is guaranteed to come back empty.
"""
from __future__ import annotations

from app.config import settings
from app.services.request_context import customer_db_url, tavily_api_key, use_demo_db


def sql_available() -> bool:
    if customer_db_url.get():
        return True
    if use_demo_db.get():
        return bool(settings.demo_database_url)
    # No database chosen: only the app's own database (local development) is left.
    return not settings.require_customer_db


def search_available() -> bool:
    if tavily_api_key.get():
        return True
    if settings.use_mock_search:
        return True
    return settings.search_fallback_to_server_key and bool(settings.tavily_api_key)


def available_agents() -> list[str]:
    agents = ["rag"]
    if sql_available():
        agents.append("sql")
    if search_available():
        agents.append("search")
    return agents
