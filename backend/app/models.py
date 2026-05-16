from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, Text, Uuid, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        Index("ix_analysis_runs_created_at_desc", "created_at"),
        Index("ix_analysis_runs_persuasiveness_score", "persuasiveness_score"),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    material_type: Mapped[str] = mapped_column(Text, nullable=False)
    audience_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_response_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_regulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    has_benchmark: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    audience_knowledge_level: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    readiness_verdict: Mapped[str | None] = mapped_column(Text, nullable=True)
    persuasiveness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
