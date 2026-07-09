"""Quality scoring helpers.

The scoring module is intentionally not a parser. It is the QA layer that lets
SHawn-hwp compare conversion routes, name conversion loss, and decide whether a
candidate is safe enough for submission review.
"""

from __future__ import annotations

from dataclasses import dataclass

WEIGHTS = {
    "text": 25,
    "structure": 20,
    "table": 15,
    "image_caption": 10,
    "footnote_numbering": 10,
    "submission": 10,
    "roundtrip": 10,
}

LOSS_LEVEL_DESCRIPTIONS = {
    "L0": "no visible loss",
    "L1": "minor style loss",
    "L2": "structure loss",
    "L3": "content loss",
    "L4": "submission-blocking loss",
}

SUBMISSION_BLOCKING_RISKS = {"submission", "missing_candidate", "template", "protected_region"}
SUBMISSION_READY_BLOCKING_RISKS = SUBMISSION_BLOCKING_RISKS | {"structure", "table", "footnote_numbering"}


@dataclass(frozen=True)
class LossLevel:
    code: str
    label: str
    submission_blocking: bool


@dataclass(frozen=True)
class RouteEvaluation:
    route: str
    engine: str
    weighted_score: int
    max_score: int
    confidence: float
    loss_level: LossLevel
    risk_categories: tuple[str, ...]
    engine_available: bool
    submission_ready: bool
    reason: str


def total_weight() -> int:
    return sum(WEIGHTS.values())


def classify_loss_level(score_percent: float, risk_categories: list[str] | tuple[str, ...]) -> LossLevel:
    """Classify conversion loss using score and submission-blocking risks.

    L0 means a candidate can be treated as nearly lossless for review. L4 means
    do not submit without manual repair, even if the numeric score looks high.
    """

    risks = set(risk_categories)
    if risks & SUBMISSION_BLOCKING_RISKS:
        code = "L4"
    elif score_percent >= 95:
        code = "L0"
    elif score_percent >= 80:
        code = "L1"
    elif score_percent >= 70:
        code = "L2"
    elif score_percent >= 60:
        code = "L3"
    else:
        code = "L4"
    return LossLevel(
        code=code,
        label=LOSS_LEVEL_DESCRIPTIONS[code],
        submission_blocking=code == "L4",
    )


def route_evaluation(
    *,
    route: str,
    engine: str,
    weighted_score: int,
    max_score: int,
    risk_categories: list[str] | tuple[str, ...],
    engine_available: bool,
) -> RouteEvaluation:
    """Evaluate one conversion route as an auditable QA candidate."""

    score_percent = (weighted_score / max_score * 100) if max_score else 0.0
    loss_level = classify_loss_level(score_percent, risk_categories)
    risk_penalty = 0.08 * len(risk_categories)
    engine_penalty = 0.0 if engine_available else 0.45
    confidence = round(max(0.0, min(1.0, weighted_score / max_score - risk_penalty - engine_penalty)), 2) if max_score else 0.0
    risks = tuple(risk_categories)
    readiness_blockers = SUBMISSION_BLOCKING_RISKS if loss_level.code == "L0" else SUBMISSION_READY_BLOCKING_RISKS
    submission_ready = engine_available and loss_level.code in {"L0", "L1"} and not (set(risks) & readiness_blockers)
    risk_text = ", ".join(risks) if risks else "no tracked risk"
    availability = "available" if engine_available else "unavailable"
    reason = f"engine={engine} ({availability}); loss={loss_level.code}; risks={risk_text}"
    return RouteEvaluation(
        route=route,
        engine=engine,
        weighted_score=weighted_score,
        max_score=max_score,
        confidence=confidence,
        loss_level=loss_level,
        risk_categories=risks,
        engine_available=engine_available,
        submission_ready=submission_ready,
        reason=reason,
    )


def recommend_best_route(candidates: list[RouteEvaluation] | tuple[RouteEvaluation, ...]) -> RouteEvaluation:
    """Pick the safest candidate: ready routes first, then confidence, then score."""

    if not candidates:
        raise ValueError("at least one route evaluation is required")
    return max(
        candidates,
        key=lambda item: (
            item.submission_ready,
            item.engine_available,
            item.confidence,
            item.weighted_score,
        ),
    )
