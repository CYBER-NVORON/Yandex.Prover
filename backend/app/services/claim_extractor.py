from __future__ import annotations

import re
from itertools import count

from app.services.document_preprocessor import is_noise_claim
from app.schemas import Claim


NUMBER_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:\d+[\d\s,.]*\s?(?:%|процента|процентов|раза|раз|лет|руб\.?|₽|млн|млрд)?)[^.!?\n]*[.!?]?)",
    re.IGNORECASE,
)
GENERALIZATION_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:многие|большинство|все|никто|каждый|всегда|никогда|любой|повсеместно)[^.!?\n]*[.!?]?)",
    re.IGNORECASE,
)
COMPARISON_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:лучше|хуже|эффективнее|быстрее|дешевле|сильнее|крупнее|мельче|больше|меньше|выше|ниже|длиннее|короче|тяжелее|легче|по сравнению|превосходит|альтернатив[аы])[^\n.!?]*[.!?]?)",
    re.IGNORECASE,
)
CAUSALITY_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:потому что|поэтому|из-за|в результате|приводит к|позволяет|влияет на|увеличивает|снижает)[^.!?\n]*[.!?]?)",
    re.IGNORECASE,
)
STRONG_CONCLUSION_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:доказано|очевидно|единственный|безусловно|гарантирует|решает проблему|не имеет аналогов)[^.!?\n]*[.!?]?)",
    re.IGNORECASE,
)
FACT_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:является|являются|имеет|имеют|умеет|умеют|может|могут|отличается|отличаются|разные|создавать орудия|считать)[^.!?\n]*[.!?]?)",
    re.IGNORECASE,
)


def split_sentences(text: str) -> list[str]:
    rough = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [part.strip() for part in rough if len(part.strip()) > 8]


def _location_for_sentence(sentence: str, text: str) -> str:
    index = text.find(sentence[: min(len(sentence), 40)])
    if index < 0:
        return "фрагмент текста"
    line = text[:index].count("\n") + 1
    return f"примерно строка {line}"


def _make_claim(
    *,
    sentence: str,
    claim_type: str,
    text: str,
    explanation: str,
    risk_level: str,
    evidence_status: str,
    sequence: int,
) -> Claim:
    clean_sentence = _strip_claim_label(" ".join(sentence.strip().split()))
    if evidence_status == "needs_source":
        recommendation = "Добавить источник, данные исследования или внутренний пример, потому что утверждение не подтверждается внутри материала."
    elif evidence_status == "too_strong":
        recommendation = "Смягчить формулировку или добавить доказательство, которое показывает границы применимости утверждения."
    else:
        recommendation = "Усилить утверждение примером или пояснить, на какой части материала оно основано."

    suggested_rewrite = clean_sentence
    if risk_level in {"medium", "high"}:
        suggested_rewrite = f"По материалу можно предположить, что {clean_sentence[0].lower() + clean_sentence[1:]}"

    return Claim(
        id=f"claim_{sequence}",
        text=clean_sentence,
        claim_type=claim_type,  # type: ignore[arg-type]
        location=_location_for_sentence(clean_sentence, text),
        needs_evidence=evidence_status in {"needs_source", "weak_argument", "too_strong", "unverifiable_from_text"},
        evidence_status=evidence_status,  # type: ignore[arg-type]
        risk_level=risk_level,  # type: ignore[arg-type]
        explanation=explanation,
        recommendation=recommendation,
        suggested_rewrite=suggested_rewrite,
    )


def _strip_claim_label(sentence: str) -> str:
    return re.sub(
        r"^(?:гипотеза|выводы?|заключение|цель(?:\s+работы|\s+исследования)?|методы(?:\s+исследования)?)\s*[:.-]\s*",
        "",
        sentence,
        flags=re.IGNORECASE,
    ).strip()


def extract_claims(text: str, limit: int = 10) -> list[Claim]:
    """Heuristic claim extraction for the local MVP.

    The extractor never verifies external facts. It only flags claims that need
    evidence or are weakly supported by the submitted material.
    """
    normalized = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip() and not is_noise_claim(line)
    )
    claims: list[Claim] = []
    seen: set[str] = set()
    claim_ids = count(1)

    patterns = [
        (
            NUMBER_PATTERN,
            "number",
            "Числовое утверждение требует методики, источника или расчёта.",
            "high",
            "needs_source",
        ),
        (
            GENERALIZATION_PATTERN,
            "generalization",
            "Широкое обобщение может вызвать вопрос о масштабе и подтверждении.",
            "medium",
            "needs_source",
        ),
        (
            COMPARISON_PATTERN,
            "comparison",
            "Сравнение требует критериев и явного объекта сравнения.",
            "medium",
            "weak_argument",
        ),
        (
            CAUSALITY_PATTERN,
            "causality",
            "Причинно-следственная связь требует объяснения механизма или доказательства.",
            "medium",
            "weak_argument",
        ),
        (
            STRONG_CONCLUSION_PATTERN,
            "unsupported_conclusion",
            "Слишком сильный вывод без ограничений выглядит уязвимым.",
            "high",
            "too_strong",
        ),
        (
            FACT_PATTERN,
            "fact",
            "Фактическое утверждение стоит связать с наблюдением, источником или частью исследования.",
            "medium",
            "needs_source",
        ),
    ]

    for pattern, claim_type, explanation, risk, status in patterns:
        for match in pattern.finditer(normalized):
            sentence = " ".join(match.group("sentence").strip().split())
            claim_sentence = _strip_claim_label(sentence)
            dedupe_key = claim_sentence.lower()
            if not claim_sentence or dedupe_key in seen or is_noise_claim(sentence) or is_noise_claim(claim_sentence):
                continue
            seen.add(dedupe_key)
            claims.append(
                _make_claim(
                    sentence=claim_sentence,
                    claim_type=claim_type,
                    text=normalized,
                    explanation=explanation,
                    risk_level=risk,
                    evidence_status=status,
                    sequence=next(claim_ids),
                )
            )
            if len(claims) >= limit:
                return claims

    if len(claims) < 3:
        for sentence in split_sentences(normalized):
            claim_sentence = _strip_claim_label(sentence)
            lower = claim_sentence.lower()
            if lower in seen:
                continue
            if not claim_sentence or is_noise_claim(sentence) or is_noise_claim(claim_sentence):
                continue
            if any(marker in lower for marker in ("важно", "нужно", "следует", "показывает", "является", "умеют", "разные")):
                seen.add(lower)
                claims.append(
                    _make_claim(
                        sentence=claim_sentence,
                        claim_type="opinion",
                        text=normalized,
                        explanation="Оценочное утверждение стоит подкрепить примером из материала.",
                        risk_level="low",
                        evidence_status="ok",
                        sequence=next(claim_ids),
                    )
                )
            if len(claims) >= min(limit, 5):
                break

    return claims[:limit]

