from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalysisCreateResponse, AnalysisResult, AnalysisSummary
from app.services.analysis_pipeline import analyze_text
from app.services.document_loader import DocumentLoadError, LoadedDocument, load_document_from_bytes
from app.services.llm.base import InvalidLLMResponseError, LLMProviderError
from app.services.storage_service import (
    StorageError,
    delete_analysis_result,
    get_analysis_result,
    list_analysis_runs,
    save_analysis_result,
)

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisCreateResponse)
async def create_analysis(
    file: UploadFile = File(...),
    regulation_file: UploadFile | None = File(None),
    benchmark_file: UploadFile | None = File(None),
    material_type: str = Form(...),
    audience_type: str = Form(...),
    audience_knowledge_level: int = Form(3),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
) -> AnalysisCreateResponse:
    content = await file.read()
    try:
        loaded = load_document_from_bytes(file.filename or "material.txt", content)
        regulation = await _load_optional_upload(regulation_file)
        benchmark = await _load_optional_upload(benchmark_file)
        result = analyze_text(
            text=loaded.text,
            filename=loaded.filename,
            material_type=material_type,
            audience_type=audience_type,
            audience_knowledge_level=audience_knowledge_level,
            regulation_text=regulation.text if regulation else None,
            regulation_filename=regulation.filename if regulation else None,
            benchmark_text=benchmark.text if benchmark else None,
            benchmark_filename=benchmark.filename if benchmark else None,
        )
        result.id = str(uuid4())
        if title and title.strip():
            result.title = title.strip()
        save_analysis_result(db, result)
    except DocumentLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidLLMResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LLMProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AnalysisCreateResponse(analysis_id=result.id, status="completed", result=result)


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(db: Session = Depends(get_db)) -> list[AnalysisSummary]:
    try:
        runs = list_analysis_runs(db)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [
        AnalysisSummary(
            id=run.id,
            filename=run.filename,
            material_type=run.material_type,
            audience_type=run.audience_type,
            audience_knowledge_level=run.audience_knowledge_level,
            has_regulation=run.has_regulation,
            has_benchmark=run.has_benchmark,
            readiness_verdict=run.readiness_verdict,
            persuasiveness_score=run.persuasiveness_score,
            provider_name=run.provider_name,
            is_mock=run.is_mock,
            created_at=run.created_at,
        )
        for run in runs
    ]


async def _load_optional_upload(upload: UploadFile | None) -> LoadedDocument | None:
    if upload is None or not upload.filename:
        return None
    content = await upload.read()
    return load_document_from_bytes(upload.filename, content)


@router.get("/{analysis_id}", response_model=AnalysisResult)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisResult:
    try:
        result = get_analysis_result(db, analysis_id)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Анализ не найден.")
    return result


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)) -> None:
    try:
        deleted = delete_analysis_result(db, analysis_id)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Анализ не найден.")
