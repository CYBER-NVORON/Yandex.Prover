from __future__ import annotations

from app.schemas import AnalysisResult


def _bullets(items: list[str]) -> str:
    if not items:
        return "- Нет данных."
    return "\n".join(f"- {item}" for item in items)


def build_markdown_report(result: AnalysisResult) -> str:
    claims_rows = [
        "| Утверждение | Тип | Статус | Риск | Рекомендация |",
        "| --- | --- | --- | --- | --- |",
    ]
    for claim in result.claims:
        claims_rows.append(
            f"| {claim.text} | {claim.claim_type} | {claim.evidence_status} | {claim.risk_level} | {claim.recommendation} |"
        )

    questions = []
    answers = []
    for question in result.audience_questions:
        questions.append(f"- **{question.question}** ({question.asked_by}, риск: {question.risk_level})")
        answers.append(f"- **{question.question}**\n  Ответ: {question.suggested_answer}")

    weaknesses = [
        f"- **{weakness.problem}** {weakness.why_problem} Исправление: {weakness.fix}"
        for weakness in result.weaknesses
    ]

    return f"""# {result.title}

## 1. Название анализа
{result.title}

## 2. Индекс убедительности
**{result.persuasiveness_score}/100**

## 3. LLM provider
Provider: {result.provider_name}

Model: {result.provider_model}

Response ID: {result.provider_response_id or "-"}

Mock mode: {"yes" if result.is_mock else "no"}

## 4. Краткое резюме
{result.summary}

## 5. Главная мысль
{result.main_idea}

## 6. Сильные стороны
{_bullets(result.strengths)}

## 7. Слабые стороны
{chr(10).join(weaknesses) if weaknesses else "- Нет данных."}

## 8. Карта доказательности
{chr(10).join(claims_rows)}

## 9. Вопросы аудитории
{chr(10).join(questions) if questions else "- Нет данных."}

## 10. Рекомендуемые ответы
{chr(10).join(answers) if answers else "- Нет данных."}

## 11. План улучшения
### За 30 минут
{_bullets(result.improvement_plan.quick_fixes_30_min)}

### За 2 часа
{_bullets(result.improvement_plan.improvements_2_hours)}

### Финальная полировка
{_bullets(result.improvement_plan.final_polish)}

## 12. Стресс-тест идеи
**Самый опасный вопрос:** {result.stress_test.most_dangerous_question}

**Почему он опасен:** {result.stress_test.why_dangerous}

**Слабое место:** {result.stress_test.exposed_weakness}

**Как ответить:** {result.stress_test.suggested_answer}

**Что добавить в материал:** {result.stress_test.what_to_add}
"""

