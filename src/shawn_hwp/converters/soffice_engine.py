"""LibreOffice/soffice-backed conversion helpers for SHawn-hwp."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from shawn_hwp.converters.stub import ConversionResult
from shawn_hwp.converters.strategy_router import choose_route


SOFFICE_TARGET_MAP = {
    "pdf": "pdf",
    "html": "html",
    "docx": "docx",
}


class SofficeConversionError(RuntimeError):
    """Raised when soffice does not publish a usable output artifact."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def soffice_available() -> bool:
    return shutil.which("soffice") is not None or shutil.which("libreoffice") is not None


def _soffice_bin() -> str:
    return shutil.which("soffice") or shutil.which("libreoffice") or "soffice"


def _expected_staged_output(staging_dir: Path, input_path: Path, target_format: str) -> Path:
    return staging_dir / f"{input_path.stem}.{target_format}"


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
    with tempfile.TemporaryDirectory(prefix="shawn-hwp-soffice-") as staging_name:
        staging_dir = Path(staging_name)
        cmd = [
            _soffice_bin(),
            "--headless",
            "--convert-to",
            convert_to,
            "--outdir",
            str(staging_dir),
            str(input_path),
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True)

        if completed.returncode != 0:
            raise subprocess.CalledProcessError(
                completed.returncode,
                cmd,
                output=completed.stdout,
                stderr=completed.stderr,
            )

        produced = _expected_staged_output(staging_dir, input_path, target_format)
        if not produced.is_file():
            detail = (completed.stderr or completed.stdout or "").strip()
            tail = detail.splitlines()[-1].strip() if detail else "soffice exited 0 but produced no output file"
            raise SofficeConversionError(tail)

        shutil.copy2(produced, output_path)

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