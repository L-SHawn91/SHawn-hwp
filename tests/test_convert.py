from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from shawn_hwp.converters.pandoc_engine import pandoc_available
from shawn_hwp.converters.stub import run_stub_conversion


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_run_stub_conversion_preserves_input_and_writes_output(tmp_path: Path):
    source = tmp_path / "source.md"
    output = tmp_path / "out.md"
    source.write_text("# Title\n\nhello\n", encoding="utf-8")

    result = run_stub_conversion(source, output, "md", "md")

    assert source.read_text(encoding="utf-8") == "# Title\n\nhello\n"
    assert output.exists()
    assert result.route == "md-to-md"
    assert result.output_size_bytes == output.stat().st_size


def test_convert_cli_writes_output_and_metadata(tmp_path: Path):
    source = tmp_path / "source.md"
    output = tmp_path / "out.docx"
    metadata = tmp_path / "meta.json"
    source.write_text("# Title\n\nhello\n", encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "convert.py"),
        "--input",
        str(source),
        "--from",
        "md",
        "--to",
        "docx",
        "--output",
        str(output),
        "--emit-metadata",
        str(metadata),
        "--preserve-original",
    ]

    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "SHawn-hwp convert" in result.stdout
    assert output.exists()
    assert metadata.exists()

    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["source_format"] == "md"
    assert payload["target_format"] == "docx"
    assert payload["preserve_original"] is True

    if pandoc_available():
        assert "engine=pandoc" in result.stdout
        assert output.read_bytes()[:2] == b"PK"
    else:
        assert "engine=stub" in result.stdout
        assert "converted by SHawn-hwp stub" in output.read_text(encoding="utf-8")


def _run_soffice_pdf_cli(
    source: Path, output: Path, metadata: Path, *, soffice_script: str
) -> subprocess.CompletedProcess[str]:
    bin_dir = source.parent / "bin"
    bin_dir.mkdir()
    soffice = bin_dir / "soffice"
    soffice.write_text("#!/bin/sh\n" + dedent(soffice_script).lstrip(), encoding="utf-8")
    soffice.chmod(0o755)

    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "convert.py"),
            "--input",
            str(source),
            "--from",
            source.suffix[1:],
            "--to",
            "pdf",
            "--output",
            str(output),
            "--emit-metadata",
            str(metadata),
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PATH": str(bin_dir)},
        capture_output=True,
        text=True,
    )


def test_convert_cli_soffice_hwpx_to_pdf_failure_is_actionable(tmp_path: Path):
    source = tmp_path / "synthetic.hwpx"
    output = tmp_path / "synthetic.pdf"
    metadata = tmp_path / "meta.json"
    source.write_bytes(b"synthetic HWPX input")
    original_pdf = b"%PDF-existing output"
    original_metadata = b'{"previous": true}\n'
    output.write_bytes(original_pdf)
    metadata.write_bytes(original_metadata)

    failed = _run_soffice_pdf_cli(
        source,
        output,
        metadata,
        soffice_script="""
            echo 'synthetic HWPX import failure' >&2
            exit 0
        """,
    )

    assert failed.returncode == 1
    assert (
        "error: soffice conversion failed (hwpx -> pdf): synthetic HWPX import failure"
        in failed.stderr
    )
    assert "hwpx -> docx (requires python-docx)" in failed.stderr
    assert "docx -> pdf as separate convert steps" in failed.stderr
    assert "Traceback" not in failed.stderr
    assert failed.stdout == ""
    assert output.read_bytes() == original_pdf
    assert metadata.read_bytes() == original_metadata


def test_convert_cli_soffice_docx_to_pdf_success(tmp_path: Path):
    source = tmp_path / "synthetic.docx"
    output = tmp_path / "published.pdf"
    metadata = tmp_path / "meta.json"
    source.write_bytes(b"synthetic DOCX input")
    output.write_bytes(b"%PDF-existing output")

    ok = _run_soffice_pdf_cli(
        source,
        output,
        metadata,
        soffice_script=r"""
            while [ "$#" -gt 0 ] && [ "$1" != "--outdir" ]; do
                shift
            done
            outdir=${2:?missing output directory}
            input=${3:?missing input path}
            name=${input##*/}
            printf '%s\n' '%PDF-1.4' 'synthetic export' > "$outdir/${name%.*}.pdf"
        """,
    )

    assert ok.returncode == 0, ok.stderr
    assert "engine=soffice" in ok.stdout
    fresh_pdf = b"%PDF-1.4\nsynthetic export\n"
    assert output.read_bytes() == fresh_pdf
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["source_format"] == "docx"
    assert payload["target_format"] == "pdf"
    assert payload["route"] == "docx-to-pdf"
    assert payload["output_path"] == str(output)
    assert payload["output_size_bytes"] == len(fresh_pdf)
