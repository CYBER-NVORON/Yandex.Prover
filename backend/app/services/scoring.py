from __future__ import annotations

from app.schemas import ScoringBreakdown


WEIGHTS = {
    "clarity_score": 0.20,
    "structure_score": 0.15,
    "argument_score": 0.20,
    "evidence_score": 0.20,
    "audience_score": 0.10,
    "question_readiness_score": 0.15,
}


def clamp_score(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def calculate_persuasiveness_score(
    *,
    clarity_score: int | float,
    structure_score: int | float,
    argument_score: int | float,
    evidence_score: int | float,
    audience_score: int | float,
    question_readiness_score: int | float,
) -> int:
    weighted = (
        clamp_score(clarity_score) * WEIGHTS["clarity_score"]
        + clamp_score(structure_score) * WEIGHTS["structure_score"]
        + clamp_score(argument_score) * WEIGHTS["argument_score"]
        + clamp_score(evidence_score) * WEIGHTS["evidence_score"]
        + clamp_score(audience_score) * WEIGHTS["audience_score"]
        + clamp_score(question_readiness_score)
        * WEIGHTS["question_readiness_score"]
    )
    return clamp_score(weighted)


def score_from_breakdown(breakdown: ScoringBreakdown) -> int:
    return calculate_persuasiveness_score(
        clarity_score=breakdown.clarity_score,
        structure_score=breakdown.structure_score,
        argument_score=breakdown.argument_score,
        evidence_score=breakdown.evidence_score,
        audience_score=breakdown.audience_score,
        question_readiness_score=breakdown.question_readiness_score,
    )


