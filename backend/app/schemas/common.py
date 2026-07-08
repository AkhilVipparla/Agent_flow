from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    """Base for API request/response schemas.

    Fields stay snake_case in Python; JSON in/out is camelCase, matching the
    frontend TypeScript types.
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class AgentStatus(str, Enum):
    running = "running"
    complete = "complete"
    failed = "failed"
    retrying = "retrying"


class ErrorResponse(CamelModel):
    detail: str


class PaginatedResponse(CamelModel, Generic[T]):
    items: list[T]
    total: int
