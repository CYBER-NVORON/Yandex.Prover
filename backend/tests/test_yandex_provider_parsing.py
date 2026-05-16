from types import SimpleNamespace

import pytest

from app.services.llm.base import InvalidLLMResponseError, LLMProviderError
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
            return SimpleNamespace(output_text='{"id":"analysis_test"}', id="response_1")

    responses = Responses()
    client = SimpleNamespace(responses=responses)
    provider = YandexAIProvider(api_key="key", folder_id="folder", client=client)

    with pytest.raises(LLMProviderError):
        provider.analyze_material(
            text="Текст",
            filename="sample.txt",
            material_type="реферат",
            audience_type="учитель",
        )

    assert responses.kwargs["model"] == "gpt://folder/aliceai-llm/latest"
    assert isinstance(responses.kwargs["input"], list)
    assert responses.kwargs["input"][0]["role"] == "user"
    assert responses.kwargs["max_output_tokens"] == 12000


def test_yandex_provider_accepts_custom_max_output_tokens():
    class Responses:
        def __init__(self) -> None:
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(output_text='{"id":"analysis_test"}', id="response_1")

    responses = Responses()
    client = SimpleNamespace(responses=responses)
    provider = YandexAIProvider(api_key="key", folder_id="folder", client=client, max_output_tokens=18000)

    with pytest.raises(LLMProviderError):
        provider.analyze_material(
            text="Текст",
            filename="sample.txt",
            material_type="реферат",
            audience_type="учитель",
        )

    assert responses.kwargs["max_output_tokens"] == 18000
