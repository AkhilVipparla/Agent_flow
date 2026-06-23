from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.base_agent import BaseAgent
from app.graph.state import AgentState, append_sql_results
from app.tools.sql_tool import SQLExecutionError, SQLValidationError, execute_sql

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema context injected into the generation prompt so the LLM knows what
# tables and columns exist. Update this block when the schema evolves.
# ---------------------------------------------------------------------------

_DB_SCHEMA = """
Tables available:
  users          (id UUID, email TEXT, name TEXT, org_id UUID, role TEXT, created_at TIMESTAMPTZ)
  organizations  (id UUID, name TEXT, plan TEXT, created_at TIMESTAMPTZ)
  projects       (id UUID, name TEXT, org_id UUID, created_by UUID, created_at TIMESTAMPTZ)
  reports        (id UUID, project_id UUID, query TEXT, final_report TEXT, confidence_score FLOAT, created_at TIMESTAMPTZ)
  agent_runs     (id UUID, report_id UUID, agent_name TEXT, status TEXT, duration_ms INT, evidence_count INT, created_at TIMESTAMPTZ)
  usage_logs     (id UUID, org_id UUID, report_id UUID, tokens_used INT, cost_usd FLOAT, created_at TIMESTAMPTZ)
"""

_GENERATION_SYSTEM = f"""\
You are a PostgreSQL expert. Given a business question and the database schema below, \
write a single, safe SELECT query that answers the question.

{_DB_SCHEMA}

Rules:
- Output ONLY the raw SQL statement. No markdown, no explanation, no code fences.
- Use only SELECT. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Do not use semicolons.
- Use table aliases for clarity.
- If the question cannot be answered from the schema, output exactly: UNSUPPORTED
"""

_GENERATION_USER = "Business question: {query}"

_SUMMARISE_SYSTEM = """\
You are a data analyst. You have executed a SQL query and received the results below. \
Summarise the findings in 2–4 concise sentences of natural language. \
Include specific numbers and facts from the data. \
Do not mention SQL, tables, or database terminology.
"""

_SUMMARISE_USER = """\
Query that was run: {sql}

Results ({row_count} rows):
{rows_text}

Summarise the key findings.
"""

_CODE_FENCE_RE = re.compile(r"```(?:sql)?(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_sql(raw: str) -> str:
    """Strip markdown fences if the LLM added them despite instructions."""
    match = _CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


class SQLAgent(BaseAgent):
    name = "sql"

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state["query"]

        # Step 1 — generate SQL
        gen_messages = [
            ("system", _GENERATION_SYSTEM),
            ("human", _GENERATION_USER.format(query=query)),
        ]
        gen_response = await self._llm.ainvoke(gen_messages)
        raw_sql = _extract_sql(gen_response.content)

        if raw_sql.strip().upper() == "UNSUPPORTED":
            logger.info("SQLAgent: query deemed unsupported by schema: %r", query)
            return {}

        logger.debug("SQLAgent generated SQL: %s", raw_sql)

        # Step 2 — execute (validation happens inside execute_sql)
        try:
            rows = await execute_sql(raw_sql)
        except SQLValidationError as exc:
            logger.warning("SQLAgent validation failed: %s", exc)
            return {"error": f"sql_agent validation: {exc}"}
        except SQLExecutionError as exc:
            logger.warning("SQLAgent execution failed: %s", exc)
            return {"error": f"sql_agent execution: {exc}"}

        if not rows:
            logger.info("SQLAgent: query returned no rows")
            return append_sql_results([{
                "query": raw_sql,
                "rows": [],
                "summary": "The query returned no results.",
                "row_count": 0,
            }])

        # Step 3 — summarise results with LLM
        rows_text = "\n".join(str(row) for row in rows[:20])  # cap rows sent to LLM
        sum_messages = [
            ("system", _SUMMARISE_SYSTEM),
            (
                "human",
                _SUMMARISE_USER.format(
                    sql=raw_sql,
                    row_count=len(rows),
                    rows_text=rows_text,
                ),
            ),
        ]
        sum_response = await self._llm.ainvoke(sum_messages)
        summary = sum_response.content.strip()

        return append_sql_results([{
            "query": raw_sql,
            "rows": rows,
            "summary": summary,
            "row_count": len(rows),
        }])
