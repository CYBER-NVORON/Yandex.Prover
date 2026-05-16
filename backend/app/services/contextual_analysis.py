from __future__ import annotations

import re
from collections.abc import Iterable

from app.schemas import (
    BenchmarkComparison,
    BenchmarkWork,
    Claim,
    ComparisonItem,
    EventRegulation,
    OverthinkingGuard,
    RegulationAnalysis,
    RegulationCheckItem,
)


KNOWLEDGE_LABELS = {
    1: "почти не знакомы с темой",
    2: "базово знакомы с темой",
    3: "средний уровень",
    4: "хорошо разбираются в теме",
    5: "экспертная аудитория",
}

SECTION_MARKERS: dict[str, tuple[str, ...]] = {
    "цель": ("цель",),
    "задачи": ("задач",),
    "методы": ("метод", "методик"),
    "вывод": ("вывод", "заключени", "итог"),
    "гипотеза": ("гипотез",),
    "актуальность": ("актуальн",),
    "новизна": ("новизн",),
    "результаты": ("результат",),
    "практическая значимость": ("практическ", "значим"),
    "список литературы": ("литератур", "источник"),
}

HIGH_RISK_REQUIRED_SECTIONS = {"цель", "задачи", "методы", "вывод"}


def normalize_audience_knowledge_level(level: int | str | None) -> int:
    try:
        parsed = int(level if level is not None else 3)
    except (TypeError, ValueError):
        parsed = 3
    return max(1, min(5, parsed))


def audience_knowledge_label(level: int) -> str:
    return KNOWLEDGE_LABELS.get(normalize_audience_knowledge_level(level), KNOWLEDGE_LABELS[3])


def build_audience_adaptation_notes(level: int) -> list[str]:
    level = normalize_audience_knowledge_level(level)
    if level <= 2:
        return [
            "Для этой аудитории нужно явнее объяснять термины, контекст и метод.",
            "Вопросы аудитории будут проще, но риск непонятности выше при перегрузе специальной лексикой.",
            "Рекомендации сфокусированы на коротких объяснениях и понятных примерах.",
        ]
    if level == 3:
        return [
            "Анализ выполнен в стандартном режиме: баланс понятности, структуры и доказательности.",
            "Вопросы проверяют главную мысль, доказательства, ограничения и готовность к уточнениям.",
        ]
    return [
        "Для подготовленной аудитории важнее точность, методология, ограничения и альтернативные объяснения.",
        "Вопросы будут глубже и строже к источникам, методу и границам выводов.",
        "Рекомендации меньше фокусируются на простых объяснениях и больше на доказательности.",
    ]


def build_regulation_analysis(
    *,
    material_text: str,
    regulation_text: str,
    regulation_filename: str,
) -> RegulationAnalysis:
    normalized_regulation = _normalize_text(regulation_text)
    event_regulation = EventRegulation(
        filename=regulation_filename,
        raw_text=regulation_text.strip(),
        extracted_summary=_summarize_regulation(normalized_regulation),
        event_name=_extract_event_name(normalized_regulation),
        work_format=_extract_work_format(normalized_regulation),
        evaluation_criteria=_extract_lines(
            normalized_regulation,
            ("критер", "оцени", "балл", "жюри", "комисси", "эксперт"),
            limit=8,
        ),
        required_sections=_extract_required_sections(normalized_regulation),
        forbidden_items=_extract_lines(
            normalized_regulation,
            ("запрещ", "не допуска", "нельзя", "недопустим"),
            limit=6,
        ),
        formatting_requirements=_extract_lines(
            normalized_regulation,
            ("объем", "объём", "страниц", "минут", "шрифт", "формат", "слайд", "файл"),
            limit=8,
        ),
        deadlines=_extract_deadlines(normalized_regulation),
        audience_expectations=_extract_lines(
            normalized_regulation,
            ("жюри", "комисси", "учител", "эксперт", "аудитор", "оценива"),
            limit=6,
        ),
        unknown_requirements=[],
    )
    if not event_regulation.required_sections:
        event_regulation.unknown_requirements.append("Не удалось уверенно выделить обязательные разделы.")
    if not event_regulation.evaluation_criteria:
        event_regulation.unknown_requirements.append("Критерии оценки не выделены явно.")

    checklist = _build_regulation_checklist(material_text, event_regulation)
    matched = [item.requirement for item in checklist if item.status == "met"]
    missing = [item.requirement for item in checklist if item.status in {"missing", "partially_met"}]
    high_risk = [
        item.requirement
        for item in checklist
        if item.risk_level == "high" and item.status in {"missing", "partially_met", "unverifiable"}
    ]

    if missing:
        summary = (
            "Регламент приложен и учтён отдельно от утверждений основного материала. "
            f"Главные риски соответствия: {', '.join(missing[:3])}."
        )
    else:
        summary = (
            "Регламент приложен и учтён отдельно от утверждений основного материала. "
            "Критичных расхождений по выделенным требованиям не найдено."
        )

    return RegulationAnalysis(
        summary=summary,
        matched_requirements=matched,
        missing_requirements=missing,
        high_risk_requirements=high_risk,
        checklist=checklist,
        event_regulation=event_regulation,
    )


