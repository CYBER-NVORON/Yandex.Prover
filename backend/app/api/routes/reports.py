from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReportResponse
from app.services.report_builder import build_markdown_report
from app.services.storage_service import StorageError, get_analysis_result


router = APIRouter(prefix="/api/analyses", tags=["reports"])


@router.get("/{analysis_id}/report", response_model=ReportResponse)
def get_report(analysis_id: str, db: Session = Depends(get_db)) -> ReportResponse:
    result = _load_result_or_404(db, analysis_id)
    return ReportResponse(analysis_id=analysis_id, markdown=build_markdown_report(result))


@router.get("/{analysis_id}/report/download")
def download_report(analysis_id: str, db: Session = Depends(get_db)) -> Response:
    result = _load_result_or_404(db, analysis_id)
    markdown = build_markdown_report(result)
    filename = "report.md"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(markdown, media_type="text/markdown; charset=utf-8", headers=headers)


def _load_result_or_404(db: Session, analysis_id: str):
    try:
        result = get_analysis_result(db, analysis_id)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Анализ не найден.")
    return result
