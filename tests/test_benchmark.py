from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_cli_generates_reports(tmp_path: Path):
    outdir = tmp_path / "benchmark-out"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "benchmark.py"),
        "--fixture",
        "simple-report",
        "--candidate",
        "shawn-hwp-route",
        "--from",
        "md",
        "--to",
        "md",
        "--outdir",
        str(outdir),
        "--notes",
        "test run",
    ]

    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    run_dir = outdir / "simple-report" / "shawn-hwp-route"
    report_path = run_dir / "qa_report.md"
    json_path = run_dir / "qa_report.json"
    manifest_path = run_dir / "benchmark_manifest.json"

    assert "SHawn-hwp benchmark" in result.stdout
    assert report_path.exists()
    assert json_path.exists()
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["fixture"] == "simple-report"
    assert manifest["candidate"] == "shawn-hwp-route"
    assert manifest["score"] == 100

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["weighted_score"] == 100
    assert payload["comparisons"]["heading_similarity"] == 1.0
