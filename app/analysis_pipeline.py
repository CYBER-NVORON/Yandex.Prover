from __future__ import annotations

from app.config import Settings, get_settings
from app.document_preprocessor import PreprocessedDocument, filter_noise_claims, preprocess_document
from app.llm import LLMProvider, MockLLMProvider, YandexAIProvider
from app.llm.base import LLMProviderError
from app.schemas import AnalysisResult


def build_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    if settings.llm_provider == "mock":
        return MockLLMProvider()
    if settings.llm_provider in {"yandex", "yandexgpt", "alice"}:
        return YandexAIProvider(
            api_key=settings.yandex_api_key,
            folder_id=settings.yandex_folder_id,
            model=settings.yandex_model,
            base_url=settings.yandex_base_url,
            fallback_provider=MockLLMProvider() if settings.allow_mock_fallback else None,
        )
    raise LLMProviderError(f"Неизвестный LLM_PROVIDER: {settings.llm_provider}. Используйте mock или yandex.")


def analyze_text(
    *,
    text: str,
    filename: str,
    material_type: str,
    audience_type: str,
    provider: LLMProvider | None = None,
) -> AnalysisResult:
    provider = provider or build_provider()
    preprocessed = preprocess_document(text)
    analysis_text = preprocessed.analysis_text or preprocessed.clean_text or text
    result = provider.analyze_material(
        text=analysis_text,
        filename=filename,
        material_type=material_type,
        audience_type=audience_type,
    )
    return _apply_preprocessing_context(result, preprocessed)


def _apply_preprocessing_context(
    result: AnalysisResult,
    preprocessed: PreprocessedDocument,
) -> AnalysisResult:
    result.claims = filter_noise_claims(result.claims)

    if preprocessed.references_text and not _contains_any(
        result.strengths,
        ("список литературы", "источник", "источники", "литература"),
    ):
        result.strengths.append(
            "В материале есть список литературы; его стоит связать с конкретными утверждениями в основной части."
        )

    return result


def _contains_any(items: list[str], needles: tuple[str, ...]) -> bool:
    joined = "\n".join(items).lower()
    return any(needle in joined for needle in needles)
