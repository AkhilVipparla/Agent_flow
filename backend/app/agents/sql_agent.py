from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.base_agent import BaseAgent
from app.graph.state import AgentState, add_warning, append_sql_results
from app.tools.sql_tool import (
    CustomerDatabaseError,
    SQLExecutionError,
    SQLValidationError,
    describe_connection_error,
    execute_sql,
    get_schema_description,
)

logger = logging.getLogger(__name__)

_GENERATION_SYSTEM = """You are a SQL expert. Given a business question and the live database schema below, write a single, safe SELECT query that answers the question.

{schema}

Rules:
- Output ONLY the raw SQL statement. No markdown, no explanation, no code fences.
- Use only SELECT. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Use only tables and columns that appear in the schema above, spelled exactly as shown.
- Do not use semicolons.
- Use table aliases for clarity.
- The question may also ask for outside information (market trends, news, benchmarks). Other
  tools handle that. Write SQL only for the part answerable from the data above, for example
  "which category earns the most revenue" in a question that also asks about its online trend.
- Revenue is not stored directly: compute it from quantity and price columns when both exist.
- Output exactly UNSUPPORTED only when no part of the question can be answered from this schema.
"""

_GENERATION_USER = "Business question: {query}"

_REPAIR_USER = """Business question: {query}

Your previous SQL failed.
SQL: {sql}
Problem: {problem}

Write a corrected single SELECT statement. Output ONLY the raw SQL.
"""

_MAX_ATTEMPTS = 2

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

    async def _write_sql(self, schema: str, query: str, previous: str = "", problem: str = "") -> str:
        user = (
            _REPAIR_USER.format(query=query, sql=previous, problem=problem)
            if previous
            else _GENERATION_USER.format(query=query)
        )
        response = await self._llm.ainvoke([
            ("system", _GENERATION_SYSTEM.format(schema=schema)),
            ("human", user),
        ])
        return _extract_sql(response.content)

    async def run(self, state: AgentState) -> dict[str, Any]:
        query = state["query"]

        # Step 1 - read the live schema
        try:
            schema = await get_schema_description()
        except CustomerDatabaseError as exc:
            logger.info("SQLAgent skipped: %s", exc)
            return add_warning(f"Your database was not used: {exc}")
        except Exception as exc:
            logger.warning("SQLAgent: schema discovery failed: %s", exc)
            return {
                "error": "sql_agent: could not read the database schema",
                "warnings": [describe_connection_error(exc)],
            }

        # Step 2 - write and run the query. One repair attempt: if the database rejects the
        # SQL, the model sees why and tries again before we give up.
        raw_sql = ""
        problem = ""
        rows: list[dict[str, Any]] | None = None
        for attempt in range(_MAX_ATTEMPTS):
            raw_sql = await self._write_sql(schema, query, raw_sql if attempt else "", problem)
            if raw_sql.strip().upper() == "UNSUPPORTED":
                logger.info("SQLAgent: query deemed unsupported by schema: %r", query)
                return add_warning("Your database has no tables that help answer this question.")
            logger.debug("SQLAgent attempt %d SQL: %s", attempt + 1, raw_sql)
            try:
                rows = await execute_sql(raw_sql)
                break
            except SQLValidationError as exc:
                logger.warning("SQLAgent validation failed: %s", exc)
                problem = str(exc)
            except SQLExecutionError as exc:
                logger.warning("SQLAgent execution failed: %s", exc.detail or exc)
                problem = exc.detail or str(exc)
        if rows is None:
            return {
                "error": "sql_agent: could not produce a working query",
                "warnings": ["The database could not be queried for this question (the generated query failed)."],
            }

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
