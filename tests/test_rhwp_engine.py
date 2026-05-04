from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from shawn_hwp.converters.rhwp_engine import (
    export_hwp_svg_with_rhwp,
    probe_hwp_with_rhwp,
    rhwp_core_available,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_HWP = REPO_ROOT / "data" / "fixtures" / "real-hwp" / "source.hwp"


def test_rhwp_core_available_when_external_package_installed():
    assert rhwp_core_available() is True


@pytest.mark.skipif(not REAL_HWP.exists() or not rhwp_core_available(), reason="real HWP fixture or rhwp core missing")
def test_rhwp_probe_reports_page_count():
    payload = probe_hwp_with_rhwp(REAL_HWP)

    assert payload["engine"] == "rhwp-core"
    assert payload["page_count"] >= 1
    assert payload["input_size_bytes"] == REAL_HWP.stat().st_size


@pytest.mark.skipif(not REAL_HWP.exists() or not rhwp_core_available(), reason="real HWP fixture or rhwp core missing")
def test_rhwp_export_svg_first_page(tmp_path: Path):
    payload = export_hwp_svg_with_rhwp(REAL_HWP, tmp_path, pages="0")

    assert payload["engine"] == "rhwp-core"
    assert payload["exported_pages"] == [0]
    svg_path = Path(payload["outputs"][0])
    assert svg_path.exists()
    assert svg_path.read_text(encoding="utf-8").lstrip().startswith("<svg")


@pytest.mark.skipif(not REAL_HWP.exists() or not rhwp_core_available(), reason="real HWP fixture or rhwp core missing")
def test_convert_cli_hwp_to_svg_real_fixture(tmp_path: Path):
    outdir = tmp_path / "svg"
    metadata = tmp_path / "meta.json"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "convert.py"),
        "--input",
        str(REAL_HWP),
        "--from",
        "hwp",
        "--to",
        "svg",
        "--output",
        str(outdir),
        "--emit-metadata",
        str(metadata),
    ]

    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "engine=rhwp-core" in result.stdout
    assert (outdir / "page-0000.svg").exists()
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["target_format"] == "svg"
    assert payload["route"] == "rhwp-svg-render"
    assert payload["output_size_bytes"] > 0
