from app.services.scoring import calculate_persuasiveness_score


def test_calculate_persuasiveness_score_weighted_average():
    score = calculate_persuasiveness_score(
        clarity_score=80,
        structure_score=60,
        argument_score=70,
        evidence_score=50,
        audience_score=90,
        question_readiness_score=40,
    )

    assert score == 64


def test_calculate_persuasiveness_score_clamps_values():
    score = calculate_persuasiveness_score(
        clarity_score=120,
        structure_score=100,
        argument_score=100,
        evidence_score=100,
        audience_score=100,
        question_readiness_score=100,
    )

    assert score == 100


