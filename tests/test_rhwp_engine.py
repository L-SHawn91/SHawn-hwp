from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from shawn_hwp.converters import rhwp_engine
from shawn_hwp.converters.rhwp_engine import (
    export_hwp_layout_with_rhwp,
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


@pytest.mark.skipif(not REAL_HWP.exists() or not rhwp_core_available(), reason="real HWP fixture or rhwp core missing")
def test_convert_cli_hwp_to_md_can_use_rhwp_layout_route(tmp_path: Path):
    output = tmp_path / "out.md"
    metadata = tmp_path / "meta.json"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "convert.py"),
        "--input",
        str(REAL_HWP),
        "--from",
        "hwp",
        "--to",
        "md",
        "--route",
        "rhwp-layout",
        "--output",
        str(output),
        "--emit-metadata",
        str(metadata),
    ]

    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "engine=rhwp-core" in result.stdout
    assert output.exists()
    body = output.read_text(encoding="utf-8")
    assert "연구개발과제의 필요성" in body
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["target_format"] == "md"
    assert payload["route"] == "rhwp-layout-to-md"
    assert payload["output_size_bytes"] > 0


@pytest.mark.skipif(not REAL_HWP.exists() or not rhwp_core_available(), reason="real HWP fixture or rhwp core missing")
def test_convert_cli_hwp_to_docx_can_use_rhwp_layout_route(tmp_path: Path):
    output = tmp_path / "out.docx"
    metadata = tmp_path / "meta.json"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "convert.py"),
        "--input",
        str(REAL_HWP),
        "--from",
        "hwp",
        "--to",
        "docx",
        "--route",
        "rhwp-layout",
        "--output",
        str(output),
        "--emit-metadata",
        str(metadata),
    ]

    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "engine=rhwp-core" in result.stdout
    assert output.exists()
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["target_format"] == "docx"
    assert payload["route"] == "rhwp-layout-to-docx"
    assert payload["output_size_bytes"] > 0


def test_rhwp_probe_error_includes_stderr(monkeypatch: pytest.MonkeyPatch):
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr="Cannot find module @rhwp/core")

    monkeypatch.setattr(rhwp_engine, "rhwp_core_available", lambda: True)
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Cannot find module @rhwp/core"):
        export_hwp_layout_with_rhwp(Path("dummy.hwp"))
