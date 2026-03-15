from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from shawn_hwp.qa.reporting import classify_readiness, generate_qa_result, render_markdown_report


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_classify_readiness():
    assert classify_readiness(95) == "near submission-ready"
    assert classify_readiness(82) == "minor repair needed"
    assert classify_readiness(71) == "working draft quality"
    assert classify_readiness(69) == "unsafe without repair"


def test_generate_qa_result_and_render(tmp_path: Path):
    source = tmp_path / "source.hwpx"
    candidate = tmp_path / "candidate.docx"
    source.write_text("original content", encoding="utf-8")
    candidate.write_text("converted content", encoding="utf-8")

    result = generate_qa_result(source, candidate, "hwpx", "docx", label="fixture-a")

    assert result.weighted_score == 95
    assert result.readiness == "near submission-ready"
    assert result.metrics["structure"] == 15
    assert result.risk_categories == ["structure"]

    report = render_markdown_report(result)
    assert "# SHawn-hwp QA Report" in report
    assert "fixture-a" in report
    assert "**95/100**" in report


def test_cli_writes_report_and_json(tmp_path: Path):
    source = tmp_path / "source.hwpx"
    candidate = tmp_path / "candidate.docx"
    report = tmp_path / "report.md"
    json_path = tmp_path / "report.json"
    source.write_text("original content", encoding="utf-8")
    candidate.write_text("converted content", encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "qa_report.py"),
        "--source",
        str(source),
        "--candidate",
        str(candidate),
        "--source-format",
        "hwpx",
        "--candidate-format",
        "docx",
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
    assert "95/100" in report.read_text(encoding="utf-8")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["label"] == "smoke"
    assert payload["weighted_score"] == 95
