from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validate_real_fixture_hwpx_to_docx(tmp_path: Path):
    fixture_dir = REPO_ROOT / "data" / "fixtures" / "real-hwpx"
    source = fixture_dir / "source.hwpx"
    source.write_text("real fixture placeholder content", encoding="utf-8")
    try:
        outdir = tmp_path / "real-validate"
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_real_fixture.py"),
            "--fixture",
            "real-hwpx",
            "--from",
            "hwpx",
            "--to",
            "docx",
            "--outdir",
            str(outdir),
        ]
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

        run_dir = outdir / "real-hwpx" / "hwpx-to-docx"
        manifest = json.loads((run_dir / "validation_manifest.json").read_text(encoding="utf-8"))
        assert "SHawn-hwp real fixture validation" in result.stdout
        assert (run_dir / "converted.docx").exists()
        assert manifest["fixture"] == "real-hwpx"
        assert manifest["target_format"] == "docx"
    finally:
        if source.exists():
            source.unlink()
