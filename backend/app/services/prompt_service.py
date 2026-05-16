from __future__ import annotations

import json
from pathlib import Path

AUDIENCE_RULES: dict[str, str] = {
    "учитель": "Фокус: тема, цель, гипотеза, задачи, методы, вывод, источники, самостоятельность и понятность. Вопросы задаёт учитель. Не используй слова инвестор, бизнес-ценность, рынок.",
    "преподаватель": "Фокус: методология, структура, доказательность, источники и выводы.",
    "комиссия": "Фокус: цель, метод, результаты, ограничения, новизна и выводы.",
    "жюри": "Фокус: проблема, решение, отличие от аналогов, демонстрация, реалистичность и метрики успеха.",
    "инвестор": "Фокус: рынок, пользователь, боль, бизнес-модель, конкуренты, масштабирование и риски.",
    "коллеги": "Фокус: практическая польза, реализация, риски и понятность.",
    "широкая аудитория": "Фокус: простота, ясность, отсутствие перегруза и понятные примеры.",
}


MATERIAL_RULES: dict[str, str] = {
    "сочинение": "Фокус: тезис, аргументы, примеры, связь аргументов с темой и вывод.",
    "реферат": "Фокус: цель, структура, источники, пересказ против собственного вывода и итоговый вывод.",
    "курсовая": "Фокус: актуальность, объект/предмет, цель, задачи, методология, источники, результаты и выводы.",
    "диплом": "Фокус: актуальность, объект/предмет, цель, задачи, методология, источники, результаты и выводы.",
    "диссертация": "Фокус: актуальность, объект/предмет, цель, задачи, методология, источники, результаты и выводы.",
    "презентация": "Фокус: проблема, аудитория, решение, отличие от аналогов, метрики и вопросы жюри.",
    "питч": "Фокус: проблема, аудитория, решение, отличие от аналогов, метрики и вопросы жюри.",
    "публичное выступление": "Фокус: ясность, структура, удержание внимания, убедительность и вопросы аудитории.",
}


class PromptService:
    def __init__(self, prompts_dir: Path | None = None) -> None:
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parents[1] / "prompts"

    def system_prompt(self) -> str:
        return self._load("system_prompt.txt")

    def build_user_prompt(
        self,
        *,
        text: str,
        filename: str,
        material_type: str,
        audience_type: str,
    ) -> str:
        prompt_parts = [
            self._load("structure_prompt.txt"),
            self._load("claims_prompt.txt"),
            self._load("scoring_prompt.txt"),
            self._load("questions_prompt.txt"),
            self._load("recommendations_prompt.txt"),
            self._load("final_json_prompt.txt"),
            self._audience_rules(audience_type),
            self._material_rules(material_type),
            "Контекст анализа уже прошёл preprocessing: титульный лист, содержание, список литературы и приложения не должны становиться claims.",
            "Анализируй только загруженный материал. Не используй внешние источники. Не выдумывай ссылки, цитаты и факты.",
            "Если утверждение не подтверждается внутри материала, используй evidence_status needs_source или unverifiable_from_text.",
            "Вопросы аудитории должны быть привязаны к реальным слабым местам текста.",
            "Не пиши работу за пользователя и не создавай новый материал вместо автора.",
            f"Файл: {filename}",
            f"Тип материала: {material_type}",
            f"Аудитория: {audience_type}",
            "Контракт JSON AnalysisResult:",
            self._compact_output_contract(),
            "Текст материала:",
            f'"""\n{text}\n"""',
        ]
        return "\n\n".join(part.strip() for part in prompt_parts if part.strip())

    def _load(self, filename: str) -> str:
        path = self.prompts_dir / filename
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def _audience_rules(self, audience_type: str) -> str:
        normalized = audience_type.lower()
        for key, rules in AUDIENCE_RULES.items():
            if key in normalized:
                return f"Правила для аудитории '{audience_type}': {rules}"
        return f"Правила для аудитории '{audience_type}': адаптируй вопросы и лексику под эту аудиторию."

    def _material_rules(self, material_type: str) -> str:
        normalized = material_type.lower()
        for key, rules in MATERIAL_RULES.items():
            if key in normalized:
                return f"Правила для типа материала '{material_type}': {rules}"
        return f"Правила для типа материала '{material_type}': оцени структуру, тезисы, доказательства, вывод и готовность к вопросам."

    def _compact_output_contract(self) -> str:
        return json.dumps(
            {
                "id": "analysis_yandex",
                "filename": "string",
                "material_type": "string",
                "audience_type": "string",
                "provider_name": "yandex",
                "provider_model": "string",
                "provider_response_id": None,
                "is_mock": False,
                "title": "string",
                "created_at": "ISO datetime string",
                "persuasiveness_score": "0..100 integer",
                "scoring_breakdown": {
                    "clarity_score": "0..100 integer",
                    "structure_score": "0..100 integer",
                    "argument_score": "0..100 integer",
                    "evidence_score": "0..100 integer",
                    "audience_score": "0..100 integer",
                    "question_readiness_score": "0..100 integer",
                    "explanation": "1 short sentence",
                },
                "summary": "2 short sentences",
                "main_idea": "1 short paragraph",
                "strengths": ["3-5 short strings"],
                "weaknesses": [
                    {
                        "problem": "string",
                        "why_problem": "string",
                        "audience_signal": "string",
                        "fix": "string",
                    }
                ],
                "risks": ["2-4 short strings"],
                "warnings": [],
                "structure_analysis": {
                    "main_idea": "string",
                    "goal": "string",
                    "target_audience": "string",
                    "structure_summary": "2 short sentences",
                    "logic_quality_score": "0..100 integer",
                    "clarity_score": "0..100 integer",
                    "problems": ["0-4 short strings"],
                    "suggestions": ["0-4 short strings"],
                },
                "claims": [
                    {
                        "id": "claim_1",
                        "text": "string",
                        "claim_type": "fact|number|comparison|causality|generalization|opinion|definition|unsupported_conclusion",
                        "location": "short location",
                        "needs_evidence": True,
                        "evidence_status": "supported_by_text|needs_source|weak_argument|too_strong|unverifiable_from_text|ok",
                        "risk_level": "low|medium|high",
                        "explanation": "short string",
                        "recommendation": "short string",
                        "suggested_rewrite": "short string",
                    }
                ],
                "recommendations": [
                    {
                        "id": "rec_1",
                        "priority": "low|medium|high",
                        "category": "string",
                        "problem": "string",
                        "action": "string",
                        "expected_effect": "string",
                    }
                ],
                "audience_questions": [
                    {
                        "id": "question_1",
                        "question": "string",
                        "asked_by": "string",
                        "category": "Вся работа: ... | Проблемное место: ...",
                        "why_asked": "string",
                        "risk_level": "low|medium|high",
                        "suggested_answer": "string",
                        "how_to_improve_material": "string",
                    }
                ],
                "improvement_plan": {
                    "quick_fixes_30_min": ["2-4 short strings"],
                    "improvements_2_hours": ["2-4 short strings"],
                    "final_polish": ["2-4 short strings"],
                },
                "stress_test": {
                    "most_dangerous_question": "string",
                    "why_dangerous": "string",
                    "exposed_weakness": "string",
                    "suggested_answer": "string",
                    "what_to_add": "string",
                },
            },
            ensure_ascii=False,
        )
