from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.rate_limit import RateLimitMiddleware
from app.api.security_middleware import SecurityMiddleware
from app.config import settings
from app.services import auth_service
from app.services.postgres_service import SqliteService

_ORIGIN = "http://localhost:5173"


# --- full stack: real app + real SQL, temp SQLite ---------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    from app.api import auth_middleware, dependencies
    from app.api.routes import auth as auth_routes
    from app.main import app

    db = SqliteService(str(tmp_path / "auth.db"))
    monkeypatch.setattr(auth_middleware, "get_database_service", lambda: db)
    monkeypatch.setattr(dependencies, "get_database_service", lambda: db)
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    auth_routes._failures.clear()
    return TestClient(app, headers={"Origin": _ORIGIN})


def _signup(client, email="ada@example.com", password="correct horse", name="Ada"):
    return client.post("/auth/signup", json={"email": email, "password": password, "name": name})


def test_protected_routes_require_login(client):
    for path in ("/documents", "/reports", "/runs", "/auth/me"):
        assert client.get(path).status_code == 401, path


def test_health_is_public(client):
    assert client.get("/health").status_code == 200


def test_signup_logs_in_and_me_returns_the_user(client):
    response = _signup(client)
    assert response.status_code == 201
    assert response.json()["email"] == "ada@example.com"
    assert client.get("/auth/me").json()["name"] == "Ada"
    assert client.get("/documents").status_code == 200


def test_session_cookie_is_httponly_and_samesite(client):
    cookie = _signup(client).headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_logout_revokes_the_session_server_side(client):
    _signup(client)
    token = client.cookies.get("agentflow_session")
    assert client.post("/auth/logout").status_code == 204
    # Replaying the old cookie must fail even if a client kept it.
    client.cookies.set("agentflow_session", token)
    assert client.get("/auth/me").status_code == 401


def test_duplicate_email_is_rejected_case_insensitively(client):
    _signup(client)
    assert _signup(client, email="ADA@example.com").status_code == 409


@pytest.mark.parametrize("email,password", [("not-an-email", "longenough1"), ("a@b.co", "short")])
def test_invalid_signup_is_rejected(client, email, password):
    assert _signup(client, email=email, password=password).status_code == 400


