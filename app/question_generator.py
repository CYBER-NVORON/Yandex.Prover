from __future__ import annotations

from app.schemas import AudienceQuestion, Claim, StressTest, Weakness


def build_audience_questions(
    *,
    claims: list[Claim],
    weaknesses: list[Weakness],
    audience_type: str,
    material_type: str,
) -> list[AudienceQuestion]:
    asked_by = audience_type or "аудитория"
    is_teacher = "учитель" in audience_type.lower()
    questions: list[AudienceQuestion] = []

    high_claims = [claim for claim in claims if claim.risk_level == "high"]
    medium_claims = [claim for claim in claims if claim.risk_level == "medium"]
    first_claim = (high_claims or medium_claims or claims or [None])[0]

    if first_claim:
        questions.append(
            AudienceQuestion(
                id="question_1",
                question=f"На чём основано утверждение: «{first_claim.text}»?",
                asked_by=asked_by,
                category="Доказательность",
                why_asked=first_claim.explanation,
                risk_level=first_claim.risk_level,
                suggested_answer="Сейчас корректнее признать, что внутри материала это утверждение требует подтверждения, и указать, какое доказательство будет добавлено.",
                how_to_improve_material=first_claim.recommendation,
            )
        )

    questions.extend(
        [
            AudienceQuestion(
                id="question_2",
                question="Какую именно главную мысль вы защищаете одним предложением?",
                asked_by=asked_by,
                category="Главная мысль",
                why_asked="Если тезис не сформулирован коротко, аудитории трудно оценить доказательства.",
                risk_level="medium",
                suggested_answer="Сформулировать тезис как проверяемое утверждение, а не как тему: что именно доказано или предлагается.",
                how_to_improve_material="Добавить в начало материала короткий тезис и повторить его в выводе.",
            ),
            AudienceQuestion(
                id="question_3",
                question="Какие ограничения есть у вашей идеи или вывода?",
                asked_by=asked_by,
                category="Ограничения",
                why_asked="Сильная защита показывает не только преимущества, но и границы применимости.",
                risk_level="medium",
                suggested_answer="Назвать 1-2 ограничения и объяснить, почему они не отменяют главный вывод.",
                how_to_improve_material="Добавить блок с ограничениями перед финальным выводом.",
            ),
            AudienceQuestion(
                id="question_4",
                question="Что изменится для аудитории, если принять вашу идею?",
                asked_by=asked_by,
                category="Ценность",
                why_asked="Материал должен связывать аргументы с понятной пользой или научной значимостью.",
                risk_level="low",
                suggested_answer=(
                    "Показать учебный или исследовательский эффект: какой вывод подтверждает работа и чем полезна практическая часть."
                    if is_teacher
                    else "Показать практический, учебный, научный или деловой эффект идеи."
                ),
                how_to_improve_material=(
                    "Добавить короткий абзац о связи цели, практической части, источников и вывода."
                    if is_teacher
                    else "Добавить короткий абзац о пользе для выбранной аудитории."
                ),
            ),
            AudienceQuestion(
                id="question_5",
                question="Почему выбранный подход лучше альтернатив?",
                asked_by=asked_by,
                category="Сравнение",
                why_asked="Без сравнения аудитория может считать, что автор не проверил другие варианты.",
                risk_level="medium",
                suggested_answer="Назвать альтернативы и сравнить их по критериям, которые важны для темы.",
                how_to_improve_material="Добавить таблицу или абзац сравнения с 2-3 альтернативами.",
            ),
        ]
    )

    if "питч" in material_type.lower():
        questions.append(
            AudienceQuestion(
                id="question_6",
                question="Какими метриками вы докажете, что проблема действительно массовая и решение востребовано?",
                asked_by=asked_by,
                category="Метрики",
                why_asked="Для питча критично показать масштаб проблемы и проверяемую ценность решения.",
                risk_level="high",
                suggested_answer="Пока стоит честно сказать, какие метрики будут измерены: частота проблемы, конверсия, экономия времени или денег.",
                how_to_improve_material="Добавить минимум одну метрику спроса и одну метрику результата.",
            )
        )

    for index, weakness in enumerate(weaknesses[:2], start=7):
        questions.append(
            AudienceQuestion(
                id=f"question_{index}",
                question=f"Как вы закрываете слабое место: {weakness.problem.lower()}",
                asked_by=asked_by,
                category="Слабое место",
                why_asked=weakness.why_problem,
                risk_level="medium",
                suggested_answer=weakness.fix,
                how_to_improve_material=weakness.fix,
            )
        )

    return questions[:7]


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
