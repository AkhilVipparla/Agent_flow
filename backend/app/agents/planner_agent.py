from __future__ import annotations

from typing import Any

from app.agents.base_agent import BaseAgent
from app.graph.state import AgentState, update_execution_plan
from app.schemas.agents import ExecutionPlan

_AVAILABLE_AGENTS = ["rag", "sql", "search", "file"]

_SYSTEM_PROMPT = """\
You are a research planning agent. Your job is to analyze a user query and decide \
which specialized agents are needed to answer it, then explain your reasoning.

Available agents:
- rag    : Retrieve information from the enterprise knowledge base (internal documents, policies, reports).
- sql    : Query structured business data from the relational database (metrics, transactions, records).
- search : Fetch current external information from the web.
- file   : Analyze uploaded files such as PDFs or spreadsheets.

Rules:
1. Select only the agents genuinely required by the query. Do not include agents that would not contribute.
2. Always include at least one agent.
3. Return valid JSON that matches this exact schema:
   {"agents": ["<agent_name>", ...], "reasoning": "<one sentence explaining your choices>"}
4. Agent names must be chosen exclusively from: rag, sql, search, file.
"""

_USER_TEMPLATE = "Query: {query}"


class PlannerAgent(BaseAgent):
    name = "planner"

    def __init__(self) -> None:
        super().__init__()
        self._structured_llm = self._llm.with_structured_output(ExecutionPlan)

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state["query"]

        messages = [
            ("system", _SYSTEM_PROMPT),
            ("human", _USER_TEMPLATE.format(query=query)),
        ]

        plan: ExecutionPlan = await self._structured_llm.ainvoke(messages)

        # Guard: keep only recognised agent names
        plan.agents = [a for a in plan.agents if a in _AVAILABLE_AGENTS]
        if not plan.agents:
            plan.agents = ["rag"]

        return update_execution_plan(plan)
