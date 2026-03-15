"""Pandoc-backed conversion helpers for SHawn-hwp."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from shawn_hwp.converters.stub import ConversionResult
from shawn_hwp.converters.strategy_router import choose_route


PANDOC_FORMAT_MAP = {
    "md": "markdown",
    "html": "html",
    "docx": "docx",
}


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def run_pandoc_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    chosen_route = route or choose_route(source_format, target_format)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pandoc_source = PANDOC_FORMAT_MAP.get(source_format, source_format)
    pandoc_target = PANDOC_FORMAT_MAP.get(target_format, target_format)

    cmd = [
        shutil.which("pandoc") or "pandoc",
        str(input_path),
        "-f",
        pandoc_source,
        "-t",
        pandoc_target,
        "-o",
        str(output_path),
    ]
    if template and target_format == "docx":
        cmd.extend(["--reference-doc", str(template)])

    subprocess.run(cmd, check=True, capture_output=True, text=True)

    return ConversionResult(
        input_path=str(input_path),
        output_path=str(output_path),
        source_format=source_format,
        target_format=target_format,
        route=chosen_route,
        preserve_original=preserve_original,
        template=str(template) if template else None,
        input_size_bytes=input_path.stat().st_size,
        output_size_bytes=output_path.stat().st_size,
    )
