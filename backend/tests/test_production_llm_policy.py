from __future__ import annotations

import pytest

from app.config import Settings, validate_runtime_settings


def test_production_rejects_mock_provider():
    settings = Settings(app_env="production", llm_provider="mock", allow_mock_fallback=False)

    with pytest.raises(ValueError, match="LLM_PROVIDER=mock"):
        validate_runtime_settings(settings)


def test_production_rejects_mock_fallback():
    settings = Settings(
        app_env="production",
        llm_provider="yandex",
        allow_mock_fallback=True,
        yandex_api_key="key",
        yandex_folder_id="folder",
    )

    with pytest.raises(ValueError, match="ALLOW_MOCK_FALLBACK"):
        validate_runtime_settings(settings)


def test_production_requires_yandex_credentials():
    settings = Settings(
        app_env="production",
        llm_provider="yandex",
        allow_mock_fallback=False,
        yandex_api_key="",
        yandex_folder_id="",
    )

    with pytest.raises(ValueError, match="YANDEX_API_KEY"):
        validate_runtime_settings(settings)
