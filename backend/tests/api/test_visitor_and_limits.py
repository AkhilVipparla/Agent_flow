from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.context_middleware import CredentialsMiddleware
from app.api.rate_limit import RateLimitMiddleware
from app.config import settings
from app.services.request_context import current_owner

_A = "11111111-1111-4111-8111-111111111111"


def _app() -> FastAPI:
    app = FastAPI()

    @app.get("/whoami")
    async def whoami() -> dict:
        return {"owner": current_owner()}

    @app.post("/settings/test")
    async def probe() -> dict:
        return {"ok": True}

    app.add_middleware(CredentialsMiddleware)
    app.add_middleware(RateLimitMiddleware)
    return app


def test_visitor_id_becomes_the_owner():
    client = TestClient(_app())
    assert client.get("/whoami", headers={"X-Visitor-Id": _A}).json() == {"owner": _A}


def test_missing_visitor_id_falls_back_to_anonymous():
    assert TestClient(_app()).get("/whoami").json() == {"owner": "anonymous"}


def test_malformed_visitor_id_is_rejected():
    response = TestClient(_app()).get("/whoami", headers={"X-Visitor-Id": "../../etc/passwd"})
    assert response.status_code == 400


def test_visitor_id_required_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "require_visitor_id", True)
    assert TestClient(_app()).get("/whoami").status_code == 400


def test_rate_limit_returns_429_with_retry_after(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_test_per_minute", 3)
    client = TestClient(_app())
    codes = [client.post("/settings/test").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    blocked = client.post("/settings/test")
    assert int(blocked.headers["retry-after"]) >= 1


def test_changing_visitor_id_does_not_bypass_rate_limit(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_test_per_minute", 2)
    client = TestClient(_app())
    ids = [f"{i}1111111-1111-4111-8111-111111111111" for i in range(4)]
    codes = [client.post("/settings/test", headers={"X-Visitor-Id": v}).status_code for v in ids]
    assert codes == [200, 200, 429, 429]


@pytest.mark.parametrize("path", ["/health"])
def test_health_is_not_rate_limited(monkeypatch, path):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 1)
    app = _app()

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    client = TestClient(app)
    assert [client.get(path).status_code for _ in range(5)] == [200] * 5


# --- demo database ---------------------------------------------------------

def test_demo_header_sets_context():
    from app.services.request_context import use_demo_db

    app = _app()

    @app.get("/demo-flag")
    async def demo_flag() -> dict:
        return {"demo": use_demo_db.get()}

    client = TestClient(app)
    assert client.get("/demo-flag", headers={"X-Use-Demo-Db": "1"}).json() == {"demo": True}
    assert client.get("/demo-flag").json() == {"demo": False}


def test_demo_preview_reports_unavailable_when_not_configured(monkeypatch):
    from app.api.routes import settings as settings_routes

    monkeypatch.setattr(settings, "demo_database_url", "")
    monkeypatch.setattr(settings_routes, "_demo_cache", None)
    app = FastAPI()
    app.include_router(settings_routes.router)
    assert TestClient(app).get("/settings/demo").json() == {"available": False, "tables": []}


@pytest.mark.asyncio
async def test_demo_choice_without_server_demo_db_skips_sql(monkeypatch):
    from app.services.request_context import use_demo_db
    from app.tools.sql_tool import CustomerDatabaseError, _get_service

    monkeypatch.setattr(settings, "demo_database_url", "")
    token = use_demo_db.set(True)
    try:
        with pytest.raises(CustomerDatabaseError):
            _get_service()
    finally:
        use_demo_db.reset(token)
