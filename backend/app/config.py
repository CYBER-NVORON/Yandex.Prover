from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_YANDEX_BASE_URL = "https://rest-assistant.api.cloud.yandex.net/v1"
DEFAULT_YANDEX_MODEL = "aliceai-llm/latest"

SOFT_CHAR_LIMIT = 50_000
HARD_CHAR_LIMIT = 120_000
MAX_CHARS_FOR_ANALYSIS = HARD_CHAR_LIMIT
PRODUCTION_ENVS = {"production", "prod"}


def normalize_yandex_model(model: str) -> str:
    model = model.strip()
    if not model:
        return DEFAULT_YANDEX_MODEL
    if model == "aliceai-llm":
        return DEFAULT_YANDEX_MODEL
    return model


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    database_url: str = "postgresql+psycopg://dokazatel:dokazatel@postgres:5432/dokazatel"

    llm_provider: str = "yandex"
    allow_mock_fallback: bool = False

    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = DEFAULT_YANDEX_MODEL
    yandex_base_url: str = DEFAULT_YANDEX_BASE_URL
    yandex_max_output_tokens: int = Field(default=12_000, ge=1)

    max_chars_for_analysis: int = Field(default=MAX_CHARS_FOR_ANALYSIS, ge=1)
    soft_char_limit: int = Field(default=SOFT_CHAR_LIMIT, ge=1)
    hard_char_limit: int = Field(default=HARD_CHAR_LIMIT, ge=1)

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def yandex_model_uri(self) -> str:
        model = normalize_yandex_model(self.yandex_model)
        return f"gpt://{self.yandex_folder_id}/{model}" if self.yandex_folder_id else ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.app_env = settings.app_env.strip().lower() or "development"
    settings.llm_provider = settings.llm_provider.strip().lower() or "yandex"
    settings.yandex_model = normalize_yandex_model(settings.yandex_model)
    settings.yandex_base_url = settings.yandex_base_url.strip() or DEFAULT_YANDEX_BASE_URL
    if settings.hard_char_limit > settings.max_chars_for_analysis:
        settings.hard_char_limit = settings.max_chars_for_analysis
    validate_runtime_settings(settings)
    return settings


def validate_runtime_settings(settings: Settings) -> None:
    if settings.app_env not in PRODUCTION_ENVS:
        return
    if settings.llm_provider == "mock":
        raise ValueError("LLM_PROVIDER=mock запрещён в production. Используйте LLM_PROVIDER=yandex.")
    if settings.allow_mock_fallback:
        raise ValueError("ALLOW_MOCK_FALLBACK=true запрещён в production.")
    if settings.llm_provider in {"yandex", "yandexgpt", "alice"} and (
        not settings.yandex_api_key or not settings.yandex_folder_id
    ):
        raise ValueError("Для production нужны YANDEX_API_KEY и YANDEX_FOLDER_ID.")
