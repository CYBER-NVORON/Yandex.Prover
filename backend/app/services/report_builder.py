from __future__ import annotations

from app.schemas import AnalysisResult


RISK_LABELS = {
    "low": "низкий",
    "medium": "средний",
    "high": "высокий",
}

EVIDENCE_LABELS = {
    "supported_by_text": "подтверждено текстом",
    "needs_source": "нужен источник",
    "weak_argument": "слабый аргумент",
    "too_strong": "слишком широкий вывод",
    "unverifiable_from_text": "не проверить по тексту",
    "ok": "достаточно",
}

CLAIM_TYPE_LABELS = {
    "fact": "факт",
    "number": "число",
    "comparison": "сравнение",
    "causality": "причинно-следственная связь",
    "generalization": "обобщение",
    "opinion": "мнение",
    "definition": "определение",
    "unsupported_conclusion": "вывод без опоры",
}

REGULATION_STATUS_LABELS = {
    "met": "выполнено",
    "missing": "не найдено",
    "partially_met": "частично выполнено",
    "unverifiable": "нельзя проверить",
}

GAP_LABELS = {
    "low": "небольшое отличие",
    "medium": "заметное отличие",
    "high": "сильное отличие",
}

READINESS_LABELS = {
    "ready": "готово",
    "almost_ready": "почти готово",
    "needs_work": "нужно доработать",
}

CONFIDENCE_LABELS = {
    "low": "низкая",
    "medium": "средняя",
    "high": "высокая",
}


def _label(labels: dict[str, str], value: str) -> str:
    return labels.get(value, value)


def _bullets(items: list[str]) -> str:
    if not items:
        return "- Нет данных."
    return "\n".join(f"- {item}" for item in items)


def _regulation_section(result: AnalysisResult) -> str:
    if result.regulation_analysis is None:
        return ""
    analysis = result.regulation_analysis
    checklist = [
        f"- **{_label(REGULATION_STATUS_LABELS, item.status)} / риск {_label(RISK_LABELS, item.risk_level)}:** {item.requirement} "
        f"Данные: {item.evidence_from_material} Рекомендация: {item.recommendation}"
        for item in analysis.checklist
    ]
    return f"""
## 13. Соответствие регламенту
{analysis.summary}

### Выполнено
{_bullets(analysis.matched_requirements)}

### Не выполнено или частично выполнено
{_bullets(analysis.missing_requirements)}

### Высокий риск
{_bullets(analysis.high_risk_requirements)}

### Чек-лист
{chr(10).join(checklist) if checklist else "- Нет данных."}
"""


def _benchmark_section(result: AnalysisResult) -> str:
    if result.benchmark_comparison is None:
        return ""
    comparison = result.benchmark_comparison
    gaps = [
        f"- **{item.aspect} ({_label(GAP_LABELS, item.gap_level)}):** пользователь — {item.user_material_observation} "
        f"эталон — {item.benchmark_observation} Рекомендация: {item.recommendation}"
        for item in comparison.comparison_items
    ]
    return f"""
## 14. Сравнение с эталоном
{comparison.summary}

**Важно:** {comparison.do_not_copy_warning}

### Что у пользователя уже хорошо
{_bullets(comparison.what_user_material_does_better)}

### Что эталон делает сильнее
{_bullets(comparison.what_benchmark_does_better)}

### Недостающие элементы
{_bullets(comparison.missing_elements)}

### Различия
{chr(10).join(gaps) if gaps else "- Нет данных."}

### Что сделать
{_bullets(comparison.action_items)}
"""


def _overthinking_section(result: AnalysisResult) -> str:
    guard = result.overthinking_guard
    return f"""
## 15. Уровень знаний аудитории
**{result.audience_knowledge_level}/5 — {result.audience_knowledge_label}**

{_bullets(result.audience_adaptation_notes)}

## 16. Готово к защите?
Вердикт: **{_label(READINESS_LABELS, guard.readiness_verdict)}**

Уверенность: **{_label(CONFIDENCE_LABELS, guard.confidence_level)}**

### 3 главных действия
{_bullets(guard.next_best_three_actions)}

### Критично
{_bullets(guard.critical_fixes)}

### Можно не трогать
{_bullets(guard.safe_to_ignore)}

### Когда остановиться
{guard.when_to_stop}

### Спокойное резюме
{guard.reassuring_summary}
"""


def build_markdown_report(result: AnalysisResult) -> str:
    claims_rows = [
        "| Утверждение | Тип | Статус | Риск | Рекомендация |",
        "| --- | --- | --- | --- | --- |",
    ]
    for claim in result.claims:
        claims_rows.append(
            f"| {claim.text} | {_label(CLAIM_TYPE_LABELS, claim.claim_type)} | {_label(EVIDENCE_LABELS, claim.evidence_status)} | {_label(RISK_LABELS, claim.risk_level)} | {claim.recommendation} |"
        )

    questions = []
    answers = []
    for question in result.audience_questions:
        questions.append(f"- **{question.question}** ({question.asked_by}, риск: {_label(RISK_LABELS, question.risk_level)})")
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

## 3. Контекст анализа
Тип материала: {result.material_type}

Аудитория: {result.audience_type}

ИИ-анализ выполнен только по загруженному материалу, без внешнего поиска.

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
{_regulation_section(result)}
{_benchmark_section(result)}
{_overthinking_section(result)}
"""

