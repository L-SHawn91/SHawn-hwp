from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from shawn_hwp.converters.soffice_engine import (
    SofficeConversionError,
    run_soffice_conversion,
    soffice_available,
)


def _staging_from_cmd(cmd: list[str]) -> Path:
    outdir_index = cmd.index("--outdir")
    return Path(cmd[outdir_index + 1])


def _input_from_cmd(cmd: list[str]) -> Path:
    return Path(cmd[-1])


def test_run_soffice_conversion_subprocess_failure_preserves_caller_files(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "report.pdf"
    destination.write_bytes(b"ORIGINAL-DESTINATION")
    sibling = tmp_path / "source.pdf"
    sibling.write_bytes(b"ORIGINAL-SIBLING")

    def fail_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="fake soffice failure")

    monkeypatch.setattr(subprocess, "run", fail_run)

    with pytest.raises(subprocess.CalledProcessError):
        run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"ORIGINAL-DESTINATION"
    assert sibling.read_bytes() == b"ORIGINAL-SIBLING"


def test_run_soffice_conversion_exit_zero_without_output_preserves_caller_files(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "custom-name.pdf"
    destination.write_bytes(b"KEEP-DEST")
    sibling = tmp_path / "source.pdf"
    sibling.write_bytes(b"KEEP-SIBLING")

    def empty_success(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="no output")

    monkeypatch.setattr(subprocess, "run", empty_success)

    with pytest.raises(SofficeConversionError):
        run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"KEEP-DEST"
    assert sibling.read_bytes() == b"KEEP-SIBLING"


def test_run_soffice_conversion_success_publishes_to_destination(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "custom-name.pdf"
    destination.write_bytes(b"OLD-DEST")
    sibling = tmp_path / "source.pdf"
    sibling.write_bytes(b"OLD-SIBLING")

    def succeed(cmd, **kwargs):
        staging = _staging_from_cmd(cmd)
        input_path = _input_from_cmd(cmd)
        (staging / f"{input_path.stem}.pdf").write_bytes(b"%PDF-NEW-CONTENT")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    result = run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"%PDF-NEW-CONTENT"
    assert sibling.read_bytes() == b"OLD-SIBLING"
    assert result.route == "docx-to-pdf"


@pytest.mark.skipif(not soffice_available(), reason="soffice not available")
def test_run_soffice_conversion_docx_to_pdf(tmp_path: Path):
    source = tmp_path / "source.docx"
    pdf = tmp_path / "out.pdf"

    # minimal docx generated via pandoc-compatible zip signature fixture copy is handled in higher-level CLI tests;
    # here we just reuse a real docx payload from the repository fixture path if available.
    repo_docx = Path('/tmp/shawn_hwp_probe.docx')
    if not repo_docx.exists():
        pytest.skip('probe docx not available')
    source.write_bytes(repo_docx.read_bytes())

    result = run_soffice_conversion(source, pdf, 'docx', 'pdf')
    assert pdf.exists()
    assert pdf.read_bytes()[:4] == b'%PDF'
    assert result.route == 'docx-to-pdf'