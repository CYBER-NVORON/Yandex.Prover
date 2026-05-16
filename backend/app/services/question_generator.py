from __future__ import annotations

from itertools import count

from app.schemas import AudienceQuestion, Claim, StressTest, Weakness


def build_audience_questions(
    *,
    claims: list[Claim],
    weaknesses: list[Weakness],
    audience_type: str,
    material_type: str,
) -> list[AudienceQuestion]:
    """Build audience questions for the full material and its weak spots.

    Yandex mode asks the model to generate questions from the whole submitted
    context. Mock mode is deterministic, so it synthesizes questions from the
    analysis artifacts we already have: material type, audience type, risky
    claims and weaknesses. This keeps the demo local without pretending to
    verify external facts.
    """

    asked_by = audience_type or "аудитория"
    is_teacher = "учитель" in audience_type.lower()
    is_pitch = "питч" in material_type.lower() or "презентац" in material_type.lower()
    is_academic = _is_academic_material(material_type)
    question_ids = count(1)
    questions: list[AudienceQuestion] = []

    questions.extend(
        _whole_work_questions(
            question_ids=question_ids,
            asked_by=asked_by,
            is_teacher=is_teacher,
            is_pitch=is_pitch,
            is_academic=is_academic,
        )
    )
    questions.extend(
        _claim_questions(
            question_ids=question_ids,
            claims=claims,
            asked_by=asked_by,
        )
    )
    questions.extend(
        _weakness_questions(
            question_ids=question_ids,
            weaknesses=weaknesses,
            asked_by=asked_by,
        )
    )

    return _dedupe_questions(questions)[:10]


def _whole_work_questions(
    *,
    question_ids,
    asked_by: str,
    is_teacher: bool,
    is_pitch: bool,
    is_academic: bool,
) -> list[AudienceQuestion]:
    questions = [
        AudienceQuestion(
            id=f"question_{next(question_ids)}",
            question="Как одним предложением сформулировать главный вывод всей работы?",
            asked_by=asked_by,
            category="Вся работа: главная мысль",
            why_asked="Аудитория сначала проверяет, есть ли у материала единый защищаемый тезис, а не только тема.",
            risk_level="medium",
            suggested_answer="Сформулировать не тему, а проверяемый вывод: что именно доказано, показано или предлагается.",
            how_to_improve_material="Добавить короткий тезис во введение и повторить его в заключении теми же словами.",
        ),
        AudienceQuestion(
            id=f"question_{next(question_ids)}",
            question="Какие доказательства внутри материала сильнее всего подтверждают главный вывод?",
            asked_by=asked_by,
            category="Вся работа: доказательства",
            why_asked="Даже сильная идея выглядит уязвимой, если автор не может быстро назвать опорные доказательства.",
            risk_level="medium",
            suggested_answer="Назвать 2-3 опорных фрагмента работы: пример, наблюдение, расчёт, результат опроса или аргумент.",
            how_to_improve_material="В конце каждого крупного раздела добавить связку: какой вывод этот раздел подтверждает.",
        ),
        AudienceQuestion(
            id=f"question_{next(question_ids)}",
            question="Какие ограничения есть у вашей идеи или вывода?",
            asked_by=asked_by,
            category="Вся работа: ограничения",
            why_asked="Сильная защита показывает не только преимущества, но и границы применимости.",
            risk_level="medium",
            suggested_answer="Назвать 1-2 ограничения и объяснить, почему они не отменяют главный вывод.",
            how_to_improve_material="Добавить блок с ограничениями перед финальным выводом.",
        ),
    ]

    if is_academic or is_teacher:
        questions.extend(
            [
                AudienceQuestion(
                    id=f"question_{next(question_ids)}",
                    question="Как связаны тема, цель, задачи, методы и вывод?",
                    asked_by=asked_by,
                    category="Вся работа: структура",
                    why_asked="Для учебной или исследовательской работы важно, чтобы структура не распадалась на отдельные части.",
                    risk_level="medium",
                    suggested_answer="Показать цепочку: цель задаёт задачи, методы помогают решить задачи, вывод отвечает на цель.",
                    how_to_improve_material="Добавить в заключение короткий абзац, который возвращает читателя к цели и задачам.",
                ),
                AudienceQuestion(
                    id=f"question_{next(question_ids)}",
                    question="Что в работе является вашим собственным выводом, а что пересказом источников?",
                    asked_by=asked_by,
                    category="Вся работа: самостоятельность",
                    why_asked="Учитель или преподаватель обычно проверяет, есть ли у автора самостоятельная позиция.",
                    risk_level="medium",
                    suggested_answer="Отделить факты и источники от собственного сравнения, наблюдения или итогового вывода.",
                    how_to_improve_material="Явно подписать собственные выводы: 'поэтому можно сделать вывод', 'сравнение показывает'.",
                ),
            ]
        )

    if is_pitch:
        questions.extend(
            [
                AudienceQuestion(
                    id=f"question_{next(question_ids)}",
                    question="Для кого именно решается проблема и чем подтверждено, что она важна?",
                    asked_by=asked_by,
                    category="Вся работа: аудитория",
                    why_asked="В питче аудитория проверяет не только идею, но и точность выбранного пользователя.",
                    risk_level="high",
                    suggested_answer="Назвать сегмент пользователей и доказательство из материала: интервью, наблюдение, метрику или пример.",
                    how_to_improve_material="Добавить блок с описанием пользователя и одним подтверждением боли.",
                ),
                AudienceQuestion(
                    id=f"question_{next(question_ids)}",
                    question="Какими метриками вы покажете, что решение действительно работает?",
                    asked_by=asked_by,
                    category="Вся работа: метрики",
                    why_asked="Без метрик ценность решения остаётся обещанием, а не проверяемым результатом.",
                    risk_level="high",
                    suggested_answer="Назвать 1-2 метрики результата: время, точность, конверсия, экономия, удовлетворённость или повторное использование.",
                    how_to_improve_material="Добавить минимум одну метрику спроса и одну метрику результата.",
                ),
            ]
        )

    return questions