def build_benchmark_comparison(
    *,
    material_text: str,
    benchmark_text: str,
    benchmark_filename: str,
) -> BenchmarkComparison:
    user_features = _text_features(material_text)
    benchmark_features = _text_features(benchmark_text)
    benchmark_work = BenchmarkWork(
        filename=benchmark_filename,
        raw_text=benchmark_text.strip(),
        summary=_first_sentence(benchmark_text)
        or "Эталонная работа загружена как пример структуры и уровня доказательности.",
        structure_analysis=_structure_observation(benchmark_features),
        strengths=_benchmark_strengths(benchmark_features),
        reusable_patterns=_benchmark_patterns(user_features, benchmark_features),
        warnings=[
            "Эталон используется только для сравнения структуры и доказательности; текст копировать не нужно."
        ],
    )

    structure_gap = _build_structure_gap(user_features, benchmark_features)
    evidence_gap = _build_evidence_gap(user_features, benchmark_features)
    clarity_gap = _build_clarity_gap(user_features, benchmark_features)
    comparison_items = [
        structure_gap,
        evidence_gap,
        clarity_gap,
        _build_detail_gap(user_features, benchmark_features),
        _build_readiness_gap(user_features, benchmark_features),
    ]

    missing_elements = _missing_benchmark_elements(user_features, benchmark_features)
    what_user_does_better = _user_advantages(user_features, benchmark_features)
    what_benchmark_does_better = _benchmark_advantages(comparison_items, missing_elements)
    action_items = _benchmark_action_items(comparison_items, missing_elements)

    return BenchmarkComparison(
        summary=(
            "Сравнение выполнено по структуре, ясности, доказательности и готовности к вопросам. "
            "Эталон не используется как источник текста для копирования."
        ),
        what_user_material_does_better=what_user_does_better,
        what_benchmark_does_better=what_benchmark_does_better,
        missing_elements=missing_elements,
        structure_gap=structure_gap,
        evidence_gap=evidence_gap,
        clarity_gap=clarity_gap,
        action_items=action_items[:5],
        do_not_copy_warning=(
            "Сервис не предлагает копировать эталон. Он сравнивает структуру и силу аргументации."
        ),
        comparison_items=comparison_items,
        benchmark_work=benchmark_work,
    )


