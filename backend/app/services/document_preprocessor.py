from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, TypeVar

from app.config import HARD_CHAR_LIMIT, SOFT_CHAR_LIMIT


SECTION_KEYS = (
    "title_page",
    "table_of_contents",
    "introduction",
    "goal",
    "hypothesis",
    "tasks",
    "methods",
    "main_body",
    "survey",
    "results",
    "conclusion",
    "references",
    "appendices",
)

ANALYSIS_SECTION_KEYS = {
    "introduction",
    "goal",
    "hypothesis",
    "tasks",
    "methods",
    "main_body",
    "survey",
    "results",
    "conclusion",
}

SECTION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("table_of_contents", (r"содержание", r"оглавление")),
    ("introduction", (r"введение", r"актуальность(?:\s+темы|\s+работы)?")),
    ("goal", (r"цель(?:\s+(?:работы|исследования|проекта))?",)),
    ("hypothesis", (r"гипотеза(?:\s+(?:работы|исследования))?",)),
    ("tasks", (r"задачи(?:\s+(?:работы|исследования|проекта))?",)),
    ("methods", (r"методы(?:\s+(?:работы|исследования))?", r"методика(?:\s+исследования)?")),
    ("survey", (r"анкетирование", r"опрос(?:\s+респондентов)?")),
    ("results", (r"результаты(?:\s+(?:работы|исследования|опроса|анкетирования))?", r"практическая\s+часть")),
    ("conclusion", (r"заключение", r"выводы?", r"итоги")),
    (
        "references",
        (
            r"литература",
            r"список\s+(?:использованной\s+)?литературы",
            r"список\s+(?:использованных\s+)?источников",
            r"использованные\s+источники",
            r"источники",
        ),
    ),
    ("appendices", (r"приложени[ея]",)),
)

METADATA_KEYWORDS = (
    "министерство",
    "департамент",
    "управление образования",
    "муниципальное",
    "образовательное учреждение",
    "общеобразовательная",
    "школа",
    "сош",
    "мбоу",
    "маоу",
    "моу",
    "гимназия",
    "лицей",
    "университет",
    "институт",
    "колледж",
    "учитель",
    "руководитель",
    "преподаватель",
    "выполнил",
    "выполнила",
    "подготовил",
    "подготовила",
    "автор работы",
    "научный руководитель",
    "квалификационная категория",
)

GENERIC_TITLE_PAGE_LINES = (
    "исследовательская работа",
    "проектная работа",
    "учебно-исследовательская работа",
    "реферат",
    "доклад",
    "конкурс",
    "номинация",
)

T = TypeVar("T")


@dataclass(frozen=True)
class PreprocessedDocument:
    title: str | None
    clean_text: str
    analysis_text: str
    metadata_text: str
    toc_text: str
    references_text: str
    appendices_text: str
    sections: dict[str, str]
    original_analysis_chars: int = 0
    analysis_chars: int = 0
    smart_context_used: bool = False
    analysis_was_truncated: bool = False
    warnings: list[str] = field(default_factory=list)


