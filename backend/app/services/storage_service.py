from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import delete, desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import AnalysisRun
from app.schemas import AnalysisResult


class StorageError(Exception):
    pass


def save_analysis_result(db: Session, result: AnalysisResult) -> AnalysisRun:
    result.id = _ensure_uuid_string(result.id)
    payload = result.model_dump(mode="json")
    run = AnalysisRun(
        id=result.id,
        filename=result.filename,
        material_type=result.material_type,
        audience_type=result.audience_type,
        title=result.title,
        provider_name=result.provider_name,
        provider_model=result.provider_model,
        provider_response_id=result.provider_response_id,
        is_mock=result.is_mock,
        has_regulation=result.regulation_analysis is not None,
        has_benchmark=result.benchmark_comparison is not None,
        audience_knowledge_level=result.audience_knowledge_level,
        readiness_verdict=result.overthinking_guard.readiness_verdict if result.overthinking_guard else None,
        persuasiveness_score=result.persuasiveness_score,
        result_json=payload,
    )
    try:
        merged = db.merge(run)
        db.commit()
        db.refresh(merged)
        return merged
    except SQLAlchemyError as exc:
        db.rollback()
        raise StorageError("Не удалось сохранить результат анализа.") from exc


def list_analysis_runs(db: Session, *, limit: int = 20) -> list[AnalysisRun]:
    try:
        statement = select(AnalysisRun).order_by(desc(AnalysisRun.created_at)).limit(limit)
        return list(db.scalars(statement).all())
    except SQLAlchemyError as exc:
        raise StorageError("Не удалось прочитать список анализов.") from exc


def get_analysis_result(db: Session, analysis_id: str) -> AnalysisResult | None:
    try:
        run = db.get(AnalysisRun, analysis_id)
    except SQLAlchemyError as exc:
        raise StorageError("Не удалось загрузить результат анализа.") from exc
    if run is None:
        return None
    return AnalysisResult.model_validate(run.result_json)


def delete_analysis_result(db: Session, analysis_id: str) -> bool:
    try:
        result = db.execute(delete(AnalysisRun).where(AnalysisRun.id == analysis_id))
        db.commit()
        return bool(result.rowcount)
    except SQLAlchemyError as exc:
        db.rollback()
        raise StorageError("Не удалось удалить результат анализа.") from exc


def _ensure_uuid_string(value: str) -> str:
    try:
        return str(UUID(value))
    except ValueError:
        return str(uuid4())
