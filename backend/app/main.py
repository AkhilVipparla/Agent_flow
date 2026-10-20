from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth_middleware import AuthMiddleware
from app.api.context_middleware import CredentialsMiddleware
from app.api.rate_limit import RateLimitMiddleware
from app.api.routes import auth, documents, health, reports, research, settings
from app.api.security_middleware import SecurityMiddleware
from app.config import settings as app_settings
from app.observability import RequestContextMiddleware, configure_logging, request_id

configure_logging()
logger = logging.getLogger(__name__)


def _check_production_settings() -> None:
    """Refuse to start in production with settings that would expose users or the server."""
    if not app_settings.is_production:
        return
    if app_settings.allow_private_hosts:
        raise RuntimeError("ALLOW_PRIVATE_HOSTS must be false in production (SSRF protection).")
    if not app_settings.trust_proxy_headers:
        logger.warning(
            "ENVIRONMENT=production but TRUST_PROXY_HEADERS is false: behind a platform proxy, "
            "HTTPS detection and per-IP rate limits will not work correctly."
        )
    if app_settings.origins and any(o.startswith("http://localhost") for o in app_settings.origins):
        logger.warning("ALLOWED_ORIGINS still contains localhost; set it to your public frontend URL.")
    if not app_settings.require_customer_db:
        logger.warning("REQUIRE_CUSTOMER_DB is false: the SQL agent may read the app database.")
    if app_settings.use_mock_search or app_settings.use_mock_sql or app_settings.use_mock_vector_search:
        logger.warning("One or more USE_MOCK_* settings are true in production.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _check_production_settings()
    from app.services.qdrant_service import get_vector_search_service
    await get_vector_search_service().ensure_collection()
    from app.services.postgres_service import get_database_service
    from app.services.research_service import fail_orphaned_runs
    await fail_orphaned_runs(get_database_service())
    yield
    # Orderly shutdown: let in-flight runs finish (or cancel them cleanly), then release connections.
    from app.services.research_service import drain_background_runs
    from app.tools.sql_tool import close_customer_pools

    await drain_background_runs()
    await close_customer_pools()
    await get_vector_search_service().close()
    await get_database_service().close()


_prod = app_settings.is_production
app = FastAPI(
    title="AgentFlow AI",
    version="0.1.0",
    lifespan=lifespan,
    # The interactive docs list every route; don't publish them on a live server.
    docs_url=None if _prod else "/docs",
    redoc_url=None if _prod else "/redoc",
    openapi_url=None if _prod else "/openapi.json",
)

# Middleware runs outermost-first in the reverse of the order added here:
# rate limit -> HTTPS/security headers -> CORS -> authentication -> request credentials -> routes.
app.add_middleware(CredentialsMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    # The browser normally reaches the API same-origin through the frontend host's proxy,
    # so this is only for direct cross-origin use (local development without the proxy).
    allow_origins=app_settings.origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "X-LLM-Api-Key", "X-LLM-Base-Url", "X-LLM-Model",
        "X-DB-Url", "X-Use-Demo-Db", "X-Tavily-Api-Key",
    ],
)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware)
# Outermost of everything: every response, including 429s and auth failures, carries a request ID.
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    """Anything unexpected: log the detail server-side, tell the client only the request ID."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error.", "request_id": request_id.get()},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI's default 422 echoes the submitted value (`input`), which would reflect a
    password back in the response body. Return only where and why it failed."""
    errors = [
        {"loc": list(e.get("loc", ())), "msg": e.get("msg", "Invalid value"), "type": e.get("type", "")}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(settings.router)
app.include_router(research.router)
app.include_router(reports.router)
app.include_router(documents.router)