def preprocess_document(
    raw_text: str,
    *,
    soft_char_limit: int = SOFT_CHAR_LIMIT,
    hard_char_limit: int = HARD_CHAR_LIMIT,
) -> PreprocessedDocument:
    """Prepare extracted document text for idea stress-testing.

    The preprocessor is intentionally conservative: it does not fetch external
    data and does not invent missing context. It only separates document
    furniture from the text that can contain claims.
    """

    lines = _normalized_lines(raw_text)
    sections: dict[str, list[str]] = {key: [] for key in SECTION_KEYS}
    metadata_lines: list[str] = []
    toc_lines: list[str] = []
    references_lines: list[str] = []
    appendices_lines: list[str] = []
    clean_lines: list[str] = []
    analysis_lines: list[str] = []
    warnings: list[str] = []

    title_page_end = _detect_title_page_end(lines)
    current_section = "main_body"

    for index, line in enumerate(lines):
        if index < title_page_end:
            sections["title_page"].append(line)
            metadata_lines.append(line)
            continue

        if current_section == "table_of_contents" and _looks_like_toc_line(line):
            sections["table_of_contents"].append(line)
            toc_lines.append(line)
            continue

        detected = _detect_section_header(line)
        if detected is not None:
            section_key, _inline_content = detected
            current_section = section_key

            if section_key == "table_of_contents":
                sections[section_key].append(line)
                toc_lines.append(line)
                continue
            if section_key == "references":
                sections[section_key].append(line)
                references_lines.append(line)
                clean_lines.append(line)
                continue
            if section_key == "appendices":
                sections[section_key].append(line)
                appendices_lines.append(line)
                clean_lines.append(line)
                continue

            _append_analysis_line(
                line,
                section_key=section_key,
                sections=sections,
                clean_lines=clean_lines,
                analysis_lines=analysis_lines,
            )
            continue

        if current_section == "table_of_contents" or _looks_like_toc_line(line):
            sections["table_of_contents"].append(line)
            toc_lines.append(line)
            continue

        if current_section == "references":
            sections["references"].append(line)
            references_lines.append(line)
            clean_lines.append(line)
            continue

        if current_section == "appendices":
            sections["appendices"].append(line)
            appendices_lines.append(line)
            clean_lines.append(line)
            continue

        if _is_metadata_line(line) or is_noise_claim(line):
            metadata_lines.append(line)
            continue

        if _looks_like_numbered_heading(line):
            sections["main_body"].append(line)
            continue

        section_key = current_section if current_section in ANALYSIS_SECTION_KEYS else "main_body"
        _append_analysis_line(
            line,
            section_key=section_key,
            sections=sections,
            clean_lines=clean_lines,
            analysis_lines=analysis_lines,
        )

    title = _detect_title(sections["title_page"], lines)
    clean_text = _join_lines(clean_lines)
    full_analysis_text = _join_lines(analysis_lines)
    section_texts = {key: _join_lines(value) for key, value in sections.items() if value}
    context = build_smart_analysis_context(
        section_texts,
        full_analysis_text,
        soft_char_limit=soft_char_limit,
        hard_char_limit=hard_char_limit,
    )
    analysis_text = context.text

    if not analysis_text:
        warnings.append("Не удалось выделить основной текст для анализа.")
    if context.smart_context_used:
        warnings.append("Документ большой, анализ выполнен по ключевым секциям.")
    if context.was_truncated:
        warnings.append("Контекст анализа сокращён до безопасного лимита.")
    if title_page_end > 0:
        warnings.append("Титульный лист исключён из анализа claims.")
    if toc_lines:
        warnings.append("Содержание исключено из анализа claims.")
    if references_lines:
        warnings.append("Список литературы сохранён отдельно и исключён из claims.")
    if appendices_lines:
        warnings.append("Приложения сохранены отдельно и исключены из claims.")

    return PreprocessedDocument(
        title=title,
        clean_text=clean_text,
        analysis_text=analysis_text,
        metadata_text=_join_lines(metadata_lines),
        toc_text=_join_lines(toc_lines),
        references_text=_join_lines(references_lines),
        appendices_text=_join_lines(appendices_lines),
        sections=section_texts,
        original_analysis_chars=len(full_analysis_text),
        analysis_chars=len(analysis_text),
        smart_context_used=context.smart_context_used,
        analysis_was_truncated=context.was_truncated,
        warnings=warnings,
    )


@dataclass(frozen=True)
class SmartAnalysisContext:
    text: str
    smart_context_used: bool
    was_truncated: bool


def build_smart_analysis_context(
    sections: dict[str, str],
    full_analysis_text: str,
    *,
    soft_char_limit: int = SOFT_CHAR_LIMIT,
    hard_char_limit: int = HARD_CHAR_LIMIT,
) -> SmartAnalysisContext:
    """Build bounded LLM context while preserving high-value sections.

    Small documents are passed through after preprocessing. Large documents are
    represented by sections that matter most for an audience stress-test:
    goal, hypothesis, tasks, methods, introduction, conclusion, survey/results,
    and then as much main body as fits.
    """

    hard_char_limit = max(1, hard_char_limit)
    soft_char_limit = min(max(1, soft_char_limit), hard_char_limit)

    if len(full_analysis_text) <= soft_char_limit:
        text = full_analysis_text[:hard_char_limit]
        return SmartAnalysisContext(
            text=text,
            smart_context_used=False,
            was_truncated=len(full_analysis_text) > hard_char_limit,
        )

    priority_groups: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "goal_hypothesis_tasks_methods",
            [
                ("Цель", sections.get("goal", "")),
                ("Гипотеза", sections.get("hypothesis", "")),
                ("Задачи", sections.get("tasks", "")),
                ("Методы", sections.get("methods", "")),
            ],
        ),
        ("introduction", [("Введение", sections.get("introduction", ""))]),
        ("conclusion", [("Заключение", sections.get("conclusion", ""))]),
        (
            "survey_results",
            [
                ("Анкетирование/опрос", sections.get("survey", "")),
                ("Результаты", sections.get("results", "")),
            ],
        ),
        ("main_body", _main_body_chunks(sections.get("main_body", ""))),
    ]

    selected: list[str] = []
    omitted = False

    for _group_name, chunks in priority_groups:
        for label, chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            rendered = _render_context_chunk(label, chunk)
            current_size = len(_join_lines(selected))
            separator_size = 2 if selected else 0
            remaining = hard_char_limit - current_size - separator_size
            if remaining <= 0:
                omitted = True
                continue
            if len(rendered) <= remaining:
                selected.append(rendered)
                continue
            if remaining > len(label) + 12:
                selected.append(rendered[:remaining].rstrip())
            omitted = True

    text = _join_lines(selected)
    if not text:
        text = full_analysis_text[:hard_char_limit].rstrip()
        omitted = len(full_analysis_text) > hard_char_limit

    return SmartAnalysisContext(
        text=text,
        smart_context_used=True,
        was_truncated=omitted or len(text) > hard_char_limit,
    )


