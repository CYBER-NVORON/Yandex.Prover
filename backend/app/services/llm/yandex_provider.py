from __future__ import annotations

import json
import re
from typing import Any

from app.config import DEFAULT_YANDEX_BASE_URL, DEFAULT_YANDEX_MODEL, normalize_yandex_model
from app.schemas import AnalysisResult, AudienceQuestion, LLMResponse, Recommendation, Weakness
from app.services.llm.base import InvalidLLMResponseError, LLMProvider, LLMProviderError
from app.services.llm.mock_provider import MockLLMProvider
from app.services.prompt_service import PromptService
from app.services.scoring import score_from_breakdown
from app.services.contextual_analysis import audience_knowledge_label, build_audience_adaptation_notes


YANDEX_403_MESSAGE = (
    "Алиса отклонила запрос из-за прав доступа. Проверьте YANDEX_FOLDER_ID, "
    "ключ API, роли ai.assistants.editor и ai.languageModels.user, а также активный биллинг."
)


REVIEW_SECTION_ALIASES = {
    "КРАТКОЕ РЕЗЮМЕ": "summary",
    "РЕЗЮМЕ": "summary",
    "ГЛАВНАЯ МЫСЛЬ": "main_idea",
    "СИЛЬНЫЕ СТОРОНЫ": "strengths",
    "СЛАБЫЕ МЕСТА": "weaknesses",
    "РИСКИ": "risks",
    "РЕКОМЕНДАЦИИ": "recommendations",
    "ВОПРОСЫ АУДИТОРИИ": "questions",
    "БЕЗ ЛИШНЕЙ ТРЕВОГИ": "anti_overthinking",
    "АНТИ-OVERTHINKING": "anti_overthinking",
    "ANTI-OVERTHINKING": "anti_overthinking",
}


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
        audience_knowledge_level: int = 3,
        regulation_text: str | None = None,
        benchmark_text: str | None = None,
        regulation_filename: str | None = None,
        benchmark_filename: str | None = None,
    ) -> AnalysisResult:
        if not self.api_key or not self.folder_id:
            return self._fallback_or_raise(
                "Для Алисы нужны YANDEX_API_KEY и YANDEX_FOLDER_ID.",
                text=text,
                filename=filename,
                material_type=material_type,
                audience_type=audience_type,
                audience_knowledge_level=audience_knowledge_level,
                regulation_text=regulation_text,
                benchmark_text=benchmark_text,
                regulation_filename=regulation_filename,
                benchmark_filename=benchmark_filename,
            )

        try:
            response = self._build_client().responses.create(
                model=self.model_uri,
                instructions=self.prompt_service.system_prompt(),
                input=[
                    {
                        "role": "user",
                        "content": self.prompt_service.build_review_prompt(
                            text=text,
                            filename=filename,
                            material_type=material_type,
                            audience_type=audience_type,
                            audience_knowledge_level=audience_knowledge_level,
                            regulation_text=regulation_text,
                            benchmark_text=benchmark_text,
                            regulation_filename=regulation_filename,
                            benchmark_filename=benchmark_filename,
                        ),
                    }
                ],
                temperature=0.3,
                max_output_tokens=self.max_output_tokens,
            )
            llm_response = self._build_llm_response(response)
            result = self._build_backend_result(
                text=text,
                filename=filename,
                material_type=material_type,
                audience_type=audience_type,
                audience_knowledge_level=audience_knowledge_level,
                regulation_text=regulation_text,
                benchmark_text=benchmark_text,
                regulation_filename=regulation_filename,
                benchmark_filename=benchmark_filename,
            )
            result = self._apply_plain_review(result, llm_response.text, audience_type)
            result.filename = filename
            result.material_type = material_type
            result.audience_type = audience_type
            result.audience_knowledge_level = audience_knowledge_level
            result.audience_knowledge_label = audience_knowledge_label(audience_knowledge_level)
            result.audience_adaptation_notes = build_audience_adaptation_notes(audience_knowledge_level)
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
                audience_knowledge_level=audience_knowledge_level,
                regulation_text=regulation_text,
                benchmark_text=benchmark_text,
                regulation_filename=regulation_filename,
                benchmark_filename=benchmark_filename,
            )
        except Exception as exc:
            message = self._friendly_api_error(exc)
            return self._fallback_or_raise(
                message,
                text=text,
                filename=filename,
                material_type=material_type,
                audience_type=audience_type,
                audience_knowledge_level=audience_knowledge_level,
                regulation_text=regulation_text,
                benchmark_text=benchmark_text,
                regulation_filename=regulation_filename,
                benchmark_filename=benchmark_filename,
            )

    def _build_backend_result(
        self,
        *,
        text: str,
        filename: str,
        material_type: str,
        audience_type: str,
        audience_knowledge_level: int,
        regulation_text: str | None,
        benchmark_text: str | None,
        regulation_filename: str | None,
        benchmark_filename: str | None,
    ) -> AnalysisResult:
        return MockLLMProvider().analyze_material(
            text=text,
            filename=filename,
            material_type=material_type,
            audience_type=audience_type,
            audience_knowledge_level=audience_knowledge_level,
            regulation_text=regulation_text,
            benchmark_text=benchmark_text,
            regulation_filename=regulation_filename,
            benchmark_filename=benchmark_filename,
        )

    def _apply_plain_review(self, result: AnalysisResult, review_text: str, audience_type: str) -> AnalysisResult:
        sections = self._parse_review_sections(review_text)
        summary = self._compact_text(sections.get("summary", ""), limit=650)
        main_idea = self._compact_text(sections.get("main_idea", ""), limit=500)

        if summary:
            result.summary = summary
        if main_idea:
            result.main_idea = main_idea
            result.structure_analysis.main_idea = main_idea

        strengths = self._section_items(sections.get("strengths", ""), limit=5)
        if strengths:
            result.strengths = self._merge_unique(strengths, result.strengths, limit=6)

        risks = self._section_items(sections.get("risks", ""), limit=5)
        if risks:
            result.risks = self._merge_unique(risks, result.risks, limit=6)

        weakness_items = self._section_items(sections.get("weaknesses", ""), limit=3)
        if weakness_items:
            yandex_weaknesses = [
                Weakness(
                    problem=item,
                    why_problem="Алиса отметила это как слабое место для предзащиты.",
                    audience_signal="Аудитория может попросить пояснить этот фрагмент.",
                    fix="Сделать точечную правку: уточнить формулировку, доказательство или связь с выводом.",
                )
                for item in weakness_items
            ]
            result.weaknesses = self._merge_weaknesses(yandex_weaknesses, result.weaknesses, limit=6)

        self._apply_review_recommendations(result, sections.get("recommendations", ""))
        self._apply_review_questions(result, sections.get("questions", ""), audience_type)
        return result

    def _parse_review_sections(self, text: str) -> dict[str, str]:
        sections: dict[str, list[str]] = {}
        current: str | None = None

        for raw_line in text.splitlines():
            key = self._review_heading_key(raw_line)
            if key:
                current = key
                sections.setdefault(current, [])
                continue
            if current:
                sections[current].append(raw_line.rstrip())

        return {key: "\n".join(lines).strip() for key, lines in sections.items()}

    def _review_heading_key(self, line: str) -> str | None:
        normalized = line.strip()
        normalized = re.sub(r"^[#>\s*-]+", "", normalized)
        normalized = re.sub(r"^\d+[\).\s-]+", "", normalized)
        normalized = normalized.rstrip(":：").strip().upper().replace("Ё", "Е")
        normalized = re.sub(r"\s+", " ", normalized)
        return REVIEW_SECTION_ALIASES.get(normalized)

    def _compact_text(self, text: str, *, limit: int) -> str:
        cleaned = re.sub(r"^\s*[-*•]\s*", "", text.strip())
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -•")
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[:limit].rsplit(" ", 1)[0].rstrip(" .,;:") + "."

    def _section_items(self, text: str, *, limit: int) -> list[str]:
        items: list[str] = []
        for line in text.splitlines():
            item = self._clean_list_item(line)
            if item:
                items.append(item)

        if not items:
            for chunk in re.split(r"(?<=[.!?])\s+", text.strip()):
                item = self._clean_list_item(chunk)
                if item:
                    items.append(item)

        return self._dedupe_strings(items, limit=limit)

    def _clean_list_item(self, value: str) -> str:
        item = value.strip()
        if not item:
            return ""
        item = re.sub(r"^\s*(?:[-*•]+|\d+[\).\:]|[a-zа-яё]\))\s*", "", item, flags=re.IGNORECASE)
        item = re.sub(r"^(?:critical|important|optional|критично|важно|желательно)\s*[:.-]\s*", "", item, flags=re.IGNORECASE)
        item = re.sub(r"\s+", " ", item).strip()
        if len(item) < 8:
            return ""
        return item[:420].rstrip()

    def _apply_review_recommendations(self, result: AnalysisResult, text: str) -> None:
        items = self._section_items(text, limit=4)
        if not items:
            return

        additions = [
            Recommendation(
                id=f"rec_yandex_{index}",
                priority=self._priority_from_text(item),
                category="Рецензия Алисы",
                problem="Алиса отметила точечную доработку по содержанию.",
                action=self._remove_priority_prefix(item),
                expected_effect="Усилит предзащиту без переписывания материала целиком.",
            )
            for index, item in enumerate(items, start=1)
        ]

        existing_high = [item for item in result.recommendations if item.priority == "high"]
        existing_other = [item for item in result.recommendations if item.priority != "high"]
        result.recommendations = self._merge_recommendations(existing_high + additions, existing_other, limit=8)

    def _apply_review_questions(self, result: AnalysisResult, text: str, audience_type: str) -> None:
        items = self._section_items(text, limit=4)
        if not items:
            return

        additions = []
        for index, item in enumerate(items, start=1):
            question = item if item.endswith("?") else f"{item.rstrip('.')}?"
            additions.append(
                AudienceQuestion(
                    id=f"question_yandex_{index}",
                    question=question,
                    asked_by=audience_type,
                    category="Вся работа: вопрос аудитории",
                    why_asked="Алиса отметила это как вероятный вопрос на предзащите.",
                    risk_level=self._priority_from_text(item),
                    suggested_answer="Ответ стоит подготовить на основе уже загруженного материала, не добавляя неподтверждённые факты.",
                    how_to_improve_material="Добавить в материал короткое пояснение или доказательство, если вопрос вскрывает пробел.",
                )
            )

        result.audience_questions = self._merge_questions(additions, result.audience_questions, limit=10)

    def _priority_from_text(self, value: str) -> str:
        lowered = value.lower()
        if "critical" in lowered or "критич" in lowered:
            return "high"
        if "optional" in lowered or "желательно" in lowered or "можно" in lowered:
            return "low"
        return "medium"

    def _remove_priority_prefix(self, value: str) -> str:
        return re.sub(
            r"^(?:critical|important|optional|критично|важно|желательно)\s*[:.-]\s*",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()

    def _merge_unique(self, preferred: list[str], existing: list[str], *, limit: int) -> list[str]:
        return self._dedupe_strings(preferred + existing, limit=limit)

    def _dedupe_strings(self, items: list[str], *, limit: int) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in items:
            normalized = re.sub(r"\s+", " ", item).strip()
            key = normalized.lower()
            if normalized and key not in seen:
                result.append(normalized)
                seen.add(key)
            if len(result) >= limit:
                break
        return result

    def _merge_weaknesses(self, preferred: list[Weakness], existing: list[Weakness], *, limit: int) -> list[Weakness]:
        result: list[Weakness] = []
        seen: set[str] = set()
        for item in preferred + existing:
            key = item.problem.lower().strip()
            if key and key not in seen:
                result.append(item)
                seen.add(key)
            if len(result) >= limit:
                break
        return result

    def _merge_recommendations(
        self,
        preferred: list[Recommendation],
        existing: list[Recommendation],
        *,
        limit: int,
    ) -> list[Recommendation]:
        result: list[Recommendation] = []
        seen: set[str] = set()
        for item in preferred + existing:
            key = item.action.lower().strip()
            if key and key not in seen:
                result.append(item)
                seen.add(key)
            if len(result) >= limit:
                break
        return result

    def _merge_questions(
        self,
        preferred: list[AudienceQuestion],
        existing: list[AudienceQuestion],
        *,
        limit: int,
    ) -> list[AudienceQuestion]:
        result: list[AudienceQuestion] = []
        seen: set[str] = set()
        for item in preferred + existing:
            key = item.question.lower().strip()
            if key and key not in seen:
                result.append(item)
                seen.add(key)
            if len(result) >= limit:
                break
        return result

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
            return "Алиса отклонила запрос: неверный или недействительный YANDEX_API_KEY."
        if status_code == 403:
            return YANDEX_403_MESSAGE

        raw = str(exc)
        if "401" in raw:
            return "Алиса отклонила запрос: неверный или недействительный YANDEX_API_KEY."
        if "403" in raw or "permission" in raw.lower() or "forbidden" in raw.lower():
            return YANDEX_403_MESSAGE
        return f"Ошибка запроса к Алисе: {raw}"

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
        raise InvalidLLMResponseError("Алиса не вернула текстовый ответ.")

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
                        "Алиса не успела вернуть полный JSON: ответ был обрезан. "
                        "Попробуйте повторить анализ или увеличьте YANDEX_MAX_OUTPUT_TOKENS. "
                        f"Начало ответа: {snippet}"
                    ) from exc
                raise InvalidLLMResponseError(f"Алиса вернула невалидный JSON. Начало ответа: {snippet}") from exc

        snippet = cleaned[:500].replace("\n", " ")
        if cleaned.startswith("{"):
            raise InvalidLLMResponseError(
                "Алиса не успела вернуть полный JSON: ответ был обрезан. "
                "Попробуйте повторить анализ или увеличьте YANDEX_MAX_OUTPUT_TOKENS. "
                f"Начало ответа: {snippet}"
            )
        raise InvalidLLMResponseError(f"Алиса ответила без JSON-объекта. Начало ответа: {snippet}")

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
        audience_knowledge_level: int = 3,
        regulation_text: str | None = None,
        benchmark_text: str | None = None,
        regulation_filename: str | None = None,
        benchmark_filename: str | None = None,
    ) -> AnalysisResult:
        if self.fallback_provider is None:
            raise LLMProviderError(message)
        return self.fallback_provider.analyze_material(
            text=text,
            filename=filename,
            material_type=material_type,
            audience_type=audience_type,
            audience_knowledge_level=audience_knowledge_level,
            regulation_text=regulation_text,
            benchmark_text=benchmark_text,
            regulation_filename=regulation_filename,
            benchmark_filename=benchmark_filename,
        )


YandexLLMProvider = YandexAIProvider
