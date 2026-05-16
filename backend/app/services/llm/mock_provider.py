from __future__ import annotations

import re
from pathlib import Path

from app.services.claim_extractor import extract_claims, split_sentences
from app.services.document_preprocessor import PreprocessedDocument, filter_noise_claims, preprocess_document
from app.services.llm.base import LLMProvider
from app.services.question_generator import build_audience_questions, build_stress_test
from app.services.recommendation_engine import build_improvement_plan, build_recommendations, build_weaknesses
from app.schemas import AnalysisResult, Claim, ScoringBreakdown, StructureAnalysis
from app.services.scoring import score_from_breakdown


class MockLLMProvider(LLMProvider):
    """Deterministic demo provider with realistic local analysis."""

    def analyze_material(
        self,
        *,
        text: str,
        filename: str,
        material_type: str,
        audience_type: str,
    ) -> AnalysisResult:
        preprocessed = preprocess_document(text)
        clean_text = self._normalize(preprocessed.clean_text or preprocessed.analysis_text or text)
        analysis_text = self._normalize(preprocessed.analysis_text or clean_text)
        claims = filter_noise_claims(
            self._ensure_claims(extract_claims(analysis_text, limit=12), analysis_text, material_type)
        )
        main_idea = self._detect_main_idea(clean_text, material_type, preprocessed)
        title = self._build_title(filename, material_type, preprocessed)
        structure = self._build_structure(clean_text, analysis_text, main_idea, material_type, audience_type, preprocessed)
        scoring = self._score(clean_text, claims, material_type, audience_type, structure)
        score = score_from_breakdown(scoring)
        strengths = self._build_strengths(clean_text, material_type, audience_type, preprocessed)
        weaknesses = build_weaknesses(claims, material_type, audience_type)
        recommendations = build_recommendations(claims, weaknesses)
        questions = build_audience_questions(
            claims=claims,
            weaknesses=weaknesses,
            audience_type=audience_type,
            material_type=material_type,
        )
        improvement_plan = build_improvement_plan(recommendations, claims)
        stress_test = build_stress_test(questions, weaknesses)

        risks = [
            "Самые сильные утверждения требуют подтверждения внутри материала.",
            "Аудитория может попросить объяснить ограничения идеи и критерии сравнения.",
            "Некоторые выводы звучат шире, чем доказательная база текста.",
        ]
        if any(claim.risk_level == "high" for claim in claims):
            risks.insert(0, "Есть высокорисковые утверждения со статусом 'нужен источник'.")

        return AnalysisResult(
            filename=filename,
            material_type=material_type,
            audience_type=audience_type,
            provider_name="mock",
            provider_model="mock",
            provider_response_id=None,
            is_mock=True,
            title=title,
            persuasiveness_score=score,
            scoring_breakdown=scoring,
            summary=self._build_summary(score, material_type, audience_type, claims),
            main_idea=main_idea,
            strengths=strengths,
            weaknesses=weaknesses,
            risks=risks[:4],
            structure_analysis=structure,
            claims=claims[:10],
            recommendations=recommendations,
            audience_questions=questions,
            improvement_plan=improvement_plan,
            stress_test=stress_test,
        )

    def _normalize(self, text: str) -> str:
        return re.sub(r"\n{3,}", "\n\n", text.strip())

    def _build_title(self, filename: str, material_type: str, preprocessed: PreprocessedDocument | None = None) -> str:
        if preprocessed and preprocessed.title:
            return f"Анализ: {preprocessed.title} ({material_type})"
        stem = Path(filename).stem.replace("_", " ").replace("-", " ").strip()
        readable = stem[:1].upper() + stem[1:] if stem else "материала"
        return f"Анализ: {readable} ({material_type})"

    def _detect_main_idea(
        self,
        text: str,
        material_type: str,
        preprocessed: PreprocessedDocument | None = None,
    ) -> str:
        if self._is_academic_material(material_type):
            conclusion = self._section_value(preprocessed, "conclusion")
            conclusion_sentence = self._first_sentence_with_markers(
                conclusion,
                ("разные", "отличаются", "доказ", "вывод", "подтвер"),
            )
            if conclusion_sentence:
                return conclusion_sentence[:350]

            hypothesis = self._section_value(preprocessed, "hypothesis")
            if hypothesis:
                return self._strip_label(self._first_sentence(hypothesis) or hypothesis)[:350]

        sentences = split_sentences(text)
        for marker in ("главная идея", "идея", "цель", "мы предлагаем", "проект", "тезис"):
            for sentence in sentences[:12]:
                if marker in sentence.lower():
                    return sentence[:350]
        if "питч" in material_type.lower() or "проект" in text.lower():
            return "Материал предлагает решение значимой проблемы, но требует более точных доказательств масштаба, ценности и отличия от альтернатив."
        if sentences:
            return sentences[0][:350]
        return "Главная мысль требует явной формулировки в начале материала."

    def _build_structure(
        self,
        clean_text: str,
        analysis_text: str,
        main_idea: str,
        material_type: str,
        audience_type: str,
        preprocessed: PreprocessedDocument | None = None,
    ) -> StructureAnalysis:
        paragraph_count = len([part for part in clean_text.split("\n\n") if part.strip()])
        lower_text = analysis_text.lower()
        explicit_goal = self._section_value(preprocessed, "goal") or self._labeled_value(
            analysis_text,
            ("цель работы", "цель исследования", "цель проекта", "цель"),
        )
        explicit_hypothesis = self._section_value(preprocessed, "hypothesis")
        explicit_methods = self._section_value(preprocessed, "methods")
        explicit_conclusion = self._section_value(preprocessed, "conclusion")
        has_goal = bool(explicit_goal) or any(word in lower_text for word in ("цель", "задача", "мы предлагаем", "показать"))
        has_hypothesis = bool(explicit_hypothesis)
        has_methods = bool(explicit_methods) or "метод" in lower_text
        has_conclusion = bool(explicit_conclusion) or any(
            word in lower_text for word in ("вывод", "итак", "таким образом", "в результате")
        )
        problems = []
        suggestions = []
        if not has_goal:
            problems.append("Цель материала не выделена отдельной формулировкой.")
            suggestions.append("Добавить в начало предложение с целью и ожидаемым результатом.")
        if self._is_academic_material(material_type) and not has_hypothesis:
            problems.append("Гипотеза исследования не выделена явно.")
            suggestions.append("Если работа проверяет предположение, оформить его отдельной строкой 'Гипотеза'.")
        if self._is_academic_material(material_type) and not has_methods:
            problems.append("Методы исследования стоит показать отдельным блоком.")
            suggestions.append("Добавить короткий список методов: наблюдение, сравнение, анкетирование или анализ источников.")
        if not has_conclusion:
            problems.append("Финальный вывод можно сделать явнее.")
            suggestions.append("Закончить материал выводом, который возвращает к главной мысли.")
        if paragraph_count < 3:
            problems.append("Структура выглядит слишком плотной: мало отдельных смысловых блоков.")
            suggestions.append("Разделить материал на проблему, аргументы, доказательства и вывод.")
        if "питч" in material_type.lower():
            problems.append("Блок конкурентов и метрик стоит сделать конкретнее.")
            suggestions.append("Добавить отдельные блоки: масштаб проблемы, альтернативы, метрики результата.")

        clarity = 76 if has_goal else 64
        logic = 72 if has_conclusion else 62
        if paragraph_count >= 4:
            logic += 6
        if problems:
            clarity -= min(10, len(problems) * 2)
            logic -= min(10, len(problems) * 2)

        return StructureAnalysis(
            main_idea=main_idea,
            goal=self._strip_label(explicit_goal) if explicit_goal else "Цель подразумевается, но её нужно сформулировать явно.",
            target_audience=audience_type,
            structure_summary="Материал содержит основу для защиты: проблему, несколько тезисов и вывод. Главный резерв роста - связать тезисы с доказательствами и критериями оценки.",
            logic_quality_score=max(0, min(100, logic)),
            clarity_score=max(0, min(100, clarity)),
            problems=problems[:5],
            suggestions=suggestions[:5],
        )

    def _score(
        self,
        text: str,
        claims: list[Claim],
        material_type: str,
        audience_type: str,
        structure: StructureAnalysis,
    ) -> ScoringBreakdown:
        high_risk = sum(1 for claim in claims if claim.risk_level == "high")
        medium_risk = sum(1 for claim in claims if claim.risk_level == "medium")
        has_metrics = bool(re.search(r"\d", text))
        has_audience = audience_type.lower() in text.lower()
        is_pitch = "питч" in material_type.lower()

        clarity = structure.clarity_score
        structure_score = structure.logic_quality_score
        argument = 68 - high_risk * 3 - medium_risk
        evidence = 66 - high_risk * 5 - medium_risk * 2
        audience = 70 + (6 if has_audience else 0)
        readiness = 62 - high_risk * 2

        if is_pitch:
            argument -= 4
            evidence -= 5 if not has_metrics else 1
            readiness -= 2
        else:
            argument += 3
            readiness += 2

        return ScoringBreakdown(
            clarity_score=max(0, min(100, clarity)),
            structure_score=max(0, min(100, structure_score)),
            argument_score=max(0, min(100, argument)),
            evidence_score=max(0, min(100, evidence)),
            audience_score=max(0, min(100, audience)),
            question_readiness_score=max(0, min(100, readiness)),
            explanation="Оценка рассчитана по шести критериям MVP: ясность, структура, аргументы, доказательность, понятность для аудитории и готовность к вопросам.",
        )

    def _build_strengths(
        self,
        text: str,
        material_type: str,
        audience_type: str,
        preprocessed: PreprocessedDocument | None = None,
    ) -> list[str]:
        strengths = [
            "В материале уже есть распознаваемая центральная идея, вокруг которой можно строить защиту.",
            "Тема сформулирована достаточно понятно для первого чтения.",
            "Есть задел для вопросов аудитории: проблему можно обсуждать и проверять.",
        ]
        lower = text.lower()
        if any(word in lower for word in ("пример", "кейс", "исследование", "методология")):
            strengths.append("В тексте есть элементы доказательной базы, которые можно развить.")
        if preprocessed and preprocessed.references_text:
            strengths.append("В материале есть список литературы; теперь важно привязать источники к конкретным утверждениям.")
        if "питч" in material_type.lower() or "проект" in lower:
            if self._is_teacher_audience(audience_type):
                strengths.append("Практическая часть может усилить защиту исследовательской работы перед учителем.")
            else:
                strengths.append("Проблема подана как прикладная, поэтому её удобно переводить в ценность для жюри или инвестора.")
        return strengths[:5]

    def _build_summary(
        self,
        score: int,
        material_type: str,
        audience_type: str,
        claims: list[Claim],
    ) -> str:
        risky = sum(1 for claim in claims if claim.risk_level in {"high", "medium"})
        if score >= 75:
            level = "Материал выглядит достаточно устойчивым"
        elif score >= 60:
            level = "Материал уже можно показывать на предзащите, но он уязвим к уточняющим вопросам"
        else:
            level = "Материал требует усиления перед выступлением"
        return (
            f"{level}: для формата '{material_type}' и аудитории '{audience_type}' главный риск связан "
            f"с доказательностью {risky} утверждений и явностью выводов. Улучшения стоит начать с источников, "
            "примеров и более осторожных формулировок."
        )

    def _ensure_claims(self, claims: list[Claim], text: str, material_type: str) -> list[Claim]:
        if claims and "питч" not in material_type.lower():
            return claims

        fallback = [
            Claim(
                id="claim_fallback_1",
                text="Идея решает значимую проблему выбранной аудитории.",
                claim_type="unsupported_conclusion",
                location="обобщение по материалу",
                needs_evidence=True,
                evidence_status="weak_argument",
                risk_level="medium",
                explanation="Ценность идеи нужно доказать через пример, метрику или сравнение.",
                recommendation="Добавить конкретный пример проблемы и показать, почему текущее решение недостаточно.",
                suggested_rewrite="Идея может решить часть проблемы выбранной аудитории при указанных условиях.",
            ),
            Claim(
                id="claim_fallback_2",
                text="Предложенный подход будет понятен и полезен аудитории.",
                claim_type="opinion",
                location="обобщение по материалу",
                needs_evidence=True,
                evidence_status="unverifiable_from_text",
                risk_level="medium",
                explanation="Понятность и польза не подтверждаются внутри материала автоматически.",
                recommendation="Добавить критерии пользы и показать, как аудитория ими воспользуется.",
                suggested_rewrite="Подход может быть полезен аудитории, если подтвердить критерии пользы.",
            ),
            Claim(
                id="claim_fallback_3",
                text="Вывод следует из приведённых аргументов.",
                claim_type="unsupported_conclusion",
                location="финальная часть материала",
                needs_evidence=True,
                evidence_status="weak_argument",
                risk_level="medium",
                explanation="Связь между аргументами и выводом нужно проговорить явно.",
                recommendation="Перед выводом добавить короткое объяснение, как каждый аргумент работает на главный тезис.",
                suggested_rewrite="Вывод будет сильнее, если явно связать его с приведёнными аргументами.",
            ),
        ]
        if "питч" in material_type.lower():
            fallback.extend(
                [
                    Claim(
                        id="claim_fallback_4",
                        text="Масштаб проблемы достаточен для запуска проекта.",
                        claim_type="generalization",
                        location="питч проекта",
                        needs_evidence=True,
                        evidence_status="needs_source",
                        risk_level="high",
                        explanation="Для питча масштаб проблемы требует метрик или пользовательских подтверждений.",
                        recommendation="Добавить количественную оценку проблемы или результаты интервью.",
                        suggested_rewrite="Первые наблюдения показывают, что проблема может быть значимой для выбранного сегмента.",
                    ),
                    Claim(
                        id="claim_fallback_5",
                        text="Решение отличается от существующих альтернатив.",
                        claim_type="comparison",
                        location="питч проекта",
                        needs_evidence=True,
                        evidence_status="weak_argument",
                        risk_level="medium",
                        explanation="Отличие от альтернатив требует критериев сравнения.",
                        recommendation="Добавить 2-3 альтернативы и сравнить по цене, скорости, удобству или качеству результата.",
                        suggested_rewrite="Решение может отличаться от альтернатив по выбранным критериям, если показать сравнение.",
                    ),
                ]
            )

        combined = claims[:]
        seen = {claim.text.lower() for claim in combined}
        for claim in fallback:
            if claim.text.lower() not in seen:
                combined.append(claim)
                seen.add(claim.text.lower())
            if len(combined) >= 6:
                break
        return combined

    def _is_academic_material(self, material_type: str) -> bool:
        lowered = material_type.lower()
        return any(
            marker in lowered
            for marker in ("реферат", "сочинение", "исследовательская", "доклад", "курсовая", "диплом", "статья")
        )

    def _is_teacher_audience(self, audience_type: str) -> bool:
        return "учитель" in audience_type.lower()

    def _section_value(self, preprocessed: PreprocessedDocument | None, key: str) -> str:
        if not preprocessed:
            return ""
        return preprocessed.sections.get(key, "").strip()

    def _labeled_value(self, text: str, labels: tuple[str, ...]) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        lowered_labels = tuple(label.lower() for label in labels)

        for index, line in enumerate(lines):
            lowered = line.lower().strip(" .")
            for label in lowered_labels:
                if lowered.startswith(label):
                    inline = re.sub(rf"^{re.escape(label)}\s*[:.-]?\s*", "", line, flags=re.IGNORECASE).strip()
                    if inline and inline.lower() != label:
                        return inline
                    if index + 1 < len(lines):
                        return lines[index + 1].strip()
        return ""

    def _first_sentence(self, text: str) -> str:
        sentences = split_sentences(text)
        return sentences[0] if sentences else text.strip()

    def _first_sentence_with_markers(self, text: str, markers: tuple[str, ...]) -> str:
        for sentence in split_sentences(text):
            lowered = sentence.lower()
            if any(marker in lowered for marker in markers):
                return self._strip_label(sentence)
        return ""

    def _strip_label(self, text: str) -> str:
        text = text.strip()
        return re.sub(
            r"^(?:цель(?:\s+работы|\s+исследования)?|гипотеза|заключение|выводы?)\s*[:.-]\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

