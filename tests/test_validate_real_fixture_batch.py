from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validate_real_fixture_batch_hwpx(tmp_path: Path):
    fixture_dir = REPO_ROOT / "data" / "fixtures" / "real-hwpx"
    source = fixture_dir / "source.hwpx"
    if not source.exists() or not zipfile.is_zipfile(source):
        pytest.skip("real-hwpx fixture is not bundled in the public repository")

    outdir = tmp_path / "real-batch"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "validate_real_fixture_batch.py"),
        "--fixture",
        "real-hwpx",
        "--from",
        "hwpx",
        "--outdir",
        str(outdir),
        "--targets",
        "docx",
        "html",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    summary_path = outdir / "real-hwpx" / "hwpx-batch-summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "SHawn-hwp real fixture batch validation" in result.stdout
    assert summary_path.exists()
    assert len(payload) == 2
    assert payload[0]["target"] == "docx"
    assert payload[1]["target"] == "html"
