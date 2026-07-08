from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, health, reports, research


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.qdrant_service import get_vector_search_service
    await get_vector_search_service().ensure_collection()
    yield


app = FastAPI(title="AgentFlow AI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(reports.router)
app.include_router(documents.router)
