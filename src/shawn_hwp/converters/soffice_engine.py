"""LibreOffice/soffice-backed conversion helpers for SHawn-hwp."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from shawn_hwp.converters.stub import ConversionResult
from shawn_hwp.converters.strategy_router import choose_route


SOFFICE_TARGET_MAP = {
    "pdf": "pdf",
    "html": "html",
    "docx": "docx",
}


def soffice_available() -> bool:
    return shutil.which("soffice") is not None or shutil.which("libreoffice") is not None


def _soffice_bin() -> str:
    return shutil.which("soffice") or shutil.which("libreoffice") or "soffice"


def run_soffice_conversion(
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

    convert_to = SOFFICE_TARGET_MAP.get(target_format, target_format)
    cmd = [
        _soffice_bin(),
        "--headless",
        "--convert-to",
        convert_to,
        "--outdir",
        str(output_path.parent),
        str(input_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    produced = output_path.parent / f"{input_path.stem}.{target_format}"
    if produced.exists() and produced != output_path:
        produced.replace(output_path)

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
