from __future__ import annotations

from shawn_hwp.qa.scoring import (
    classify_loss_level,
    recommend_best_route,
    route_evaluation,
)


def test_classify_loss_level_marks_submission_blocking_risks():
    level = classify_loss_level(91, ["submission"])

    assert level.code == "L4"
    assert level.label == "submission-blocking loss"
    assert level.submission_blocking is True


def test_classify_loss_level_uses_score_when_no_blocking_risk():
    assert classify_loss_level(96, []).code == "L0"
    assert classify_loss_level(86, []).code == "L1"
    assert classify_loss_level(73, []).code == "L2"
    assert classify_loss_level(61, []).code == "L3"
    assert classify_loss_level(50, []).code == "L4"


def test_route_evaluation_combines_engine_signal_and_loss_level():
    result = route_evaluation(
        route="pandoc-md-to-docx",
        engine="pandoc",
        weighted_score=84,
        max_score=100,
        risk_categories=["table"],
        engine_available=True,
    )

    assert result.route == "pandoc-md-to-docx"
    assert result.loss_level.code == "L1"
    assert result.confidence == 0.76
    assert result.submission_ready is False
    assert "table" in result.reason


def test_route_evaluation_keeps_l0_minor_deltas_submission_ready():
    result = route_evaluation(
        route="md-to-md",
        engine="file-pair-qa",
        weighted_score=98,
        max_score=100,
        risk_categories=["text", "footnote_numbering"],
        engine_available=True,
    )

    assert result.loss_level.code == "L0"
    assert result.submission_ready is True


def test_recommend_best_route_prefers_ready_candidate_then_confidence():
    weak = route_evaluation(
        route="stub",
        engine="stub",
        weighted_score=92,
        max_score=100,
        risk_categories=[],
        engine_available=False,
    )
    strong = route_evaluation(
        route="rhwp-layout-plus-salvage",
        engine="rhwp+hwp-salvage",
        weighted_score=88,
        max_score=100,
        risk_categories=[],
        engine_available=True,
    )

    assert recommend_best_route([weak, strong]) == strong
