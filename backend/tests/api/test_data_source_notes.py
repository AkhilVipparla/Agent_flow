"""A run that finished its report is complete, and gaps in the evidence are stated in it."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import asyncpg
import pytest
from fastapi import HTTPException

from app.api.routes.research import submit_query
from app.schemas.research import ResearchRequest
from app.services.request_context import customer_db_url
from app.services.research_service import _render_report_markdown, _unique_warnings
from app.tools.sql_tool import check_database, describe_connection_error

REPORT = json.dumps({"executive_summary": "Summary.", "key_findings": ["One."], "citations": []})


def test_notes_appear_in_the_markdown_and_in_the_report_findings():
    markdown, fields = _render_report_markdown(REPORT, ["Your database was not used: login rejected."])
    assert "## Data availability" in markdown
    assert "- Your database was not used: login rejected." in markdown
    assert fields["key_findings"][-1].startswith("Note: Your database was not used")


def test_no_notes_leaves_the_report_unchanged():
    markdown, fields = _render_report_markdown(REPORT, [])
    assert "Data availability" not in markdown
    assert fields["key_findings"] == ["One."]


def test_repeated_notes_from_a_retry_are_listed_once():
    assert _unique_warnings({"warnings": ["a", "b", "a"]}) == ["a", "b"]


@pytest.mark.asyncio
async def test_no_database_chosen_means_nothing_to_check():
    assert await check_database() is None


@pytest.mark.asyncio
async def test_a_rejected_login_is_found_before_the_run_starts():
    token = customer_db_url.set("postgresql://u:wrong@db.example.com:5432/shop")
    try:
        with (
            patch("app.tools.sql_tool.validate_customer_db_url", lambda u: u),
            patch("app.tools.sql_tool._customer_service") as svc,
        ):
            svc.return_value.fetch_many = AsyncMock(side_effect=asyncpg.InvalidPasswordError("nope"))
            problem = await check_database()
    finally:
        customer_db_url.reset(token)
    assert problem and "user name or password" in problem


@pytest.mark.asyncio
async def test_query_endpoint_refuses_to_start_when_the_chosen_database_is_unusable():
    with (
        patch("app.api.routes.research.llm_unavailable_reason", return_value=None),
        patch(
            "app.api.routes.research.check_database",
            AsyncMock(return_value="The database rejected the user name or password."),
        ),
        patch("app.api.routes.research.start_research", AsyncMock()) as start,
    ):
        with pytest.raises(HTTPException) as err:
            await submit_query(ResearchRequest(query="What is our revenue?"), db=object())
    assert err.value.status_code == 400
    assert "user name or password" in err.value.detail
    start.assert_not_awaited()


def test_connection_errors_have_plain_explanations():
    assert "reach the database host" in describe_connection_error(OSError("refused"))
    assert "does not exist" in describe_connection_error(asyncpg.InvalidCatalogNameError("x"))
