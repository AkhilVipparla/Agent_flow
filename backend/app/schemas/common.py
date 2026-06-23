from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class AgentStatus(str, Enum):
    running = "running"
    complete = "complete"
    failed = "failed"
    retrying = "retrying"


class ErrorResponse(BaseModel):
    detail: str


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
