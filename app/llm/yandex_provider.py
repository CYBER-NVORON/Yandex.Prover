from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.config import DEFAULT_YANDEX_BASE_URL, DEFAULT_YANDEX_MODEL, normalize_yandex_model
from app.llm.base import InvalidLLMResponseError, LLMProvider, LLMProviderError
from app.schemas import AnalysisResult, LLMResponse
from app.scoring import score_from_breakdown


def _load_prompt(filename: str) -> str:
    path = Path(__file__).resolve().parents[1] / "prompts" / filename
    return path.read_text(encoding="utf-8")


class YandexAIProvider(LLMProvider):
    """Yandex AI provider through the OpenAI-compatible Responses API."""

    def __init__(
        self,
        *,
        api_key: str,
        folder_id: str,
        model: str = DEFAULT_YANDEX_MODEL,
        base_url: str = DEFAULT_YANDEX_BASE_URL,
        fallback_provider: LLMProvider | None = None,
    ) -> None:
        self.api_key = api_key
        self.folder_id = folder_id
        self.model = normalize_yandex_model(model)
        self.model_uri = f"gpt://{folder_id}/{self.model}" if folder_id else ""
        self.base_url = base_url or DEFAULT_YANDEX_BASE_URL
        self.fallback_provider = fallback_provider

    def analyze_material(
        self,
        *,
        text: str,
        filename: str,
        material_type: str,
        audience_type: str,
    ) -> AnalysisResult:
        if not self.api_key or not self.folder_id:
            return self._fallback_or_raise(
                "Для Yandex AI нужны YANDEX_API_KEY и YANDEX_FOLDER_ID.",
                text=text,
                filename=filename,
                material_type=material_type,
                audience_type=audience_type,
            )

        try:
            client = self._build_client()
            response = client.responses.create(
                model=self.model_uri,
                instructions=self._system_prompt(),
                input=self._user_prompt(text, filename, material_type, audience_type),
                temperature=0.6,
                max_output_tokens=6000,
            )
            llm_response = self._build_llm_response(response)
            result = self.parse_analysis_json(self._extract_json(llm_response.text))
            result.filename = filename
            result.material_type = material_type
            result.audience_type = audience_type
            result.provider_name = llm_response.provider
            result.provider_model = llm_response.model
            result.provider_response_id = llm_response.response_id
            result.is_mock = llm_response.is_mock
            result.persuasiveness_score = score_from_breakdown(result.scoring_breakdown)
            return result
        except (InvalidLLMResponseError, LLMProviderError) as exc:
            return self._fallback_or_raise(
                str(exc),
                text=text,
                filename=filename,
                material_type=material_type,
                audience_type=audience_type,
            )
        except Exception as exc:
            return self._fallback_or_raise(
                f"Ошибка запроса к Yandex AI: {exc}",
                text=text,
                filename=filename,
                material_type=material_type,
                audience_type=audience_type,
            )

    def _build_client(self) -> Any:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise LLMProviderError("Пакет openai не установлен. Установите зависимости из requirements.txt.") from exc

        return OpenAI(api_key=self.api_key, base_url=self.base_url, project=self.folder_id)

    def _build_llm_response(self, response: Any) -> LLMResponse:
        return LLMResponse(
            text=self._extract_output_text(response),
            provider="yandex",
            model=self.model_uri,
            response_id=self._extract_response_id(response),
            is_mock=False,
        )

    def _extract_response_id(self, response: Any) -> str | None:
        response_id = getattr(response, "id", None)
        if response_id:
            return str(response_id)
        if hasattr(response, "model_dump"):
            data = response.model_dump()
        elif isinstance(response, dict):
            data = response
        else:
            data = {}
        response_id = data.get("id") if isinstance(data, dict) else None
        return str(response_id) if response_id else None

    def _system_prompt(self) -> str:
        return _load_prompt("system_prompt.txt")

    def _user_prompt(self, text: str, filename: str, material_type: str, audience_type: str) -> str:
        schema = json.dumps(AnalysisResult.model_json_schema(), ensure_ascii=False)
        return f"""Проанализируй материал пользователя и верни только JSON без markdown.

Файл: {filename}
Тип материала: {material_type}
Аудитория: {audience_type}

JSON должен соответствовать схеме AnalysisResult:
{schema}

Правила:
- не используй внешние источники;
- не выдумывай реальные ссылки и citations;
- не считай утверждениями номера страниц, элементы титульного листа, класс, год, ФИО, пункты содержания, список литературы, подписи приложений и заголовки разделов;
- извлекай утверждения только из основного текста, введения, практической части и заключения;
- для реферата, сочинения, доклада или исследовательской работы сначала ищи тему, цель, гипотезу, задачи, методы и вывод;
- если есть явная строка "Цель работы", используй её как цель; если есть "Гипотеза", используй её как гипотезу;
- не бери название конкурса или учреждения как главную мысль;
- если аудитория "учитель", не используй слова "инвестор", "жюри" и "бизнес-ценность"; пиши про учителя, защиту, исследовательскую работу, вывод, источники и практическую часть;
- если утверждение не подтверждается внутри материала, ставь статус needs_source или unverifiable_from_text;
- persuasiveness_score будет пересчитан приложением по scoring_breakdown, но scoring_breakdown должен быть заполнен;
- сильные стороны, слабые места, риски, утверждения, рекомендации и вопросы аудитории должны быть конкретными.

Текст материала:
\"\"\"
{text}
\"\"\"
"""

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text)

        if hasattr(response, "model_dump"):
            data = response.model_dump()
        elif isinstance(response, dict):
            data = response
        else:
            data = {}

        chunks = self._collect_text_values(data)
        if chunks:
            return "\n".join(chunks)
        raise InvalidLLMResponseError("Yandex AI не вернул текстовый JSON-ответ.")

    def _collect_text_values(self, value: Any) -> list[str]:
        if isinstance(value, dict):
            chunks: list[str] = []
            if isinstance(value.get("text"), str):
                chunks.append(value["text"])
            for child in value.values():
                chunks.extend(self._collect_text_values(child))
            return chunks
        if isinstance(value, list):
            chunks = []
            for item in value:
                chunks.extend(self._collect_text_values(item))
            return chunks
        return []

    def _extract_json(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()

        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            candidate = cleaned[start : end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError as exc:
                raise InvalidLLMResponseError("Yandex AI вернул невалидный JSON.") from exc
        raise InvalidLLMResponseError("Yandex AI ответил без JSON-объекта.")

    def _fallback_or_raise(
        self,
        message: str,
        *,
        text: str,
        filename: str,
        material_type: str,
        audience_type: str,
    ) -> AnalysisResult:
        if self.fallback_provider is None:
            raise LLMProviderError(message)
        return self.fallback_provider.analyze_material(
            text=text,
            filename=filename,
            material_type=material_type,
            audience_type=audience_type,
        )


# Backwards-compatible export for existing imports.
YandexLLMProvider = YandexAIProvider
