from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


MAX_CHARS_FOR_ANALYSIS = 50_000
DEFAULT_YANDEX_BASE_URL = "https://ai.api.cloud.yandex.net/v1"
DEFAULT_YANDEX_MODEL = "aliceai-llm/latest"


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    yandex_api_key: str
    yandex_folder_id: str
    yandex_model: str
    yandex_model_uri: str
    yandex_base_url: str
    allow_mock_fallback: bool
    database_path: Path
    max_chars_for_analysis: int = MAX_CHARS_FOR_ANALYSIS


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_yandex_model(model: str) -> str:
    model = model.strip()
    if not model:
        return DEFAULT_YANDEX_MODEL
    if model == "aliceai-llm":
        return DEFAULT_YANDEX_MODEL
    return model


def get_settings() -> Settings:
    load_dotenv()
    yandex_folder_id = os.getenv("YANDEX_FOLDER_ID", "").strip()
    yandex_model = normalize_yandex_model(os.getenv("YANDEX_MODEL", DEFAULT_YANDEX_MODEL))
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "mock").strip().lower() or "mock",
        yandex_api_key=os.getenv("YANDEX_API_KEY", "").strip(),
        yandex_folder_id=yandex_folder_id,
        yandex_model=yandex_model,
        yandex_model_uri=f"gpt://{yandex_folder_id}/{yandex_model}" if yandex_folder_id else "",
        yandex_base_url=os.getenv("YANDEX_BASE_URL", DEFAULT_YANDEX_BASE_URL).strip() or DEFAULT_YANDEX_BASE_URL,
        allow_mock_fallback=_env_bool("ALLOW_MOCK_FALLBACK", False),
        database_path=Path(os.getenv("DATABASE_PATH", "./data/dokazatel.sqlite")),
    )
