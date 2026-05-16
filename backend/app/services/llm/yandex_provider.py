from __future__ import annotations

import json
import re
from typing import Any

from app.config import DEFAULT_YANDEX_BASE_URL, DEFAULT_YANDEX_MODEL, normalize_yandex_model
from app.schemas import AnalysisResult, LLMResponse
from app.services.llm.base import InvalidLLMResponseError, LLMProvider, LLMProviderError
from app.services.prompt_service import PromptService
from app.services.scoring import score_from_breakdown


YANDEX_403_MESSAGE = (
    "Yandex AI отклонил запрос из-за прав доступа. Проверьте YANDEX_FOLDER_ID, "
    "API key, роли ai.assistants.editor и ai.languageModels.user, а также активный биллинг."
)


class YandexAIProvider(LLMProvider):
    """Yandex/Alice AI provider through the OpenAI-compatible Responses API."""

    def __init__(
        self,
        *,
        api_key: str,
        folder_id: str,
        model: str = DEFAULT_YANDEX_MODEL,
        base_url: str = DEFAULT_YANDEX_BASE_URL,
        fallback_provider: LLMProvider | None = None,
        client: Any | None = None,
        prompt_service: PromptService | None = None,
        max_output_tokens: int = 12_000,
    ) -> None:
        self.api_key = api_key
        self.folder_id = folder_id
        self.model = normalize_yandex_model(model)
        self.model_uri = f"gpt://{folder_id}/{self.model}" if folder_id else ""
        self.base_url = base_url or DEFAULT_YANDEX_BASE_URL
        self.fallback_provider = fallback_provider
        self._client = client
        self.prompt_service = prompt_service or PromptService()
        self.max_output_tokens = max_output_tokens

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
            response = self._build_client().responses.create(
                model=self.model_uri,
                instructions=self.prompt_service.system_prompt(),
                input=[
                    {
                        "role": "user",
                        "content": self.prompt_service.build_user_prompt(
                            text=text,
                            filename=filename,
                            material_type=material_type,
                            audience_type=audience_type,
                        ),
                    }
                ],
                temperature=0.3,
                max_output_tokens=self.max_output_tokens,
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
            message = self._friendly_api_error(exc)
            return self._fallback_or_raise(
                message,
                text=text,
                filename=filename,
                material_type=material_type,
                audience_type=audience_type,
            )

    def _build_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise LLMProviderError("Пакет openai не установлен. Установите зависимости backend/requirements.txt.") from exc

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, project=self.folder_id)
        return self._client

    def _friendly_api_error(self, exc: Exception) -> str:
        status_code = getattr(exc, "status_code", None)
        if status_code == 401:
            return "Yandex AI отклонил запрос: неверный или недействительный YANDEX_API_KEY."
        if status_code == 403:
            return YANDEX_403_MESSAGE

        raw = str(exc)
        if "401" in raw:
            return "Yandex AI отклонил запрос: неверный или недействительный YANDEX_API_KEY."
        if "403" in raw or "permission" in raw.lower() or "forbidden" in raw.lower():
            return YANDEX_403_MESSAGE
        return f"Ошибка запроса к Yandex AI: {raw}"

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
        data = self._dump_response(response)
        response_id = data.get("id") if isinstance(data, dict) else None
        return str(response_id) if response_id else None

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text)

        data = self._dump_response(response)
        chunks = self._collect_text_values(data)
        if chunks:
            return "\n".join(chunks)
        raise InvalidLLMResponseError("Yandex AI не вернул текстовый JSON-ответ.")

    def _dump_response(self, response: Any) -> dict[str, Any]:
        if hasattr(response, "model_dump"):
            dumped = response.model_dump()
            return dumped if isinstance(dumped, dict) else {}
        return response if isinstance(response, dict) else {}

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
                snippet = cleaned[:500].replace("\n", " ")
                if self._looks_like_truncated_json(cleaned):
                    raise InvalidLLMResponseError(
                        "Yandex AI не успел вернуть полный JSON: ответ был обрезан. "
                        "Попробуйте повторить анализ или увеличьте YANDEX_MAX_OUTPUT_TOKENS. "
                        f"Начало ответа: {snippet}"
                    ) from exc
                raise InvalidLLMResponseError(f"Yandex AI вернул невалидный JSON. Начало ответа: {snippet}") from exc

        snippet = cleaned[:500].replace("\n", " ")
        if cleaned.startswith("{"):
            raise InvalidLLMResponseError(
                "Yandex AI не успел вернуть полный JSON: ответ был обрезан. "
                "Попробуйте повторить анализ или увеличьте YANDEX_MAX_OUTPUT_TOKENS. "
                f"Начало ответа: {snippet}"
            )
        raise InvalidLLMResponseError(f"Yandex AI ответил без JSON-объекта. Начало ответа: {snippet}")

    def _looks_like_truncated_json(self, text: str) -> bool:
        stripped = text.rstrip()
        if stripped.startswith("{") and not stripped.endswith("}"):
            return True
        return stripped.count("{") > stripped.count("}")

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


YandexLLMProvider = YandexAIProvider
