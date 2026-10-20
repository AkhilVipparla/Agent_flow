from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.context_middleware import CredentialsMiddleware
from app.api.rate_limit import RateLimitMiddleware
from app.api.routes import documents, health, reports, research, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.qdrant_service import get_vector_search_service
    await get_vector_search_service().ensure_collection()
    from app.services.postgres_service import get_database_service
    from app.services.research_service import fail_orphaned_runs
    await fail_orphaned_runs(get_database_service())
    yield


app = FastAPI(title="AgentFlow AI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Outermost: its own 400 responses add the CORS header themselves.
app.add_middleware(CredentialsMiddleware)
# Outermost of all: reject floods before doing any work.
app.add_middleware(RateLimitMiddleware)

app.include_router(health.router)
app.include_router(settings.router)
app.include_router(research.router)
app.include_router(reports.router)
app.include_router(documents.router)
