from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings  # noqa: E402


def extract_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)

    if hasattr(response, "model_dump"):
        data = response.model_dump()
    elif isinstance(response, dict):
        data = response
    else:
        data = {}

    chunks = collect_text_values(data)
    return "\n".join(chunks).strip()


def collect_text_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        chunks: list[str] = []
        if isinstance(value.get("text"), str):
            chunks.append(value["text"])
        for child in value.values():
            chunks.extend(collect_text_values(child))
        return chunks
    if isinstance(value, list):
        chunks: list[str] = []
        for item in value:
            chunks.extend(collect_text_values(item))
        return chunks
    return []


def main() -> int:
    settings = get_settings()
    if not settings.yandex_api_key or not settings.yandex_folder_id:
        print("YANDEX_API_KEY and YANDEX_FOLDER_ID are required.", file=sys.stderr)
        return 1

    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        print("Package openai is not installed. Install requirements.txt.", file=sys.stderr)
        return 1

    model = f"gpt://{settings.yandex_folder_id}/{settings.yandex_model}"
    client = OpenAI(
        api_key=settings.yandex_api_key,
        base_url=settings.yandex_base_url,
        project=settings.yandex_folder_id,
    )

    try:
        response = client.responses.create(
            model=model,
            instructions="",
            input="Ответь одним коротким предложением: проверка связи с Yandex AI.",
            temperature=0,
            max_output_tokens=120,
        )
    except Exception as exc:
        print(f"Yandex AI request failed: {exc}", file=sys.stderr)
        return 1

    print(f"provider: yandex")
    print(f"model: {model}")
    print(f"response_id: {getattr(response, 'id', None) or '-'}")
    print("text:")
    print(extract_text(response) or "<empty>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
