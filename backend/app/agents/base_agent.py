from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_groq import ChatGroq

from app.graph.state import AgentState
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for all LangGraph agents."""

    name: str = "base"

    def __init__(self) -> None:
        self._llm: ChatGroq = get_llm()

    @abstractmethod
    async def run(self, state: AgentState) -> dict[str, Any]:
        """Execute agent logic and return a partial state update dict."""
        ...

    async def safe_run(self, state: AgentState) -> dict[str, Any]:
        """Wraps run() with error capture so the graph never crashes."""
        try:
            return await self.run(state)
        except Exception as exc:
            logger.exception("%s failed: %s", self.name, exc)
            return {"error": f"{self.name} failed: {exc}"}
