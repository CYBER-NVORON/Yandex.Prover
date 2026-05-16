from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, TypeVar


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
    warnings: list[str] = field(default_factory=list)


def preprocess_document(raw_text: str) -> PreprocessedDocument:
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
    analysis_text = _join_lines(analysis_lines)

    if not analysis_text:
        warnings.append("Не удалось выделить основной текст для анализа.")
    if title_page_end > 0:
        warnings.append("Титульный лист исключён из анализа утверждений.")
    if toc_lines:
        warnings.append("Содержание исключено из анализа утверждений.")
    if references_lines:
        warnings.append("Список литературы сохранён отдельно и исключён из карты доказательности.")
    if appendices_lines:
        warnings.append("Приложения сохранены отдельно и исключены из карты доказательности.")

    return PreprocessedDocument(
        title=title,
        clean_text=clean_text,
        analysis_text=analysis_text,
        metadata_text=_join_lines(metadata_lines),
        toc_text=_join_lines(toc_lines),
        references_text=_join_lines(references_lines),
        appendices_text=_join_lines(appendices_lines),
        sections={key: _join_lines(value) for key, value in sections.items() if value},
        warnings=warnings,
    )


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
