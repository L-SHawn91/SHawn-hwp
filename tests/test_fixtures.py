from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_benchmark(tmp_path: Path, fixture: str) -> tuple[dict, dict]:
    outdir = tmp_path / "fixture-bench"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "benchmark.py"),
        "--fixture",
        fixture,
        "--candidate",
        "fixture-check",
        "--from",
        "md",
        "--to",
        "md",
        "--outdir",
        str(outdir),
    ]
    subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    run_dir = outdir / fixture / "fixture-check"
    payload = json.loads((run_dir / "qa_report.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "benchmark_manifest.json").read_text(encoding="utf-8"))
    return payload, manifest


def test_table_heavy_fixture_surfaces_table_risk(tmp_path: Path):
    payload, manifest = run_benchmark(tmp_path, "table-heavy")
    assert manifest["fixture"] == "table-heavy"
    assert payload["metrics"]["table"] < 15
    assert "table" in payload["risk_categories"]


def test_image_caption_fixture_runs_cleanly(tmp_path: Path):
    payload, manifest = run_benchmark(tmp_path, "image-caption")
    assert manifest["fixture"] == "image-caption"
    assert payload["weighted_score"] == 100
    assert payload["comparisons"]["heading_similarity"] == 1.0


def test_footnote_heavy_fixture_detects_text_loss(tmp_path: Path):
    payload, manifest = run_benchmark(tmp_path, "footnote-heavy")
    assert manifest["fixture"] == "footnote-heavy"
    assert payload["weighted_score"] < 100
    assert payload["metrics"]["text"] < 25
