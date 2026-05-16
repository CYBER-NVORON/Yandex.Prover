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
RegulationRequirementStatus = Literal["met", "missing", "partially_met", "unverifiable"]
BenchmarkGapLevel = Literal["low", "medium", "high"]
ReadinessVerdict = Literal["ready", "almost_ready", "needs_work"]
ConfidenceLevel = Literal["low", "medium", "high"]


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


class EventRegulation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("regulation"))
    filename: str
    raw_text: str
    extracted_summary: str
    event_name: str | None = None
    work_format: str | None = None
    evaluation_criteria: list[str] = Field(default_factory=list)
    required_sections: list[str] = Field(default_factory=list)
    forbidden_items: list[str] = Field(default_factory=list)
    formatting_requirements: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    audience_expectations: list[str] = Field(default_factory=list)
    unknown_requirements: list[str] = Field(default_factory=list)


class RegulationCheckItem(BaseModel):
    requirement: str
    status: RegulationRequirementStatus
    evidence_from_material: str
    risk_level: RiskLevel
    recommendation: str


class RegulationAnalysis(BaseModel):
    summary: str
    matched_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    high_risk_requirements: list[str] = Field(default_factory=list)
    checklist: list[RegulationCheckItem] = Field(default_factory=list)
    event_regulation: EventRegulation | None = None


class BenchmarkWork(BaseModel):
    id: str = Field(default_factory=lambda: new_id("benchmark"))
    filename: str
    raw_text: str
    summary: str
    structure_analysis: str
    strengths: list[str] = Field(default_factory=list)
    reusable_patterns: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ComparisonItem(BaseModel):
    aspect: str
    user_material_observation: str
    benchmark_observation: str
    gap_level: BenchmarkGapLevel
    recommendation: str


class BenchmarkComparison(BaseModel):
    summary: str
    what_user_material_does_better: list[str] = Field(default_factory=list)
    what_benchmark_does_better: list[str] = Field(default_factory=list)
    missing_elements: list[str] = Field(default_factory=list)
    structure_gap: ComparisonItem
    evidence_gap: ComparisonItem
    clarity_gap: ComparisonItem
    action_items: list[str] = Field(default_factory=list)
    do_not_copy_warning: str
    comparison_items: list[ComparisonItem] = Field(default_factory=list)
    benchmark_work: BenchmarkWork | None = None


class OverthinkingGuard(BaseModel):
    readiness_verdict: ReadinessVerdict
    confidence_level: ConfidenceLevel
    critical_fixes: list[str] = Field(default_factory=list)
    optional_improvements: list[str] = Field(default_factory=list)
    safe_to_ignore: list[str] = Field(default_factory=list)
    stop_doing_list: list[str] = Field(default_factory=list)
    next_best_three_actions: list[str] = Field(default_factory=list, max_length=3)
    timeboxed_plan: dict[str, list[str]] = Field(default_factory=dict)
    reassuring_summary: str
    when_to_stop: str


def default_overthinking_guard() -> OverthinkingGuard:
    return OverthinkingGuard(
        readiness_verdict="almost_ready",
        confidence_level="medium",
        critical_fixes=[],
        optional_improvements=[],
        safe_to_ignore=[],
        stop_doing_list=[],
        next_best_three_actions=[
            "Проверить самый рискованный тезис.",
            "Подготовить ответ на самый опасный вопрос.",
            "Уточнить вывод, чтобы он не был шире доказательств.",
        ],
        timeboxed_plan={
            "15 минут": ["Выберите один самый рискованный тезис и подпишите, чем он подтверждается."],
            "30 минут": ["Подготовьте короткий ответ на самый опасный вопрос аудитории."],
            "60 минут": ["Проверьте связку цель -> доказательства -> вывод."],
            "если есть вечер": ["Сделайте финальный проход только по критичным рискам."],
        },
        reassuring_summary="Материал не обязан быть идеальным; достаточно закрыть ключевые риски перед защитой.",
        when_to_stop="Остановитесь после закрытия ключевых рисков и подготовки ответа на главный вопрос.",
    )


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: new_id("analysis"))
    filename: str
    material_type: str
    audience_type: str
    audience_knowledge_level: int = Field(default=3, ge=1, le=5)
    audience_knowledge_label: str = "средний уровень"
    audience_adaptation_notes: list[str] = Field(default_factory=list)
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
    regulation_analysis: RegulationAnalysis | None = None
    benchmark_comparison: BenchmarkComparison | None = None
    overthinking_guard: OverthinkingGuard = Field(default_factory=default_overthinking_guard)

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


class AnalyzeRequest(BaseModel):
    material_type: str
    audience_type: str
    audience_knowledge_level: int = Field(default=3, ge=1, le=5)
    title: str | None = None


class AnalysisCreateResponse(BaseModel):
    analysis_id: str
    status: str
    result: AnalysisResult


class AnalysisSummary(BaseModel):
    id: str
    filename: str
    material_type: str
    audience_type: str
    audience_knowledge_level: int = 3
    has_regulation: bool = False
    has_benchmark: bool = False
    readiness_verdict: ReadinessVerdict | None = None
    persuasiveness_score: int
    provider_name: str | None = None
    is_mock: bool
    created_at: datetime


class ReportResponse(BaseModel):
    analysis_id: str
    markdown: str
