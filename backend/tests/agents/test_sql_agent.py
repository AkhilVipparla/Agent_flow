"""The SQL agent must either answer from the database or say why it could not."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import asyncpg
import pytest

from app.agents.sql_agent import SQLAgent
from app.graph.state import initial_state
from app.tools.sql_tool import CustomerDatabaseError, SQLExecutionError

QUESTION = "Which product category brings in the most revenue, and what is its market trend online?"
GOOD_SQL = (
    "SELECT p.category, SUM(oi.quantity * p.unit_price) AS revenue FROM order_items oi "
    "JOIN products p ON p.id = oi.product_id GROUP BY p.category ORDER BY revenue DESC"
)
SCHEMA = "Tables available: ..."


def _agent(*replies: str) -> tuple[SQLAgent, AsyncMock]:
    """An agent whose model answers with `replies` in order (SQL first, then summaries)."""
    llm = AsyncMock()
    llm.ainvoke.side_effect = [SimpleNamespace(content=r) for r in replies]
    agent = SQLAgent()
    agent._injected_llm = llm
    return agent, llm


@pytest.mark.asyncio
async def test_mixed_question_is_answered_from_the_database():
    agent, _ = _agent(GOOD_SQL, "Electronics earns the most revenue.")
    rows = [{"category": "Electronics", "revenue": 180000}]
    with (
        patch("app.agents.sql_agent.get_schema_description", AsyncMock(return_value=SCHEMA)),
        patch("app.agents.sql_agent.execute_sql", AsyncMock(return_value=rows)),
    ):
        update = await agent.run(initial_state(QUESTION))
    assert update["sql_results"][0]["rows"] == rows
    assert "warnings" not in update and "error" not in update


@pytest.mark.asyncio
async def test_prompt_tells_the_model_to_answer_the_data_part_of_mixed_questions():
    agent, llm = _agent(GOOD_SQL, "ok")
    with (
        patch("app.agents.sql_agent.get_schema_description", AsyncMock(return_value=SCHEMA)),
        patch("app.agents.sql_agent.execute_sql", AsyncMock(return_value=[{"a": 1}])),
    ):
        await agent.run(initial_state(QUESTION))
    system = llm.ainvoke.call_args_list[0].args[0][0][1]
    assert "outside information" in system
    assert "only when no part of the question" in system


@pytest.mark.asyncio
async def test_unusable_database_is_reported_not_skipped_silently():
    agent, _ = _agent()
    with patch(
        "app.agents.sql_agent.get_schema_description",
        AsyncMock(side_effect=CustomerDatabaseError("Add your database connection in Settings to use SQL analysis.")),
    ):
        update = await agent.run(initial_state(QUESTION))
    assert "Add your database connection" in update["warnings"][0]


@pytest.mark.asyncio
async def test_rejected_login_gives_a_plain_warning():
    agent, _ = _agent()
    with patch(
        "app.agents.sql_agent.get_schema_description",
        AsyncMock(side_effect=asyncpg.InvalidPasswordError("password authentication failed")),
    ):
        update = await agent.run(initial_state(QUESTION))
    assert "user name or password" in update["warnings"][0]
    assert "password authentication failed" not in update["warnings"][0]
    assert update["error"]


@pytest.mark.asyncio
async def test_unsupported_question_leaves_a_warning():
    agent, _ = _agent("UNSUPPORTED")
    with patch("app.agents.sql_agent.get_schema_description", AsyncMock(return_value=SCHEMA)):
        update = await agent.run(initial_state(QUESTION))
    assert "no tables" in update["warnings"][0]


@pytest.mark.asyncio
async def test_a_failed_query_is_repaired_once_using_the_database_message():
    agent, llm = _agent("SELECT bad FROM nowhere", GOOD_SQL, "Electronics leads.")
    rows = [{"category": "Electronics", "revenue": 1}]
    execute = AsyncMock(
        side_effect=[SQLExecutionError("failed", detail='relation "nowhere" does not exist'), rows]
    )
    with (
        patch("app.agents.sql_agent.get_schema_description", AsyncMock(return_value=SCHEMA)),
        patch("app.agents.sql_agent.execute_sql", execute),
    ):
        update = await agent.run(initial_state(QUESTION))
    assert update["sql_results"][0]["rows"] == rows
    repair_prompt = llm.ainvoke.call_args_list[1].args[0][1][1]
    assert 'relation "nowhere" does not exist' in repair_prompt


@pytest.mark.asyncio
async def test_two_failed_queries_end_with_a_warning_and_no_internal_detail():
    agent, _ = _agent("SELECT 1 FROM a", "SELECT 1 FROM b")
    execute = AsyncMock(
        side_effect=SQLExecutionError("failed", detail='relation "secret_table" does not exist')
    )
    with (
        patch("app.agents.sql_agent.get_schema_description", AsyncMock(return_value=SCHEMA)),
        patch("app.agents.sql_agent.execute_sql", execute),
    ):
        update = await agent.run(initial_state(QUESTION))
    assert update["error"]
    assert update["warnings"] and "secret_table" not in update["warnings"][0]
