"""QA report generation helpers for SHawn-hwp."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from shawn_hwp.qa.scoring import WEIGHTS, total_weight


READINESS_BANDS = (
    (90, "near submission-ready"),
    (80, "minor repair needed"),
    (70, "working draft quality"),
    (0, "unsafe without repair"),
)


@dataclass
class QaResult:
    source: str
    candidate: str
    source_format: str
    candidate_format: str
    label: str | None
    source_exists: bool
    candidate_exists: bool
    source_size_bytes: int | None
    candidate_size_bytes: int | None
    weighted_score: int
    max_score: int
    readiness: str
    risk_categories: list[str]
    metrics: dict[str, int]
    comparisons: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_read_text(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_markdown_headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.lstrip().startswith("#")]


def _count_markdown_tables(text: str) -> int:
    return sum(1 for line in text.splitlines() if "|" in line and line.count("|") >= 2)


def _extract_numbered_list_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\.\s+", line)
        if m:
            tokens.append(m.group(1))
    return tokens


def _count_footnotes(text: str) -> int:
    refs = re.findall(r"\[\^[^\]]+\]", text)
    defs = re.findall(r"^\[\^[^\]]+\]:", text, flags=re.MULTILINE)
    return max(len(refs), len(defs))


def _count_checkboxes(text: str) -> int:
    return len(re.findall(r"- \[[ xX]\]", text))


def _count_placeholders(text: str) -> int:
    return len(re.findall(r"placeholder", text, flags=re.IGNORECASE))


def _text_similarity(source_text: str, candidate_text: str) -> float:
    if not source_text or not candidate_text:
        return 0.0
    return SequenceMatcher(None, _normalize_text(source_text), _normalize_text(candidate_text)).ratio()


def _heading_similarity(source_text: str, candidate_text: str) -> float:
    source_headings = _extract_markdown_headings(source_text)
    candidate_headings = _extract_markdown_headings(candidate_text)
    if not source_headings and not candidate_headings:
        return 1.0
    if not source_headings or not candidate_headings:
        return 0.0
    return SequenceMatcher(None, "\n".join(source_headings), "\n".join(candidate_headings)).ratio()


def _table_similarity(source_text: str, candidate_text: str) -> float:
    source_tables = _count_markdown_tables(source_text)
    candidate_tables = _count_markdown_tables(candidate_text)
    if source_tables == 0 and candidate_tables == 0:
        return 1.0
    if source_tables == 0 or candidate_tables == 0:
        return 0.0
    gap = abs(source_tables - candidate_tables)
    return max(0.0, 1.0 - (gap / max(source_tables, candidate_tables)))


def _numbering_similarity(source_text: str, candidate_text: str) -> float:
    source_numbers = _extract_numbered_list_tokens(source_text)
    candidate_numbers = _extract_numbered_list_tokens(candidate_text)
    if not source_numbers and not candidate_numbers:
        return 1.0
    if not source_numbers or not candidate_numbers:
        return 0.0
    return SequenceMatcher(None, " ".join(source_numbers), " ".join(candidate_numbers)).ratio()


def _footnote_similarity(source_text: str, candidate_text: str) -> float:
    source_count = _count_footnotes(source_text)
    candidate_count = _count_footnotes(candidate_text)
    if source_count == 0 and candidate_count == 0:
        return 1.0
    if source_count == 0 or candidate_count == 0:
        return 0.0
    gap = abs(source_count - candidate_count)
    return max(0.0, 1.0 - (gap / max(source_count, candidate_count)))


def _submission_similarity(source_text: str, candidate_text: str) -> float:
    source_boxes = _count_checkboxes(source_text)
    candidate_boxes = _count_checkboxes(candidate_text)
    source_placeholders = _count_placeholders(source_text)
    candidate_placeholders = _count_placeholders(candidate_text)

    checkbox_ratio = 1.0 if source_boxes == candidate_boxes else max(0.0, 1.0 - abs(source_boxes - candidate_boxes) / max(source_boxes, candidate_boxes, 1))
    placeholder_ratio = 1.0 if source_placeholders == candidate_placeholders else 0.0
    return (checkbox_ratio + placeholder_ratio) / 2


def _score_ratio(weight: int, ratio: float) -> int:
    ratio = min(1.0, max(0.0, ratio))
    return int(round(weight * ratio))


def _build_comparisons(source: Path, candidate: Path) -> dict[str, Any]:
    source_text = _safe_read_text(source)
    candidate_text = _safe_read_text(candidate)
    return {
        "text_similarity": round(_text_similarity(source_text, candidate_text), 4),
        "heading_similarity": round(_heading_similarity(source_text, candidate_text), 4),
        "source_heading_count": len(_extract_markdown_headings(source_text)),
        "candidate_heading_count": len(_extract_markdown_headings(candidate_text)),
        "table_similarity": round(_table_similarity(source_text, candidate_text), 4),
        "source_table_count": _count_markdown_tables(source_text),
        "candidate_table_count": _count_markdown_tables(candidate_text),
        "numbering_similarity": round(_numbering_similarity(source_text, candidate_text), 4),
        "source_numbering_count": len(_extract_numbered_list_tokens(source_text)),
        "candidate_numbering_count": len(_extract_numbered_list_tokens(candidate_text)),
        "footnote_similarity": round(_footnote_similarity(source_text, candidate_text), 4),
        "source_footnote_count": _count_footnotes(source_text),
        "candidate_footnote_count": _count_footnotes(candidate_text),
        "submission_similarity": round(_submission_similarity(source_text, candidate_text), 4),
        "source_checkbox_count": _count_checkboxes(source_text),
        "candidate_checkbox_count": _count_checkboxes(candidate_text),
        "source_placeholder_count": _count_placeholders(source_text),
        "candidate_placeholder_count": _count_placeholders(candidate_text),
    }


def _build_metrics(source: Path, candidate: Path, source_format: str, candidate_format: str) -> tuple[dict[str, int], dict[str, Any]]:
    comparisons = _build_comparisons(source, candidate)
    source_exists = source.exists() and source.stat().st_size > 0
    candidate_exists = candidate.exists() and candidate.stat().st_size > 0

    text_score = _score_ratio(WEIGHTS["text"], comparisons["text_similarity"])
    structure_ratio = comparisons["heading_similarity"]
    if source_format != candidate_format:
        structure_ratio *= 0.9
    structure_score = _score_ratio(WEIGHTS["structure"], structure_ratio)
    table_score = _score_ratio(WEIGHTS["table"], comparisons["table_similarity"])
    footnote_numbering_ratio = (comparisons["numbering_similarity"] + comparisons["footnote_similarity"]) / 2
    footnote_numbering_score = _score_ratio(WEIGHTS["footnote_numbering"], footnote_numbering_ratio)
    submission_score = _score_ratio(WEIGHTS["submission"], comparisons["submission_similarity"])

    metrics = {
        "text": text_score if source_exists and candidate_exists else 0,
        "structure": structure_score if source_exists and candidate_exists else 0,
        "table": table_score if source_exists and candidate_exists else 0,
        "image_caption": WEIGHTS["image_caption"] if candidate_exists else 0,
        "footnote_numbering": footnote_numbering_score if source_exists and candidate_exists else 0,
        "submission": submission_score if source_exists and candidate_exists else 0,
        "roundtrip": WEIGHTS["roundtrip"] if source_exists and candidate_exists else 0,
    }
    return metrics, comparisons


def classify_readiness(score: int) -> str:
    for threshold, label in READINESS_BANDS:
        if score >= threshold:
            return label
    return "unsafe without repair"


def top_risk_categories(metrics: dict[str, int], limit: int = 3) -> list[str]:
    deficits = sorted(
        ((category, WEIGHTS[category] - value) for category, value in metrics.items()),
        key=lambda item: (-item[1], item[0]),
    )
    return [category for category, deficit in deficits if deficit > 0][:limit]


def generate_qa_result(
    source: Path,
    candidate: Path,
    source_format: str,
    candidate_format: str,
    label: str | None = None,
) -> QaResult:
    metrics, comparisons = _build_metrics(source, candidate, source_format, candidate_format)
    score = sum(metrics.values())
    return QaResult(
        source=str(source),
        candidate=str(candidate),
        source_format=source_format,
        candidate_format=candidate_format,
        label=label,
        source_exists=source.exists(),
        candidate_exists=candidate.exists(),
        source_size_bytes=source.stat().st_size if source.exists() else None,
        candidate_size_bytes=candidate.stat().st_size if candidate.exists() else None,
        weighted_score=score,
        max_score=total_weight(),
        readiness=classify_readiness(score),
        risk_categories=top_risk_categories(metrics),
        metrics=metrics,
        comparisons=comparisons,
    )


def render_markdown_report(result: QaResult) -> str:
    lines = [
        "# SHawn-hwp QA Report",
        "",
        f"- source: `{result.source}`",
        f"- candidate: `{result.candidate}`",
        f"- source format: `{result.source_format}`",
        f"- candidate format: `{result.candidate_format}`",
        f"- score: **{result.weighted_score}/{result.max_score}**",
        f"- readiness: **{result.readiness}**",
    ]
    if result.label:
        lines.append(f"- label: `{result.label}`")
    lines.extend([
        "",
        "## Metrics",
        "",
        "| Category | Score | Max |",
        "|---|---:|---:|",
    ])
    for category, value in result.metrics.items():
        lines.append(f"| {category} | {value} | {WEIGHTS[category]} |")
    lines.extend([
        "",
        "## Comparisons",
        "",
        f"- text similarity: `{result.comparisons['text_similarity']}`",
        f"- heading similarity: `{result.comparisons['heading_similarity']}`",
        f"- source heading count: `{result.comparisons['source_heading_count']}`",
        f"- candidate heading count: `{result.comparisons['candidate_heading_count']}`",
        f"- table similarity: `{result.comparisons['table_similarity']}`",
        f"- source table count: `{result.comparisons['source_table_count']}`",
        f"- candidate table count: `{result.comparisons['candidate_table_count']}`",
        f"- numbering similarity: `{result.comparisons['numbering_similarity']}`",
        f"- source numbering count: `{result.comparisons['source_numbering_count']}`",
        f"- candidate numbering count: `{result.comparisons['candidate_numbering_count']}`",
        f"- footnote similarity: `{result.comparisons['footnote_similarity']}`",
        f"- source footnote count: `{result.comparisons['source_footnote_count']}`",
        f"- candidate footnote count: `{result.comparisons['candidate_footnote_count']}`",
        f"- submission similarity: `{result.comparisons['submission_similarity']}`",
        f"- source checkbox count: `{result.comparisons['source_checkbox_count']}`",
        f"- candidate checkbox count: `{result.comparisons['candidate_checkbox_count']}`",
        f"- source placeholder count: `{result.comparisons['source_placeholder_count']}`",
        f"- candidate placeholder count: `{result.comparisons['candidate_placeholder_count']}`",
        "",
        "## Top Risks",
        "",
    ])
    if result.risk_categories:
        lines.extend(f"- {category}" for category in result.risk_categories)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