def build_overthinking_guard(
    result,
    regulation_analysis: RegulationAnalysis | None,
    benchmark_comparison: BenchmarkComparison | None,
    audience_knowledge_level: int,
) -> OverthinkingGuard:
    high_risk_claims = [claim for claim in result.claims if claim.risk_level == "high"]
    critical_regulation_items = _critical_regulation_items(regulation_analysis)
    critical_missing_regulation = bool(critical_regulation_items)
    score = result.persuasiveness_score

    if score >= 80 and len(high_risk_claims) <= 1 and not critical_missing_regulation:
        verdict = "ready"
    elif score < 60 or critical_missing_regulation or len(high_risk_claims) >= 4:
        verdict = "needs_work"
    else:
        verdict = "almost_ready"

    confidence = _confidence_level(result)
    critical_fixes = _first_unique(
        [
            *critical_regulation_items,
            *(_claim_fix_items(high_risk_claims)),
            _dangerous_question_fix(result),
            *(_structure_critical_fixes(result)),
        ],
        limit=4,
    )
    optional_improvements = _first_unique(
        [
            *[recommendation.action for recommendation in result.recommendations if recommendation.priority in {"medium", "low"}],
            *(benchmark_comparison.action_items if benchmark_comparison else []),
            *result.improvement_plan.final_polish,
        ],
        limit=4,
    )
    next_best_three_actions = _first_unique(
        [
            *critical_fixes,
            *[recommendation.action for recommendation in result.recommendations if recommendation.priority == "high"],
            *result.improvement_plan.quick_fixes_30_min,
            result.stress_test.what_to_add,
        ],
        limit=3,
    )
    while len(next_best_three_actions) < 3:
        fallback_actions = [
            "Сформулировать главный вывод одним предложением.",
            "Подготовить ответ на самый опасный вопрос.",
            "Проверить, что вывод не шире доказательств в тексте.",
        ]
        next_best_three_actions = _first_unique([*next_best_three_actions, *fallback_actions], limit=3)

    safe_to_ignore = _safe_to_ignore_items(audience_knowledge_level, regulation_analysis, benchmark_comparison)
    stop_doing_list = _stop_doing_items(audience_knowledge_level, regulation_analysis)
    timeboxed_plan = _timeboxed_plan(next_best_three_actions, critical_fixes, optional_improvements)

    return OverthinkingGuard(
        readiness_verdict=verdict,
        confidence_level=confidence,
        critical_fixes=critical_fixes,
        optional_improvements=optional_improvements,
        safe_to_ignore=safe_to_ignore,
        stop_doing_list=stop_doing_list,
        next_best_three_actions=next_best_three_actions,
        timeboxed_plan=timeboxed_plan,
        reassuring_summary=_reassuring_summary(verdict, critical_fixes),
        when_to_stop=_when_to_stop(next_best_three_actions),
    )


def _build_regulation_checklist(material_text: str, event_regulation: EventRegulation) -> list[RegulationCheckItem]:
    material_lower = material_text.lower()
    material_lines = [line.strip() for line in material_text.splitlines() if line.strip()]
    checklist: list[RegulationCheckItem] = []

    for section in event_regulation.required_sections:
        markers = SECTION_MARKERS.get(section.lower(), (section.lower(),))
        evidence_line = _find_line_with_any(material_lines, markers)
        risk = "high" if section.lower() in HIGH_RISK_REQUIRED_SECTIONS else "medium"
        if evidence_line:
            checklist.append(
                RegulationCheckItem(
                    requirement=f"В материале должен быть раздел или явная часть: {section}.",
                    status="met",
                    evidence_from_material=_shorten(evidence_line, 180),
                    risk_level="low",
                    recommendation="Требование найдено; перед сдачей проверьте, что раздел связан с главным выводом.",
                )
            )
        else:
            checklist.append(
                RegulationCheckItem(
                    requirement=f"В материале должен быть раздел или явная часть: {section}.",
                    status="missing",
                    evidence_from_material="В загруженном материале явный маркер не найден.",
                    risk_level=risk,
                    recommendation=f"Добавить короткий раздел или явную формулировку: {section}.",
                )
            )

    for requirement in event_regulation.formatting_requirements[:3]:
        checklist.append(
            RegulationCheckItem(
                requirement=requirement,
                status="unverifiable",
                evidence_from_material="По извлечённому тексту нельзя надёжно проверить оформление, объём страниц или формат файла.",
                risk_level="medium",
                recommendation="Проверить это требование вручную перед отправкой.",
            )
        )

    for forbidden in event_regulation.forbidden_items[:3]:
        checklist.append(
            RegulationCheckItem(
                requirement=forbidden,
                status="unverifiable" if not _forbidden_marker_found(material_lower, forbidden) else "partially_met",
                evidence_from_material=(
                    "Есть похожий маркер в материале; проверьте формулировку вручную."
                    if _forbidden_marker_found(material_lower, forbidden)
                    else "По тексту нельзя надёжно подтвердить соблюдение запрета."
                ),
                risk_level="medium",
                recommendation="Проверить запрет вручную; не добавлять спорный элемент, если он не нужен для защиты.",
            )
        )

    if not checklist:
        checklist.append(
            RegulationCheckItem(
                requirement="Регламент приложен, но конкретные проверяемые требования выделить не удалось.",
                status="unverifiable",
                evidence_from_material="В тексте регламента нет явных маркеров требований или критериев.",
                risk_level="medium",
                recommendation="Сверить материал с регламентом вручную по оригинальному файлу.",
            )
        )

    return checklist[:14]


