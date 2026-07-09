from __future__ import annotations

import json
import shutil
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
    assert manifest["loss_level"]["code"] == "L0"
    assert manifest["route_evaluation"]["submission_ready"] is True

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["weighted_score"] == 100
    assert payload["comparisons"]["heading_similarity"] == 1.0


def test_benchmark_cli_falls_back_to_convert_stub_when_candidate_missing(tmp_path: Path):
    fixture_dir = REPO_ROOT / "data" / "fixtures" / "simple-report"
    candidate_path = fixture_dir / "candidate.md"
    backup_path = fixture_dir / "candidate.md.bak"
    shutil.move(candidate_path, backup_path)
    try:
        outdir = tmp_path / "benchmark-out"
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "benchmark.py"),
            "--fixture",
            "simple-report",
            "--candidate",
            "stub-route",
            "--from",
            "md",
            "--to",
            "md",
            "--outdir",
            str(outdir),
        ]
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

        run_dir = outdir / "simple-report" / "stub-route"
        generated_candidate = run_dir / "converted_candidate.md"
        manifest = json.loads((run_dir / "benchmark_manifest.json").read_text(encoding="utf-8"))

        assert "SHawn-hwp benchmark" in result.stdout
        assert generated_candidate.exists()
        assert manifest["candidate_path"] == str(generated_candidate)
    finally:
        shutil.move(backup_path, candidate_path)
