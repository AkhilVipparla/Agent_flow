from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.dependencies import DbDep
from app.schemas.reports import ReportListResponse, ReportResponse
from app.services.reports_service import delete_report as delete_report_row
from app.services.reports_service import get_report, list_reports

router = APIRouter(tags=["reports"])


@router.get("/reports", response_model=ReportListResponse)
async def list_all_reports(db: DbDep) -> ReportListResponse:
    return await list_reports(db)


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report_by_id(report_id: str, db: DbDep) -> ReportResponse:
    result = await get_report(report_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(report_id: str, db: DbDep) -> None:
    result = await get_report(report_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found")
    await delete_report_row(report_id, db)