def _critical_regulation_items(regulation_analysis: RegulationAnalysis | None) -> list[str]:
    if not regulation_analysis:
        return []
    return [
        item.recommendation
        for item in regulation_analysis.checklist
        if item.risk_level == "high" and item.status in {"missing", "partially_met"}
    ]


def _claim_fix_items(claims: Iterable[Claim]) -> list[str]:
    return [claim.recommendation for claim in claims if claim.recommendation][:3]


def _dangerous_question_fix(result) -> str:
    return result.stress_test.what_to_add or "Подготовить ответ на самый опасный вопрос аудитории."


def _structure_critical_fixes(result) -> list[str]:
    fixes: list[str] = []
    for problem in result.structure_analysis.problems:
        lowered = problem.lower()
        if any(marker in lowered for marker in ("цель", "метод", "вывод", "заключ")):
            fixes.append(problem)
    return fixes[:2]


def _confidence_level(result) -> str:
    if not result.claims or "Не удалось выделить основной текст для анализа." in result.warnings:
        return "low"
    if result.persuasiveness_score >= 75 and len(result.claims) >= 3 and len(result.audience_questions) >= 4:
        return "high"
    return "medium"


def _safe_to_ignore_items(
    audience_knowledge_level: int,
    regulation_analysis: RegulationAnalysis | None,
    benchmark_comparison: BenchmarkComparison | None,
) -> list[str]:
    items = [
        "Мелкие стилистические улучшения, если осталось меньше часа.",
        "Дополнительные примеры, если основной пример уже подтверждает тезис.",
    ]
    if regulation_analysis is None:
        items.append("Специальные требования конкурса, если регламент не загружен и их нельзя проверить по материалу.")
    if benchmark_comparison is None:
        items.append("Сравнение с идеальной работой, если эталона сейчас нет под рукой.")
    if audience_knowledge_level <= 2:
        items.append("Глубокие методологические детали, если аудитории сначала нужно понять базовый контекст.")
    elif audience_knowledge_level >= 4:
        items.append("Упрощение каждого термина, если аудитория экспертная и терминология уместна.")
    return items[:4]


def _stop_doing_items(audience_knowledge_level: int, regulation_analysis: RegulationAnalysis | None) -> list[str]:
    items = [
        "Не переписывайте весь текст с нуля, если проблема только в доказательствах нескольких утверждений.",
        "Не ищите десятый источник, пока не закрыты самые рискованные утверждения.",
        "Не расширяйте тему, если текущий вывод можно защитить точнее.",
    ]
    if regulation_analysis is not None:
        items.append("Не добавляйте новые разделы, если они не требуются регламентом и не закрывают риск защиты.")
    if audience_knowledge_level <= 2:
        items.append("Не усложняйте термины, если аудитория почти не знакома с темой.")
    else:
        items.append("Не добавляйте длинные объяснения очевидных терминов, если аудитория подготовленная.")
    return items[:4]


def _timeboxed_plan(
    next_actions: list[str],
    critical_fixes: list[str],
    optional_improvements: list[str],
) -> dict[str, list[str]]:
    first = next_actions[0] if next_actions else "Выберите один ключевой риск."
    second = next_actions[1] if len(next_actions) > 1 else "Подготовьте ответ на самый опасный вопрос."
    third = next_actions[2] if len(next_actions) > 2 else "Проверьте финальный вывод."
    optional = optional_improvements[0] if optional_improvements else "Сделайте только лёгкую редактуру без расширения темы."
    critical = critical_fixes[0] if critical_fixes else first
    return {
        "15 минут": [first],
        "30 минут": [first, second],
        "60 минут": [critical, second, third],
        "если есть вечер": [*next_actions[:3], optional],
    }


def _reassuring_summary(verdict: str, critical_fixes: list[str]) -> str:
    if verdict == "ready":
        return (
            "Материал уже выглядит защищаемым для выбранной аудитории. "
            "После короткой проверки ключевых ответов можно остановиться."
        )
    if verdict == "almost_ready":
        return (
            "Материал не обязан быть идеальным. Если закрыть три действия с максимальным эффектом, "
            "можно спокойно идти на защиту."
        )
    if critical_fixes:
        return (
            "Сейчас важны не бесконечные улучшения, а несколько критичных правок. "
            "Начните с них и не расширяйте работу сверх цели."
        )
    return (
        "Материал требует усиления, но это решается точечными шагами: уточнить вывод, закрыть доказательства "
        "и подготовить ответ на главный вопрос."
    )


