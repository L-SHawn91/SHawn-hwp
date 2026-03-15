"""QA report generation helpers for SHawn-hwp."""

from __future__ import annotations

from dataclasses import asdict, dataclass
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _score_text(source: Path, candidate: Path) -> int:
    if not source.exists() or not candidate.exists():
        return 0
    if source.stat().st_size == 0 or candidate.stat().st_size == 0:
        return 0
    return WEIGHTS["text"]


def _score_structure(source_format: str, candidate_format: str) -> int:
    if source_format == candidate_format:
        return WEIGHTS["structure"]
    if {source_format, candidate_format} <= {"hwpx", "docx", "md", "html"}:
        return 15
    return 10


def _score_category(source: Path, candidate: Path, category: str) -> int:
    if not source.exists() or not candidate.exists():
        return 0
    if candidate.stat().st_size == 0:
        return 0
    return WEIGHTS[category]


def _build_metrics(source: Path, candidate: Path, source_format: str, candidate_format: str) -> dict[str, int]:
    return {
        "text": _score_text(source, candidate),
        "structure": _score_structure(source_format, candidate_format),
        "table": _score_category(source, candidate, "table"),
        "image_caption": _score_category(source, candidate, "image_caption"),
        "footnote_numbering": _score_category(source, candidate, "footnote_numbering"),
        "submission": _score_category(source, candidate, "submission"),
        "roundtrip": WEIGHTS["roundtrip"] if source.exists() and candidate.exists() and candidate.stat().st_size > 0 else 0,
    }


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
    metrics = _build_metrics(source, candidate, source_format, candidate_format)
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
        "## Top Risks",
        "",
    ])
    if result.risk_categories:
        lines.extend(f"- {category}" for category in result.risk_categories)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
