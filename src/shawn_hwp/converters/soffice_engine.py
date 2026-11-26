"""LibreOffice/soffice-backed conversion helpers for SHawn-hwp."""

from __future__ import annotations

import os
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


def _run_soffice_convert(input_path: Path, outdir: Path, target_format: str) -> subprocess.CompletedProcess[str]:
    convert_to = SOFFICE_TARGET_MAP.get(target_format, target_format)
    cmd = [
        _soffice_bin(),
        "--headless",
        "--convert-to",
        convert_to,
        "--outdir",
        str(outdir),
        str(input_path),
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def _soffice_failure_detail(completed: subprocess.CompletedProcess[str], *, missing: bool) -> str:
    detail = (completed.stderr or completed.stdout or "").strip()
    if detail:
        return detail.splitlines()[-1].strip()
    if missing:
        return "soffice exited 0 but produced no output file"
    return f"exit status {completed.returncode}"


def _atomic_publish_file(staged: Path, output_path: Path) -> None:
    if output_path.exists() and output_path.is_dir():
        raise SofficeConversionError("output path is a directory")
    if staged.resolve() == output_path.resolve():
        return
    try:
        os.replace(staged, output_path)
    except OSError as exc:
        raise SofficeConversionError(f"failed to publish output: {exc}") from exc


def _publish_pdf_from_staging(staged_pdf: Path, output_path: Path) -> None:
    if not staged_pdf.is_file():
        raise SofficeConversionError("soffice exited 0 but produced no pdf file")
    if staged_pdf.stat().st_size == 0:
        raise SofficeConversionError("soffice produced an empty pdf file")
    if staged_pdf.read_bytes()[:4] != b"%PDF":
        raise SofficeConversionError("soffice produced a non-pdf artifact")
    _atomic_publish_file(staged_pdf, output_path)


def _run_non_pdf_conversion(
    input_path: Path,
    output_path: Path,
    target_format: str,
) -> None:
    """Legacy main (17e8a4b) publish semantics for non-PDF soffice routes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = _run_soffice_convert(input_path, output_path.parent, target_format)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            completed.args,
            output=completed.stdout,
            stderr=completed.stderr,
        )

    produced = output_path.parent / f"{input_path.stem}.{target_format}"
    if produced.exists() and produced != output_path:
        produced.replace(output_path)


def _run_pdf_conversion(input_path: Path, output_path: Path) -> None:
    if input_path.resolve() == output_path.resolve():
        raise SofficeConversionError("output path must not be the input file")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_path.parent, prefix="shawn-hwp-soffice-") as staging_name:
        staging_dir = Path(staging_name)
        completed = _run_soffice_convert(input_path, staging_dir, "pdf")
        if completed.returncode != 0:
            raise subprocess.CalledProcessError(
                completed.returncode,
                completed.args,
                output=completed.stdout,
                stderr=completed.stderr,
            )

        produced = _expected_staged_output(staging_dir, input_path, "pdf")
        if not produced.is_file():
            raise SofficeConversionError(_soffice_failure_detail(completed, missing=True))
        _publish_pdf_from_staging(produced, output_path)


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

    if target_format == "pdf":
        _run_pdf_conversion(input_path, output_path)
    else:
        _run_non_pdf_conversion(input_path, output_path, target_format)

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