def _when_to_stop(next_actions: list[str]) -> str:
    if not next_actions:
        return "Остановитесь после проверки главного вывода и ответа на самый опасный вопрос."
    joined = "; ".join(next_actions[:3])
    return f"Остановитесь после того, как выполните эти действия: {joined}."


def _extract_event_name(text: str) -> str | None:
    for line in _lines(text)[:12]:
        lowered = line.lower()
        if any(marker in lowered for marker in ("конкурс", "конференц", "хакатон", "защит", "олимпиад", "положение")):
            return _shorten(line, 160)
    return None


def _extract_work_format(text: str) -> str | None:
    formats = ("реферат", "доклад", "проект", "презентация", "питч", "эссе", "статья", "исследовательская работа")
    lowered = text.lower()
    found = [format_name for format_name in formats if format_name in lowered]
    return ", ".join(found[:3]) if found else None


def _extract_required_sections(text: str) -> list[str]:
    lowered = text.lower()
    required_context = any(marker in lowered for marker in ("долж", "обяз", "треб", "содерж", "структур", "включ"))
    sections: list[str] = []
    for section, markers in SECTION_MARKERS.items():
        if any(marker in lowered for marker in markers) and required_context:
            sections.append(section)
    return _first_unique(sections, limit=12)


def _extract_deadlines(text: str) -> list[str]:
    lines = _extract_lines(text, ("срок", "дедлайн", "до ", "не позднее"), limit=6)
    dates = re.findall(r"\b\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?\b", text)
    for date in dates:
        lines.append(f"Дата или срок: {date}")
    return _first_unique(lines, limit=8)


def _extract_lines(text: str, markers: tuple[str, ...], *, limit: int) -> list[str]:
    result: list[str] = []
    for line in _lines(text):
        lowered = line.lower()
        if any(marker in lowered for marker in markers):
            result.append(_shorten(line, 220))
        if len(result) >= limit:
            break
    return _first_unique(result, limit=limit)


def _summarize_regulation(text: str) -> str:
    event_name = _extract_event_name(text)
    criteria_count = len(_extract_lines(text, ("критер", "оцени", "балл"), limit=20))
    section_count = len(_extract_required_sections(text))
    if event_name:
        return f"{event_name}. Выделено требований к разделам: {section_count}, критериев/оценочных маркеров: {criteria_count}."
    return f"Выделено требований к разделам: {section_count}, критериев/оценочных маркеров: {criteria_count}."


def _text_features(text: str) -> dict[str, object]:
    normalized = _normalize_text(text)
    lowered = normalized.lower()
    sentences = [sentence for sentence in re.split(r"(?<=[.!?])\s+|\n+", normalized) if sentence.strip()]
    words = re.findall(r"[A-Za-zА-Яа-яЁё0-9-]+", normalized)
    sections = {section: any(marker in lowered for marker in markers) for section, markers in SECTION_MARKERS.items()}
    evidence_markers = sum(
        1
        for marker in ("исслед", "опрос", "данн", "расч", "пример", "источник", "литератур", "эксперимент", "метод")
        if marker in lowered
    )
    return {
        "sections": sections,
        "section_count": sum(1 for present in sections.values() if present),
        "paragraph_count": len([part for part in re.split(r"\n{2,}", normalized) if part.strip()]),
        "sentence_count": len(sentences),
        "avg_sentence_words": (len(words) / len(sentences)) if sentences else 0,
        "number_count": len(re.findall(r"\d", normalized)),
        "evidence_markers": evidence_markers,
        "has_limitations": any(marker in lowered for marker in ("огранич", "исключени", "границ", "риск")),
        "has_questions": "вопрос" in lowered,
        "word_count": len(words),
    }


