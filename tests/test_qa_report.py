from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from shawn_hwp.qa.reporting import classify_readiness, generate_qa_result, render_markdown_report


REPO_ROOT = Path(__file__).resolve().parents[1]


SOURCE_TEXT = """# Title

## Section A
Hello world

| A | B |
|---|---|
| 1 | 2 |
"""

CANDIDATE_GOOD = """# Title

## Section A
Hello world updated

| A | B |
|---|---|
| 1 | 2 |
"""

CANDIDATE_BAD = """Plain paragraph only
No headings
No table
"""


def test_classify_readiness():
    assert classify_readiness(95) == "near submission-ready"
    assert classify_readiness(82) == "minor repair needed"
    assert classify_readiness(71) == "working draft quality"
    assert classify_readiness(69) == "unsafe without repair"


def test_generate_qa_result_and_render(tmp_path: Path):
    source = tmp_path / "source.md"
    candidate = tmp_path / "candidate.md"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    candidate.write_text(CANDIDATE_GOOD, encoding="utf-8")

    result = generate_qa_result(source, candidate, "md", "md", label="fixture-a")

    assert result.weighted_score >= 95
    assert result.readiness == "near submission-ready"
    assert result.loss_level["code"] == "L0"
    assert result.route_evaluation["submission_ready"] is True
    assert result.metrics["structure"] == 20
    assert result.metrics["table"] == 15
    assert result.metrics["footnote_numbering"] == 10
    assert result.metrics["submission"] == 10
    assert result.comparisons["source_heading_count"] == 2
    assert result.comparisons["source_table_count"] >= 2
    assert result.comparisons["numbering_similarity"] == 1.0
    assert result.comparisons["footnote_similarity"] == 1.0

    report = render_markdown_report(result)
    assert "# SHawn-hwp QA Report" in report
    assert "fixture-a" in report
    assert "text similarity" in report
    assert "loss level" in report


def test_generate_qa_result_detects_structure_and_table_loss(tmp_path: Path):
    source = tmp_path / "source.md"
    candidate = tmp_path / "candidate.md"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    candidate.write_text(CANDIDATE_BAD, encoding="utf-8")

    result = generate_qa_result(source, candidate, "md", "md")

    assert result.metrics["structure"] == 0
    assert result.metrics["table"] == 0
    assert result.loss_level["code"] in {"L2", "L3", "L4"}
    assert result.route_evaluation["submission_ready"] is False
    assert "structure" in result.risk_categories
    assert "table" in result.risk_categories


def test_cli_writes_report_and_json(tmp_path: Path):
    source = tmp_path / "source.md"
    candidate = tmp_path / "candidate.md"
    report = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    candidate.write_text(CANDIDATE_GOOD, encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "qa_report.py"),
        "--source",
        str(source),
        "--candidate",
        str(candidate),
        "--source-format",
        "md",
        "--candidate-format",
        "md",
        "--report",
        str(report),
        "--json",
        str(json_path),
        "--label",
        "smoke",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "near submission-ready" in result.stdout
    assert report.exists()
    assert json_path.exists()
    assert "heading similarity" in report.read_text(encoding="utf-8")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["label"] == "smoke"
    assert payload["loss_level"]["code"] == "L0"
    assert payload["route_evaluation"]["route"] == "md-to-md"
    assert payload["comparisons"]["source_heading_count"] == 2
    assert payload["metrics"]["table"] == 15
