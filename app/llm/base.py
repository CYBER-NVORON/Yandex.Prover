from __future__ import annotations

from abc import ABC, abstractmethod

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
    ) -> AnalysisResult:
        raise NotImplementedError

    def parse_analysis_json(self, payload: str) -> AnalysisResult:
        try:
            return AnalysisResult.model_validate_json(payload)
        except ValidationError as exc:
            raise InvalidLLMResponseError("LLM вернула JSON, который не соответствует схеме анализа.") from exc