def _build_structure_gap(user: dict[str, object], benchmark: dict[str, object]) -> ComparisonItem:
    missing_sections = _missing_benchmark_elements(user, benchmark)
    gap = "high" if len(missing_sections) >= 3 else "medium" if missing_sections else "low"
    return ComparisonItem(
        aspect="Структура",
        user_material_observation=f"В материале явно найдено разделов: {user['section_count']}.",
        benchmark_observation=f"В эталоне явно найдено разделов: {benchmark['section_count']}.",
        gap_level=gap,
        recommendation=(
            "Добавить недостающие опорные части: " + ", ".join(missing_sections[:4])
            if missing_sections
            else "Структурный разрыв небольшой; не копируйте порядок эталона без необходимости."
        ),
    )


def _build_evidence_gap(user: dict[str, object], benchmark: dict[str, object]) -> ComparisonItem:
    user_score = int(user["evidence_markers"]) + min(5, int(user["number_count"]))
    benchmark_score = int(benchmark["evidence_markers"]) + min(5, int(benchmark["number_count"]))
    difference = benchmark_score - user_score
    gap = "high" if difference >= 4 else "medium" if difference >= 2 else "low"
    return ComparisonItem(
        aspect="Доказательность",
        user_material_observation=f"Опорных маркеров доказательности: {user_score}.",
        benchmark_observation=f"В эталоне таких маркеров: {benchmark_score}.",
        gap_level=gap,
        recommendation=(
            "Добавить доказательство к 1-2 центральным утверждениям: данные, пример, метод или ограничение."
            if gap != "low"
            else "Доказательная плотность сопоставима; достаточно проверить самые рискованные утверждения."
        ),
    )


def _build_clarity_gap(user: dict[str, object], benchmark: dict[str, object]) -> ComparisonItem:
    user_avg = float(user["avg_sentence_words"])
    benchmark_avg = float(benchmark["avg_sentence_words"])
    gap = "medium" if user_avg > benchmark_avg + 7 and user_avg > 24 else "low"
    return ComparisonItem(
        aspect="Понятность",
        user_material_observation=f"Средняя длина предложения: {user_avg:.1f} слов.",
        benchmark_observation=f"В эталоне: {benchmark_avg:.1f} слов.",
        gap_level=gap,
        recommendation=(
            "Разбить самые длинные объяснения и добавить короткие связки между тезисами."
            if gap != "low"
            else "По длине объяснений серьёзного разрыва с эталоном не видно."
        ),
    )


def _build_detail_gap(user: dict[str, object], benchmark: dict[str, object]) -> ComparisonItem:
    user_words = int(user["word_count"])
    benchmark_words = int(benchmark["word_count"])
    gap = "medium" if benchmark_words > user_words * 1.6 and benchmark_words - user_words > 250 else "low"
    return ComparisonItem(
        aspect="Уровень детализации",
        user_material_observation=f"Объём материала: около {user_words} слов.",
        benchmark_observation=f"Объём эталона: около {benchmark_words} слов.",
        gap_level=gap,
        recommendation=(
            "Добавлять детали только там, где они закрывают вопрос аудитории или требование регламента."
            if gap != "low"
            else "Не увеличивайте объём ради сходства с эталоном."
        ),
    )


def _build_readiness_gap(user: dict[str, object], benchmark: dict[str, object]) -> ComparisonItem:
    user_ready = bool(user["has_limitations"] or user["has_questions"])
    benchmark_ready = bool(benchmark["has_limitations"] or benchmark["has_questions"])
    gap = "medium" if benchmark_ready and not user_ready else "low"
    return ComparisonItem(
        aspect="Готовность к вопросам",
        user_material_observation="Ограничения или возможные вопросы обозначены." if user_ready else "Ограничения и возможные вопросы явно не найдены.",
        benchmark_observation="В эталоне есть подготовка к ограничениям или вопросам." if benchmark_ready else "В эталоне такой блок явно не найден.",
        gap_level=gap,
        recommendation=(
            "Добавить короткий блок с ограничениями и ответом на самый опасный вопрос."
            if gap != "low"
            else "Достаточно подготовить устный ответ на главный риск."
        ),
    )


def _missing_benchmark_elements(user: dict[str, object], benchmark: dict[str, object]) -> list[str]:
    user_sections = user["sections"]
    benchmark_sections = benchmark["sections"]
    if not isinstance(user_sections, dict) or not isinstance(benchmark_sections, dict):
        return []
    return [
        section
        for section, benchmark_has in benchmark_sections.items()
        if benchmark_has and not user_sections.get(section)
    ][:8]


