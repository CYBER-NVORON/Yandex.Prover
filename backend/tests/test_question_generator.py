from app.schemas import Claim, Weakness
from app.services.question_generator import build_audience_questions


def test_build_audience_questions_contains_whole_work_and_problem_questions():
    claim = Claim(
        id="claim_1",
        text="Большинство пользователей улучшат защиту после сервиса.",
        claim_type="generalization",
        location="примерно строка 4",
        needs_evidence=True,
        evidence_status="needs_source",
        risk_level="high",
        explanation="Широкое обобщение требует подтверждения.",
        recommendation="Добавить данные опроса или пример из материала.",
        suggested_rewrite="Часть пользователей может улучшить защиту после сервиса.",
    )
    weakness = Weakness(
        problem="Недостаточно доказательств",
        why_problem="Главный вывод не подкреплён данными.",
        audience_signal="Аудитория спросит, на чём основан вывод.",
        fix="Добавить один подтверждающий пример.",
    )

    questions = build_audience_questions(
        claims=[claim],
        weaknesses=[weakness],
        audience_type="учитель",
        material_type="реферат",
    )

    categories = {question.category for question in questions}
    assert any(category.startswith("Вся работа") for category in categories)
    assert any(category.startswith("Проблемное место") for category in categories)
    assert any("главный вывод всей работы" in question.question for question in questions)
    assert any(claim.text in question.question for question in questions)