def _claim_questions(*, question_ids, claims: list[Claim], asked_by: str) -> list[AudienceQuestion]:
    risky_claims = sorted(claims, key=lambda claim: _risk_rank(claim.risk_level), reverse=True)[:3]
    questions: list[AudienceQuestion] = []

    for claim in risky_claims:
        questions.append(
            AudienceQuestion(
                id=f"question_{next(question_ids)}",
                question=f"На чём основано утверждение: «{claim.text}»?",
                asked_by=asked_by,
                category="Проблемное место: доказательность",
                why_asked=claim.explanation,
                risk_level=claim.risk_level,
                suggested_answer="Честно указать, чем это подтверждается внутри материала, или признать, какое доказательство нужно добавить.",
                how_to_improve_material=claim.recommendation,
            )
        )

    return questions


def _weakness_questions(*, question_ids, weaknesses: list[Weakness], asked_by: str) -> list[AudienceQuestion]:
    questions: list[AudienceQuestion] = []

    for weakness in weaknesses[:3]:
        questions.append(
            AudienceQuestion(
                id=f"question_{next(question_ids)}",
                question=f"Как вы закрываете слабое место: {weakness.problem.lower()}?",
                asked_by=asked_by,
                category="Проблемное место: слабость работы",
                why_asked=weakness.why_problem,
                risk_level="medium",
                suggested_answer=weakness.fix,
                how_to_improve_material=weakness.fix,
            )
        )

    return questions


def _dedupe_questions(questions: list[AudienceQuestion]) -> list[AudienceQuestion]:
    seen: set[str] = set()
    result: list[AudienceQuestion] = []
    for question in questions:
        key = question.question.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        result.append(question)
    return result


def _risk_rank(risk_level: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(risk_level, 0)


def _is_academic_material(material_type: str) -> bool:
    lowered = material_type.lower()
    return any(
        marker in lowered
        for marker in ("реферат", "сочинение", "исследовательская", "доклад", "курсовая", "диплом", "диссертация", "статья")
    )


def build_stress_test(questions: list[AudienceQuestion], weaknesses: list[Weakness]) -> StressTest:
    dangerous = next((question for question in questions if question.risk_level == "high"), questions[0])
    weakness = weaknesses[0] if weaknesses else None
    return StressTest(
        most_dangerous_question=dangerous.question,
        why_dangerous=dangerous.why_asked,
        exposed_weakness=weakness.problem if weakness else "Ключевое утверждение недостаточно подтверждено внутри материала.",
        suggested_answer=dangerous.suggested_answer,
        what_to_add=dangerous.how_to_improve_material,
    )
