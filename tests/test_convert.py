from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