def _render_context_chunk(label: str, chunk: str) -> str:
    return f"{label}\n{chunk.strip()}"


def _main_body_chunks(text: str, *, chunk_size: int = 8_000) -> list[tuple[str, str]]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", text) if paragraph.strip()]
    chunks: list[tuple[str, str]] = []
    current: list[str] = []
    current_size = 0

    for paragraph in paragraphs:
        if current and current_size + len(paragraph) + 2 > chunk_size:
            chunks.append(("Основная часть", "\n\n".join(current)))
            current = []
            current_size = 0
        current.append(paragraph)
        current_size += len(paragraph) + 2

    if current:
        chunks.append(("Основная часть", "\n\n".join(current)))
    return chunks


def is_noise_claim(text: str) -> bool:
    """Return True for document furniture that should never become a claim."""

    line = _normalize_line(text)
    if not line:
        return True

    lowered = _normalize_for_match(line)

    if _is_page_number_line(line):
        return True
    if _detect_section_header(line) is not None and _line_is_heading_only(line):
        return True
    if _looks_like_toc_line(line):
        return True
    if _is_metadata_line(line):
        return True
    if _looks_like_numbered_heading(line):
        return True

    if re.fullmatch(r"(?:19|20)\d{2}", lowered):
        return True
    if re.fullmatch(r"(?:19|20)\d{2}\s+\d{1,3}\s+(?:содержание|оглавление)", lowered):
        return True
    if re.fullmatch(r"приложени[ея](?:\s+\d+)?", lowered):
        return True

    return False


def filter_noise_claims(claims: Iterable[T]) -> list[T]:
    """Filter objects with a ``text`` attribute, preserving their type."""

    filtered: list[T] = []
    for claim in claims:
        text = getattr(claim, "text", str(claim))
        if not is_noise_claim(text):
            filtered.append(claim)
    return filtered


def _append_analysis_line(
    line: str,
    *,
    section_key: str,
    sections: dict[str, list[str]],
    clean_lines: list[str],
    analysis_lines: list[str],
) -> None:
    sections[section_key].append(line)
    clean_lines.append(line)
    analysis_lines.append(line)


def _normalized_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = _normalize_line(raw_line)
        if not line:
            continue
        if _is_page_number_line(line):
            continue
        lines.append(line)
    return lines


def _normalize_line(line: str) -> str:
    line = (
        line.replace("\ufeff", "")
        .replace("\u00a0", " ")
        .replace("\u00ad", "")
        .replace("\t", " ")
    )
    line = re.sub(r"\s+", " ", line)
    return line.strip(" \u200b")


def _join_lines(lines: list[str]) -> str:
    return "\n".join(line for line in lines if line.strip()).strip()


