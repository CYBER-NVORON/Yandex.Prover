from __future__ import annotations

from app.config import Settings, get_settings
from app.services.contextual_analysis import (
    audience_knowledge_label,
    build_audience_adaptation_notes,
    build_benchmark_comparison,
    build_overthinking_guard,
    build_regulation_analysis,
    normalize_audience_knowledge_level,
)
from app.services.document_preprocessor import PreprocessedDocument, filter_noise_claims, preprocess_document
from app.services.llm import LLMProvider, MockLLMProvider, YandexAIProvider
from app.services.llm.base import LLMProviderError
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
            max_output_tokens=settings.yandex_max_output_tokens,
            fallback_provider=MockLLMProvider() if settings.allow_mock_fallback else None,
        )
    raise LLMProviderError(f"Неизвестный LLM_PROVIDER: {settings.llm_provider}. Используйте mock или yandex.")


def analyze_text(
    *,
    text: str,
    filename: str,
    material_type: str,
    audience_type: str,
    audience_knowledge_level: int = 3,
    regulation_text: str | None = None,
    regulation_filename: str | None = None,
    benchmark_text: str | None = None,
    benchmark_filename: str | None = None,
    provider: LLMProvider | None = None,
) -> AnalysisResult:
    settings = get_settings()
    provider = provider or build_provider(settings)
    audience_knowledge_level = normalize_audience_knowledge_level(audience_knowledge_level)
    preprocessed = preprocess_document(
        text,
        soft_char_limit=settings.soft_char_limit,
        hard_char_limit=settings.hard_char_limit,
    )
    analysis_text = preprocessed.analysis_text or preprocessed.clean_text or text
    result = provider.analyze_material(
        text=analysis_text,
        filename=filename,
        material_type=material_type,
        audience_type=audience_type,
        audience_knowledge_level=audience_knowledge_level,
        regulation_text=_prompt_context(regulation_text, settings.soft_char_limit),
        benchmark_text=_prompt_context(benchmark_text, settings.soft_char_limit),
        regulation_filename=regulation_filename,
        benchmark_filename=benchmark_filename,
    )
    result = _apply_preprocessing_context(result, preprocessed)
    return _apply_contextual_features(
        result,
        material_text=preprocessed.clean_text or analysis_text,
        regulation_text=regulation_text,
        regulation_filename=regulation_filename,
        benchmark_text=benchmark_text,
        benchmark_filename=benchmark_filename,
        audience_knowledge_level=audience_knowledge_level,
    )


def _apply_preprocessing_context(
    result: AnalysisResult,
    preprocessed: PreprocessedDocument,
) -> AnalysisResult:
    result.claims = filter_noise_claims(result.claims)
    existing_warnings = set(result.warnings)
    for warning in preprocessed.warnings:
        if warning not in existing_warnings:
            result.warnings.append(warning)
            existing_warnings.add(warning)

    if preprocessed.references_text and not _contains_any(
        result.strengths,
        ("список литературы", "источник", "источники", "литература"),
    ):
        result.strengths.append(
            "В материале есть список литературы; его стоит связать с конкретными утверждениями в основной части."
        )

    return result


def _apply_contextual_features(
    result: AnalysisResult,
    *,
    material_text: str,
    regulation_text: str | None,
    regulation_filename: str | None,
    benchmark_text: str | None,
    benchmark_filename: str | None,
    audience_knowledge_level: int,
) -> AnalysisResult:
    result.audience_knowledge_level = audience_knowledge_level
    result.audience_knowledge_label = audience_knowledge_label(audience_knowledge_level)
    result.audience_adaptation_notes = build_audience_adaptation_notes(audience_knowledge_level)

    if regulation_text and regulation_text.strip():
        result.regulation_analysis = build_regulation_analysis(
            material_text=material_text,
            regulation_text=regulation_text,
            regulation_filename=regulation_filename or "regulation.txt",
        )
    else:
        result.regulation_analysis = None

    if benchmark_text and benchmark_text.strip():
        result.benchmark_comparison = build_benchmark_comparison(
            material_text=material_text,
            benchmark_text=benchmark_text,
            benchmark_filename=benchmark_filename or "benchmark.txt",
        )
    else:
        result.benchmark_comparison = None

    result.overthinking_guard = build_overthinking_guard(
        result,
        result.regulation_analysis,
        result.benchmark_comparison,
        audience_knowledge_level,
    )
    return result


def _prompt_context(text: str | None, limit: int) -> str | None:
    if not text:
        return None
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip()


def _contains_any(items: list[str], needles: tuple[str, ...]) -> bool:
    joined = "\n".join(items).lower()
    return any(needle in joined for needle in needles)

