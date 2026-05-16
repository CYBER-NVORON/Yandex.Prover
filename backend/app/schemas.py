from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


ClaimType = Literal[
    "fact",
    "number",
    "comparison",
    "causality",
    "generalization",
    "opinion",
    "definition",
    "unsupported_conclusion",
]

EvidenceStatus = Literal[
    "supported_by_text",
    "needs_source",
    "weak_argument",
    "too_strong",
    "unverifiable_from_text",
    "ok",
]

RiskLevel = Literal["low", "medium", "high"]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


class LLMResponse(BaseModel):
    text: str
    provider: str
    model: str
    response_id: str | None = None
    is_mock: bool


class StructureAnalysis(BaseModel):
    main_idea: str
    goal: str
    target_audience: str
    structure_summary: str
    logic_quality_score: int = Field(ge=0, le=100)
    clarity_score: int = Field(ge=0, le=100)
    problems: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    id: str = Field(default_factory=lambda: new_id("claim"))
    text: str
    claim_type: ClaimType
    location: str
    needs_evidence: bool
    evidence_status: EvidenceStatus
    risk_level: RiskLevel
    explanation: str
    recommendation: str
    suggested_rewrite: str


class AudienceQuestion(BaseModel):
    id: str = Field(default_factory=lambda: new_id("question"))
    question: str
    asked_by: str
    category: str
    why_asked: str
    risk_level: RiskLevel
    suggested_answer: str
    how_to_improve_material: str


class Recommendation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("rec"))
    priority: RiskLevel
    category: str
    problem: str
    action: str
    expected_effect: str


class ImprovementPlan(BaseModel):
    quick_fixes_30_min: list[str] = Field(default_factory=list)
    improvements_2_hours: list[str] = Field(default_factory=list)
    final_polish: list[str] = Field(default_factory=list)


class Weakness(BaseModel):
    problem: str
    why_problem: str
    audience_signal: str
    fix: str


class ScoringBreakdown(BaseModel):
    clarity_score: int = Field(ge=0, le=100)
    structure_score: int = Field(ge=0, le=100)
    argument_score: int = Field(ge=0, le=100)
    evidence_score: int = Field(ge=0, le=100)
    audience_score: int = Field(ge=0, le=100)
    question_readiness_score: int = Field(ge=0, le=100)
    explanation: str


class StressTest(BaseModel):
    most_dangerous_question: str
    why_dangerous: str
    exposed_weakness: str
    suggested_answer: str
    what_to_add: str


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("analysis"))
    filename: str
    material_type: str
    audience_type: str
    provider_name: str = "unknown"
    provider_model: str = "unknown"
    provider_response_id: str | None = None
    is_mock: bool = False
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    persuasiveness_score: int = Field(ge=0, le=100)
    scoring_breakdown: ScoringBreakdown
    summary: str
    main_idea: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[Weakness] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    structure_analysis: StructureAnalysis
    claims: list[Claim] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    audience_questions: list[AudienceQuestion] = Field(default_factory=list)
    improvement_plan: ImprovementPlan
    stress_test: StressTest

    @field_validator("title", "summary", "main_idea")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty")
        return value


class HealthResponse(BaseModel):
    status: str
    service: str


class AnalysisCreateResponse(BaseModel):
    analysis_id: str
    status: str
    result: AnalysisResult


class AnalysisSummary(BaseModel):
    id: str
    filename: str
    material_type: str
    audience_type: str
    persuasiveness_score: int
    provider_name: str | None = None
    is_mock: bool
    created_at: datetime


class ReportResponse(BaseModel):
    analysis_id: str
    markdown: str