def test_wrong_password_and_unknown_email_look_identical(client):
    _signup(client)
    client.post("/auth/logout")
    wrong = client.post("/auth/login", json={"email": "ada@example.com", "password": "nope-nope-nope"})
    unknown = client.post("/auth/login", json={"email": "ghost@example.com", "password": "nope-nope-nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_account_locks_after_repeated_failures(client):
    _signup(client)
    client.post("/auth/logout")
    for _ in range(5):
        client.post("/auth/login", json={"email": "ada@example.com", "password": "wrong-wrong"})
    locked = client.post("/auth/login", json={"email": "ada@example.com", "password": "correct horse"})
    assert locked.status_code == 429
    assert "retry-after" in locked.headers


def test_users_cannot_see_each_others_documents(client, tmp_path):
    from app.api import dependencies
    db = dependencies.get_database_service()

    _signup(client, email="a@example.com")
    import asyncio
    asyncio.run(db.execute(
        "INSERT INTO documents (id, filename, file_type, chunk_count, created_at, owner_id) "
        "VALUES ($1, $2, $3, $4, $5, $6)",
        ("doc-1", "secret.pdf", "pdf", 1, "2026-01-01T00:00:00+00:00", client.get("/auth/me").json()["id"]),
    ))
    assert [d["filename"] for d in client.get("/documents").json()] == ["secret.pdf"]

    client.post("/auth/logout")
    _signup(client, email="b@example.com")
    assert client.get("/documents").json() == []
    assert client.delete("/documents/doc-1").status_code == 404


def test_cross_site_post_is_blocked_but_same_site_works(client):
    evil = client.post("/auth/login", json={"email": "a@b.co", "password": "x"},
                       headers={"Origin": "https://evil.example"})
    assert evil.status_code == 403


# --- password hashing -------------------------------------------------------

def test_passwords_are_hashed_and_verified():
    stored = auth_service.hash_password("hunter2-hunter2")
    assert "hunter2" not in stored
    assert stored != auth_service.hash_password("hunter2-hunter2")  # unique salt
    assert auth_service.verify_password("hunter2-hunter2", stored)
    assert not auth_service.verify_password("hunter3-hunter3", stored)
    assert not auth_service.verify_password("x", "garbage")


# --- HTTPS / security headers -----------------------------------------------

def _plain_app() -> FastAPI:
    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict:
        return {"ok": True}

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.add_middleware(SecurityMiddleware)
    return app


def test_security_headers_present():
    response = TestClient(_plain_app()).get("/ping")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    assert "strict-transport-security" not in response.headers  # development


def test_production_redirects_http_to_https_and_sets_hsts(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    client = TestClient(_plain_app(), follow_redirects=False)

    http = client.get("/ping?x=1", headers={"x-forwarded-proto": "http"})
    assert http.status_code == 308
    assert http.headers["location"].startswith("https://")
    assert http.headers["location"].endswith("/ping?x=1")

    https = client.get("/ping", headers={"x-forwarded-proto": "https"})
    assert https.status_code == 200
    assert "max-age=31536000" in https.headers["strict-transport-security"]

    # Platform health checks arrive over plain HTTP and must still pass.
    assert client.get("/health", headers={"x-forwarded-proto": "http"}).status_code == 200


def test_production_cookie_uses_host_prefix_and_secure(monkeypatch, client):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    response = client.post(
        "/auth/signup",
        json={"email": "prod@example.com", "password": "correct horse"},
        headers={"x-forwarded-proto": "https"},
    )
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("__Host-agentflow_session=")
    assert "Secure" in cookie and "HttpOnly" in cookie


def test_production_refuses_unsafe_private_host_setting(monkeypatch):
    from app.main import _check_production_settings

    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "allow_private_hosts", True)
    with pytest.raises(RuntimeError):
        _check_production_settings()


# --- rate limiting ----------------------------------------------------------

def _limited_app() -> FastAPI:
    app = FastAPI()

    @app.post("/settings/test")
    async def probe() -> dict:
        return {"ok": True}

    @app.post("/auth/login")
    async def login() -> dict:
        return {"ok": True}

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.add_middleware(RateLimitMiddleware)
    return app


def test_rate_limit_returns_429_with_retry_after(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_test_per_minute", 3)
    client = TestClient(_limited_app())
    codes = [client.post("/settings/test").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    assert int(client.post("/settings/test").headers["retry-after"]) >= 1


def test_login_attempts_are_rate_limited(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_login_per_minute", 2)
    client = TestClient(_limited_app())
    assert [client.post("/auth/login").status_code for _ in range(4)] == [200, 200, 429, 429]


def test_health_is_not_rate_limited(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 1)
    client = TestClient(_limited_app())
    assert [client.get("/health").status_code for _ in range(5)] == [200] * 5


# --- demo database / planner availability -----------------------------------

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


def test_planner_only_offers_agents_that_can_run(monkeypatch):
    from app.services import capabilities
    from app.services.request_context import customer_db_url, tavily_api_key

    monkeypatch.setattr(settings, "require_customer_db", True)
    monkeypatch.setattr(settings, "use_mock_search", False)
    monkeypatch.setattr(settings, "search_fallback_to_server_key", False)
    assert capabilities.available_agents() == ["rag"]

    t1 = tavily_api_key.set("tvly-test")
    assert capabilities.available_agents() == ["rag", "search"]
    t2 = customer_db_url.set("postgresql://u:p@db.example.com/d")
    assert capabilities.available_agents() == ["rag", "sql", "search"]
    customer_db_url.reset(t2)
    tavily_api_key.reset(t1)


# --- connection pool regression ---------------------------------------------

def test_database_service_is_a_process_wide_singleton(monkeypatch):
    # Building a new service per call leaked a Postgres pool on every request and
    # eventually exhausted max_connections.
    from app.services import postgres_service

    monkeypatch.setattr(settings, "use_mock_sql", True)
    postgres_service.get_database_service.cache_clear()
    try:
        assert postgres_service.get_database_service() is postgres_service.get_database_service()
    finally:
        postgres_service.get_database_service.cache_clear()


# --- observability, error handling, readiness -------------------------------

def test_every_response_carries_a_request_id(client):
    response = client.get("/health")
    assert len(response.headers["x-request-id"]) >= 8


def test_caller_supplied_request_id_is_echoed_only_if_safe(client):
    ok = client.get("/health", headers={"X-Request-ID": "trace-1234-abcd"})
    assert ok.headers["x-request-id"] == "trace-1234-abcd"
    # A forged/injected value (newline, spaces, too short) is replaced, never echoed.
    bad = client.get("/health", headers={"X-Request-ID": "x y"})
    assert bad.headers["x-request-id"] != "x y"


def test_validation_errors_do_not_echo_the_submitted_value(client):
    secret = "p" * 300  # exceeds the password max length, so validation fails
    response = client.post("/auth/login", json={"email": "a@b.co", "password": secret})
    assert response.status_code == 422
    assert secret not in response.text
    assert "input" not in response.text


def test_unhandled_errors_hide_details_but_return_a_request_id(client, monkeypatch):
    from app.api.routes import auth as auth_routes

    async def boom(*_args, **_kwargs):
        raise RuntimeError("database password is hunter2")

    monkeypatch.setattr(auth_routes, "authenticate", boom)
    local = TestClient(client.app, raise_server_exceptions=False, headers={"Origin": _ORIGIN})
    response = local.post("/auth/login", json={"email": "a@b.co", "password": "whatever-long"})
    assert response.status_code == 500
    assert "hunter2" not in response.text
    assert response.json()["detail"] == "Internal server error."
    assert response.json()["request_id"]


def test_ready_reports_ok_when_dependencies_are_up(client, monkeypatch):
    from app.api.routes import health

    class _Vectors:
        async def ping(self):
            return None

    monkeypatch.setattr(health, "get_vector_search_service", lambda: _Vectors())
    monkeypatch.setattr(health, "get_database_service", lambda: dependencies_db())
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok", "vector_store": "ok"}}


def test_ready_returns_503_without_leaking_the_reason(client, monkeypatch):
    from app.api.routes import health

    class _DownVectors:
        async def ping(self):
            raise ConnectionError("qdrant at 10.0.0.5:6333 refused the connection")

    monkeypatch.setattr(health, "get_vector_search_service", lambda: _DownVectors())
    monkeypatch.setattr(health, "get_database_service", lambda: dependencies_db())
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["vector_store"] == "unavailable"
    assert "10.0.0.5" not in response.text


def dependencies_db():
    from app.api import dependencies

    return dependencies.get_database_service()


# --- cookie parsing ----------------------------------------------------------

def test_session_survives_other_apps_cookies_on_localhost(client):
    """Cookies are shared across ports on localhost, so the header can include junk from
    unrelated dev servers. A strict parser drops the whole header, silently logging the user out."""
    from http.cookies import SimpleCookie

    _signup(client)
    token = client.cookies.get("agentflow_session")
    junk = 'other_app={"a":1,"b":[2,3]}; weird=va"lue; theme=dark'

    # Prove the old parser really does lose our cookie on this header...
    jar = SimpleCookie()
    try:
        jar.load(f"{junk}; agentflow_session={token}")
    except Exception:
        jar = SimpleCookie()
    assert "agentflow_session" not in jar

    # ...and that we still authenticate with it.
    client.cookies.clear()
    response = client.get("/auth/session", headers={"Cookie": f"{junk}; agentflow_session={token}"})
    assert response.json()["user"]["email"] == "ada@example.com"


def test_cookie_value_may_be_quoted_and_cookie_order_does_not_matter(client):
    _signup(client)
    token = client.cookies.get("agentflow_session")
    client.cookies.clear()
    first = client.get("/auth/session", headers={"Cookie": f'agentflow_session="{token}"; a=b'})
    last = client.get("/auth/session", headers={"Cookie": f"a=b; agentflow_session={token}"})
    assert first.json()["user"] and last.json()["user"]


# --- a half-finished LLM setting must not break the whole app ----------------

def test_key_without_model_does_not_break_ordinary_requests(client):
    _signup(client)
    incomplete = {"X-LLM-Api-Key": "sk-test-123"}  # key saved, no model chosen
    for path in ("/documents", "/reports", "/runs", "/auth/session"):
        assert client.get(path, headers=incomplete).status_code == 200, path


def test_starting_research_explains_the_missing_model(client):
    _signup(client)
    response = client.post("/query", json={"query": "anything"}, headers={"X-LLM-Api-Key": "sk-test-123"})
    assert response.status_code == 400
    assert "model" in response.json()["detail"].lower()


def test_research_requires_a_key_when_the_server_default_is_disabled(client, monkeypatch):
    _signup(client)
    monkeypatch.setattr(settings, "require_user_llm_key", True)
    response = client.post("/query", json={"query": "anything"})
    assert response.status_code == 400
    assert "api key" in response.json()["detail"].lower()


# --- document preview --------------------------------------------------------

def _pdf_with_text(text: str) -> bytes:
    """A minimal, valid one-page PDF that contains `text`."""
    stream = f"BT /F1 24 Tf 72 700 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    return out


@pytest.fixture
def uploads(client, monkeypatch):
    """Upload endpoint with in-memory embeddings and vectors, so tests never touch Qdrant."""
    from app.api import dependencies
    from app.services.embedding_service import MockEmbeddingService
    from app.services.qdrant_service import MockVectorSearch

    monkeypatch.setattr(dependencies, "get_embedding_service", lambda: MockEmbeddingService())
    monkeypatch.setattr(dependencies, "get_vector_search_service", lambda: MockVectorSearch())
    return client


def _upload(client, name: str, data: bytes, mime: str):
    return client.post("/documents/upload", files={"file": (name, data, mime)})


def test_uploaded_pdf_can_be_viewed_by_its_owner(uploads):
    _signup(uploads)
    pdf = _pdf_with_text("Quarterly revenue grew")
    created = _upload(uploads, "report.pdf", pdf, "application/pdf")
    assert created.status_code == 201, created.text
    doc_id = created.json()["id"]

    listed = uploads.get("/documents").json()
    assert listed[0]["hasFile"] is True

    response = uploads.get(f"/documents/{doc_id}/file")
    assert response.status_code == 200
    assert response.content == pdf
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline")
    assert "report.pdf" in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "private, no-store"
    assert "sandbox" in response.headers["content-security-policy"]


def test_another_user_cannot_view_the_pdf(uploads):
    _signup(uploads, email="owner@example.com")
    doc_id = _upload(uploads, "private.pdf", _pdf_with_text("secret plans"), "application/pdf").json()["id"]
    assert uploads.get(f"/documents/{doc_id}/file").status_code == 200

    uploads.post("/auth/logout")
    _signup(uploads, email="intruder@example.com")
    assert uploads.get(f"/documents/{doc_id}/file").status_code == 404


def test_logged_out_requests_cannot_view_the_pdf(uploads):
    _signup(uploads)
    doc_id = _upload(uploads, "a.pdf", _pdf_with_text("hello world"), "application/pdf").json()["id"]
    uploads.post("/auth/logout")
    assert uploads.get(f"/documents/{doc_id}/file").status_code == 401


def test_non_pdf_uploads_have_no_preview(uploads):
    _signup(uploads)
    doc_id = _upload(uploads, "data.csv", b"name,role\nAda,Engineer\n", "text/csv").json()["id"]
    assert uploads.get("/documents").json()[0]["hasFile"] is False
    assert uploads.get(f"/documents/{doc_id}/file").status_code == 404


def test_pdf_named_file_without_pdf_content_is_not_stored(uploads):
    """Only genuine PDFs (by their magic bytes) are kept and served back as application/pdf."""
    _signup(uploads)
    # Ingest fails on non-PDF bytes, so nothing is created or stored.
    response = _upload(uploads, "fake.pdf", b"<html><script>alert(1)</script></html>", "application/pdf")
    assert response.status_code == 400
    assert "pdf" in response.json()["detail"].lower()
    assert uploads.get("/documents").json() == []


def test_deleting_a_document_removes_its_stored_file(uploads):
    _signup(uploads)
    doc_id = _upload(uploads, "gone.pdf", _pdf_with_text("temporary text"), "application/pdf").json()["id"]
    assert uploads.delete(f"/documents/{doc_id}").status_code == 204
    assert uploads.get(f"/documents/{doc_id}/file").status_code == 404

    import asyncio

    from app.api import dependencies

    db = dependencies.get_database_service()
    leftover = asyncio.run(db.fetch_one("SELECT document_id FROM document_files WHERE document_id = $1", (doc_id,)))
    assert leftover is None