def _benchmark_strengths(features: dict[str, object]) -> list[str]:
    strengths: list[str] = []
    if int(features["section_count"]) >= 5:
        strengths.append("У эталона явно выражена структура.")
    if int(features["evidence_markers"]) >= 4:
        strengths.append("В эталоне плотнее показаны доказательства, методы или примеры.")
    if bool(features["has_limitations"]):
        strengths.append("Эталон заранее показывает ограничения или риски.")
    if not strengths:
        strengths.append("Эталон полезен как ориентир подачи, но не как текст для копирования.")
    return strengths[:4]


def _benchmark_patterns(user: dict[str, object], benchmark: dict[str, object]) -> list[str]:
    missing = _missing_benchmark_elements(user, benchmark)
    patterns = [f"Явно обозначить блок: {section}." for section in missing[:3]]
    if bool(benchmark["has_limitations"]) and not bool(user["has_limitations"]):
        patterns.append("Добавить короткий блок ограничений перед выводом.")
    if not patterns:
        patterns.append("Сохранить свою идею, но проверить ясность переходов между разделами.")
    return patterns[:4]


def _user_advantages(user: dict[str, object], benchmark: dict[str, object]) -> list[str]:
    advantages: list[str] = []
    if float(user["avg_sentence_words"]) < float(benchmark["avg_sentence_words"]) - 4:
        advantages.append("Материал пользователя короче и может читаться проще.")
    if int(user["number_count"]) > int(benchmark["number_count"]):
        advantages.append("В материале пользователя больше числовых маркеров, которые можно превратить в доказательства.")
    user_sections = user["sections"]
    benchmark_sections = benchmark["sections"]
    if isinstance(user_sections, dict) and isinstance(benchmark_sections, dict):
        for section in ("цель", "вывод", "методы"):
            if user_sections.get(section) and not benchmark_sections.get(section):
                advantages.append(f"У пользователя явнее обозначен блок: {section}.")
    if not advantages:
        advantages.append("Материал пользователя сохраняет собственную тему и авторскую логику; её не нужно заменять эталоном.")
    return advantages[:4]


def _benchmark_advantages(comparison_items: list[ComparisonItem], missing_elements: list[str]) -> list[str]:
    advantages = [
        item.recommendation
        for item in comparison_items
        if item.gap_level in {"medium", "high"} and item.recommendation
    ]
    if missing_elements:
        advantages.insert(0, "В эталоне явнее представлены: " + ", ".join(missing_elements[:4]) + ".")
    if not advantages:
        advantages.append("Сильного разрыва с эталоном не видно; используйте его только как ориентир самопроверки.")
    return _first_unique(advantages, limit=4)


def _benchmark_action_items(comparison_items: list[ComparisonItem], missing_elements: list[str]) -> list[str]:
    actions = [item.recommendation for item in comparison_items if item.gap_level in {"medium", "high"}]
    actions.extend(f"Добавить или явно подписать блок: {element}." for element in missing_elements[:3])
    if not actions:
        actions.append("Сверить финальный вывод с эталоном по ясности, не копируя текст.")
    return _first_unique(actions, limit=5)


def _structure_observation(features: dict[str, object]) -> str:
    return (
        f"Разделов с явными маркерами: {features['section_count']}; "
        f"абзацев: {features['paragraph_count']}; "
        f"средняя длина предложения: {float(features['avg_sentence_words']):.1f} слов."
    )


def _forbidden_marker_found(material_lower: str, forbidden_line: str) -> bool:
    words = [
        word
        for word in re.findall(r"[а-яёa-z0-9-]{4,}", forbidden_line.lower())
        if word not in {"запрещается", "нельзя", "допускается", "недопустимо"}
    ]
    return any(word in material_lower for word in words[:4])


def _find_line_with_any(lines: list[str], markers: tuple[str, ...]) -> str:
    for line in lines:
        lowered = line.lower()
        if any(marker in lowered for marker in markers):
            return line
    return ""


def _first_sentence(text: str) -> str:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+|\n+", text.strip()) if sentence.strip()]
    return _shorten(sentences[0], 220) if sentences else ""


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _lines(text: str) -> list[str]:
    return [line.strip() for line in _normalize_text(text).splitlines() if line.strip()]


def _shorten(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _first_unique(items: Iterable[str], *, limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = re.sub(r"\s+", " ", str(item)).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
        if len(result) >= limit:
            break
    return result
