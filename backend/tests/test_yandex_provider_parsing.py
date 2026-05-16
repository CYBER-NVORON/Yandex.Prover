import json
from types import SimpleNamespace

import pytest

from app.services.llm.base import InvalidLLMResponseError
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.yandex_provider import YandexAIProvider


def test_yandex_provider_extracts_json_from_markdown_fence():
    provider = YandexAIProvider(api_key="key", folder_id="folder")

    payload = provider._extract_json('```json\n{"ok": true}\n```')

    assert payload == '{"ok": true}'


def test_yandex_provider_extracts_json_with_surrounding_text():
    provider = YandexAIProvider(api_key="key", folder_id="folder")

    payload = provider._extract_json('Ответ:\n{"ok": true}\nСпасибо')

    assert payload == '{"ok": true}'


def test_yandex_provider_raises_with_response_snippet_for_invalid_json():
    provider = YandexAIProvider(api_key="key", folder_id="folder")

    with pytest.raises(InvalidLLMResponseError) as exc:
        provider._extract_json("модель вернула текст без json")

    assert "Начало ответа" in str(exc.value)


def test_yandex_provider_reports_truncated_json():
    provider = YandexAIProvider(api_key="key", folder_id="folder")

    with pytest.raises(InvalidLLMResponseError) as exc:
        provider._extract_json('{"id": "analysis_1", "claims": [{"text": "обрезано"}')

    assert "ответ был обрезан" in str(exc.value)


def test_yandex_provider_uses_responses_api_input_shape():
    class Responses:
        def __init__(self) -> None:
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(
                output_text=(
                    "КРАТКОЕ РЕЗЮМЕ\n"
                    "Материал понятен, но требует усилить доказательства.\n\n"
                    "ГЛАВНАЯ МЫСЛЬ\n"
                    "Автор проверяет готовность материала к вопросам аудитории.\n\n"
                    "РЕКОМЕНДАЦИИ\n"
                    "- critical: Уточнить главный вывод."
                ),
                id="response_1",
            )

    responses = Responses()
    client = SimpleNamespace(responses=responses)
    provider = YandexAIProvider(api_key="key", folder_id="folder", client=client)

    result = provider.analyze_material(
        text="Цель: проверить работу. Вывод: материал нужно защищать доказательно.",
        filename="sample.txt",
        material_type="реферат",
        audience_type="учитель",
    )

    assert responses.kwargs["model"] == "gpt://folder/aliceai-llm/latest"
    assert isinstance(responses.kwargs["input"], list)
    assert responses.kwargs["input"][0]["role"] == "user"
    assert responses.kwargs["max_output_tokens"] == 12000
    assert "не json" in responses.kwargs["input"][0]["content"].lower()
    assert result.provider_name == "yandex"
    assert result.provider_response_id == "response_1"
    assert result.is_mock is False
    assert result.summary.startswith("Материал понятен")
    assert result.main_idea.startswith("Автор проверяет")


def test_yandex_provider_accepts_custom_max_output_tokens():
    class Responses:
        def __init__(self) -> None:
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(output_text="КРАТКОЕ РЕЗЮМЕ\nРазбор получен обычным текстом.", id="response_1")

    responses = Responses()
    client = SimpleNamespace(responses=responses)
    provider = YandexAIProvider(api_key="key", folder_id="folder", client=client, max_output_tokens=18000)

    result = provider.analyze_material(
        text="Цель: проверить работу. Вывод: материал нужно защищать доказательно.",
        filename="sample.txt",
        material_type="реферат",
        audience_type="учитель",
    )

    assert responses.kwargs["max_output_tokens"] == 18000
    assert result.provider_name == "yandex"


def test_yandex_provider_accepts_plain_review_and_ignores_json_artifacts():
    class Responses:
        def create(self, **kwargs):
            return SimpleNamespace(
                output_text=(
                    "Перед секциями может быть лишний текст.\n"
                    "КРАТКОЕ РЕЗЮМЕ\n"
                    "Alice даёт смысловой разбор, а backend собирает строгий DTO.\n\n"
                    "РИСКИ\n"
                    "- Не хватает доказательства главного тезиса.\n\n"
                    "ВОПРОСЫ АУДИТОРИИ\n"
                    "- Почему вывод следует из аргументов\n\n"
                    "{\"artifact\": true}"
                ),
                id="response_2",
            )

    provider = YandexAIProvider(api_key="key", folder_id="folder", client=SimpleNamespace(responses=Responses()))

    result = provider.analyze_material(
        text="Цель: проверить работу. Вывод: материал нужно защищать доказательно.",
        filename="sample.txt",
        material_type="доклад",
        audience_type="жюри",
    )

    assert result.summary == "Alice даёт смысловой разбор, а backend собирает строгий DTO."
    assert any("Не хватает доказательства" in risk for risk in result.risks)
    assert any(question.question.startswith("Почему вывод") for question in result.audience_questions)
    assert result.provider_name == "yandex"
    assert result.is_mock is False


def test_provider_parser_ignores_backend_built_sections_and_normalizes_priorities():
    result = MockLLMProvider().analyze_material(
        text="Цель: проверить работу. Вывод: материал нужно защищать доказательно.",
        filename="sample.txt",
        material_type="доклад",
        audience_type="жюри",
    )
    payload = result.model_dump(mode="json")
    payload["extra_field_from_llm"] = "ignore"
    payload["recommendations"][0]["priority"] = "critical"
    payload["overthinking_guard"] = {
        "readiness_verdict": "ready",
        "confidence_level": "high",
        "next_best_three_actions": ["one", "two", "three", "four"],
    }
    payload["regulation_analysis"] = {"summary": "too short"}
    payload["benchmark_comparison"] = {"summary": "too short"}

    parsed = YandexAIProvider(api_key="key", folder_id="folder").parse_analysis_json(json.dumps(payload))

    assert parsed.recommendations[0].priority == "high"
    assert parsed.regulation_analysis is None
    assert parsed.benchmark_comparison is None
    assert len(parsed.overthinking_guard.next_best_three_actions) == 3
