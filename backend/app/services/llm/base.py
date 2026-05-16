from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import Any

from pydantic import ValidationError

from app.schemas import AnalysisResult


class LLMProviderError(Exception):
    pass


class InvalidLLMResponseError(LLMProviderError):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def analyze_material(
        self,
        *,
        text: str,
        filename: str,
        material_type: str,
        audience_type: str,
        audience_knowledge_level: int = 3,
        regulation_text: str | None = None,
        benchmark_text: str | None = None,
        regulation_filename: str | None = None,
        benchmark_filename: str | None = None,
    ) -> AnalysisResult:
        raise NotImplementedError

    def parse_analysis_json(self, payload: str) -> AnalysisResult:
        try:
            data = json.loads(payload)
            data = self._normalize_analysis_payload(data)
            return AnalysisResult.model_validate(data)
        except json.JSONDecodeError as exc:
            raise InvalidLLMResponseError("LLM вернула невалидный JSON.") from exc
        except ValidationError as exc:
            details = self._validation_summary(exc)
            raise InvalidLLMResponseError(f"LLM вернула JSON, который не соответствует схеме анализа: {details}") from exc

    def _normalize_analysis_payload(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise InvalidLLMResponseError("LLM вернула JSON, но корневой объект не является словарём.")

        allowed_fields = set(AnalysisResult.model_fields)
        normalized = {key: value for key, value in data.items() if key in allowed_fields}

        # These sections are deterministic backend stages. If the LLM tries to
        # fill them and misses a nested contract detail, the pipeline will still
        # rebuild them after provider parsing.
        normalized["regulation_analysis"] = None
        normalized["benchmark_comparison"] = None
        normalized.pop("overthinking_guard", None)

        self._normalize_recommendations(normalized.get("recommendations"))
        self._normalize_risk_items(normalized.get("claims"))
        self._normalize_risk_items(normalized.get("audience_questions"))

        if not str(normalized.get("title", "")).strip():
            normalized["title"] = "Анализ материала"
        if not str(normalized.get("summary", "")).strip():
            normalized["summary"] = "Материал проанализирован по структуре, доказательности и готовности к вопросам."
        if not str(normalized.get("main_idea", "")).strip():
            structure = normalized.get("structure_analysis")
            if isinstance(structure, dict) and str(structure.get("main_idea", "")).strip():
                normalized["main_idea"] = structure["main_idea"]
            else:
                normalized["main_idea"] = "Главную мысль стоит сформулировать явно."

        return normalized

    def _normalize_recommendations(self, recommendations: Any) -> None:
        if not isinstance(recommendations, list):
            return
        for item in recommendations:
            if isinstance(item, dict):
                item["priority"] = self._risk_value(item.get("priority"), default="medium")

    def _normalize_risk_items(self, items: Any) -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if isinstance(item, dict) and "risk_level" in item:
                item["risk_level"] = self._risk_value(item.get("risk_level"), default="medium")

    def _risk_value(self, value: Any, *, default: str) -> str:
        normalized = str(value or "").strip().lower()
        mapping = {
            "critical": "high",
            "important": "medium",
            "optional": "low",
            "высокий": "high",
            "высокая": "high",
            "средний": "medium",
            "средняя": "medium",
            "низкий": "low",
            "низкая": "low",
        }
        normalized = mapping.get(normalized, normalized)
        return normalized if normalized in {"low", "medium", "high"} else default

    def _validation_summary(self, exc: ValidationError) -> str:
        errors = exc.errors(include_url=False)
        chunks: list[str] = []
        for error in errors[:5]:
            location = ".".join(str(part) for part in error.get("loc", ())) or "root"
            chunks.append(f"{location}: {error.get('msg', 'invalid')}")
        if len(errors) > 5:
            chunks.append(f"ещё {len(errors) - 5} ошибок")
        return "; ".join(chunks)


