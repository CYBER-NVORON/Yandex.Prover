from __future__ import annotations

import json
from pathlib import Path

from app.schemas import AnalysisResult


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
        schema = json.dumps(AnalysisResult.model_json_schema(), ensure_ascii=False)
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
            "JSON schema AnalysisResult:",
            schema,
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