def _normalize_for_match(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[«»\"“”]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,:;–—-")


def _is_page_number_line(line: str) -> bool:
    stripped = line.strip()
    return bool(
        re.fullmatch(r"\d{1,4}", stripped)
        or re.fullmatch(r"[-–—]\s*\d{1,4}\s*[-–—]", stripped)
        or re.fullmatch(r"стр(?:аница)?\.?\s*\d{1,4}", _normalize_for_match(stripped))
    )


def _detect_title_page_end(lines: list[str]) -> int:
    for index, line in enumerate(lines[:45]):
        detected = _detect_section_header(line)
        if detected is None:
            continue
        section_key, _ = detected
        prefix = lines[:index]
        if section_key == "table_of_contents":
            return index
        if prefix and any(_is_metadata_line(prefix_line) for prefix_line in prefix):
            return index
    return 0


def _detect_title(title_page_lines: list[str], all_lines: list[str]) -> str | None:
    candidates: list[str] = []
    source_lines = title_page_lines if title_page_lines else all_lines[:12]

    for line in source_lines:
        if _is_metadata_line(line) or is_noise_claim(line):
            continue
        quoted = re.search(r"[«\"]([^»\"]{4,120})[»\"]", line)
        if quoted:
            return quoted.group(1).strip()
        normalized = _normalize_for_match(line)
        if normalized in GENERIC_TITLE_PAGE_LINES:
            continue
        if 4 <= len(line) <= 140 and re.search(r"[а-яёa-z]", normalized):
            candidates.append(line.strip(" ."))

    if not candidates:
        return None
    return max(candidates, key=lambda value: (len(value.split()), len(value)))[:140]


def _detect_section_header(line: str) -> tuple[str, str] | None:
    candidates = _heading_candidates(line)
    for candidate in candidates:
        normalized = _normalize_for_match(candidate)
        normalized = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", normalized).strip()
        normalized = re.sub(r"\s+\d{1,3}$", "", normalized).strip()

        for section_key, patterns in SECTION_PATTERNS:
            for pattern in patterns:
                inline_match = re.fullmatch(rf"({pattern})\s*[:.-]\s*(.+)", normalized)
                if inline_match:
                    return section_key, inline_match.group(2).strip()
                if re.fullmatch(pattern, normalized):
                    return section_key, ""
                if section_key == "appendices" and re.fullmatch(rf"{pattern}\s+\d+", normalized):
                    return section_key, ""
    return None


def _heading_candidates(line: str) -> list[str]:
    parts = line.split()
    candidates = [line]
    max_skip = min(3, len(parts) - 1)
    for start in range(1, max_skip + 1):
        candidates.append(" ".join(parts[start:]))
    return candidates


def _line_is_heading_only(line: str) -> bool:
    normalized = _normalize_for_match(line)
    if len(normalized) > 80:
        return False
    for candidate in _heading_candidates(line):
        candidate = _normalize_for_match(candidate)
        candidate = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", candidate).strip()
        candidate = re.sub(r"\s+\d{1,3}$", "", candidate).strip()
        for _, patterns in SECTION_PATTERNS:
            if any(re.fullmatch(pattern, candidate) for pattern in patterns):
                return True
    return False


def _looks_like_toc_line(line: str) -> bool:
    normalized = _normalize_for_match(line)
    if not normalized:
        return True

    if re.search(r"\.{2,}\s*\d{1,3}$", line):
        return True
    if re.fullmatch(r"(?:19|20)\d{2}\s+\d{1,3}\s+(?:содержание|оглавление)", normalized):
        return True
    if re.fullmatch(r"\d{1,3}\s+\d+(?:\.\d+)*\.?\s*\S.{0,120}", normalized):
        return True
    if re.fullmatch(r"\d+(?:\.\d+)*\.?\s*\S.{0,120}\s+\d{1,3}", normalized):
        return True

    without_page = re.sub(r"\s+\d{1,3}$", "", line).strip()
    if without_page != line and _detect_section_header(without_page) is not None:
        return True

    return False


def _looks_like_numbered_heading(line: str) -> bool:
    normalized = _normalize_for_match(line)
    if len(normalized) > 130:
        return False
    if line.rstrip().endswith((".", "!", "?")):
        return False
    return bool(re.fullmatch(r"\d+(?:\.\d+)*\.?\s*\S.{0,120}", normalized))


def _is_metadata_line(line: str) -> bool:
    normalized = _normalize_for_match(line)
    if not normalized:
        return True

    if re.fullmatch(r"(?:19|20)\d{2}(?:\s*г)?", normalized):
        return True
    if re.fullmatch(r"(?:г\.?\s*)?[а-яё-]+,?\s*(?:19|20)\d{2}(?:\s*г)?", normalized):
        return True
    if re.search(r"\bкласс(?:а|е)?\s*\d+\b|\b\d+\s*класс(?:а|е)?\b", normalized):
        return True
    if re.search(r"\bучени(?:к|ца|цы|ка)?\s+\d+\s+класса\b", normalized):
        return True
    if normalized.startswith("направление:") or "квалификационная категория" in normalized:
        return True
    if any(keyword in normalized for keyword in METADATA_KEYWORDS) and len(normalized) <= 180:
        return True
    if _looks_like_fio(line):
        return True

    return False


def _looks_like_fio(line: str) -> bool:
    stripped = line.strip(" .")
    if re.fullmatch(r"[А-ЯЁ][а-яё-]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.", stripped):
        return True
    if re.fullmatch(r"[А-ЯЁ][а-яё-]+(?:\s+[А-ЯЁ][а-яё-]+){1,2}", stripped):
        return True
    return False

