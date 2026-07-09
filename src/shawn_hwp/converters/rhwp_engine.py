"""Optional rhwp/@rhwp-core integration for real HWP conversion routes.

The npm package is installed under ``external/rhwp-core`` by
``npm install --prefix external/rhwp-core @rhwp/core``.  SHawn-hwp uses rhwp as
an optional backend for SVG rendering and layout-model based HWP -> MD/DOCX
conversion routes.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from shawn_hwp.converters.stub import ConversionResult


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _probe_script() -> Path:
    return _repo_root() / "scripts" / "rhwp_probe.mjs"


def _core_dir() -> Path:
    return _repo_root() / "external" / "rhwp-core" / "node_modules" / "@rhwp" / "core"


def rhwp_core_available() -> bool:
    return (
        shutil.which("node") is not None
        and _probe_script().exists()
        and (_core_dir() / "rhwp.js").exists()
        and (_core_dir() / "rhwp_bg.wasm").exists()
    )


def _run_probe(args: list[str]) -> dict[str, Any]:
    if not rhwp_core_available():
        raise RuntimeError(
            "rhwp/@rhwp-core is not available; run "
            "`npm install --prefix external/rhwp-core @rhwp/core`"
        )

    try:
        proc = subprocess.run(
            ["node", str(_probe_script()), *args],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or str(exc)
        raise RuntimeError(f"rhwp_probe.mjs failed with exit code {exc.returncode}: {detail}") from exc
    return json.loads(proc.stdout)


def probe_hwp_with_rhwp(input_path: Path) -> dict[str, Any]:
    return _run_probe(["info", "--input", str(input_path)])


def export_hwp_svg_with_rhwp(input_path: Path, output_dir: Path, pages: str | None = None) -> dict[str, Any]:
    args = ["export-svg", "--input", str(input_path), "--outdir", str(output_dir)]
    if pages:
        args.extend(["--pages", pages])
    return _run_probe(args)


def export_hwp_layout_with_rhwp(input_path: Path, pages: str | None = None) -> dict[str, Any]:
    args = ["export-layout", "--input", str(input_path)]
    if pages:
        args.extend(["--pages", pages])
    return _run_probe(args)


def run_hwp_to_svg_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    if source_format != "hwp" or target_format != "svg":
        raise ValueError("run_hwp_to_svg_conversion only supports hwp -> svg")

    payload = export_hwp_svg_with_rhwp(input_path, output_path)
    output_size = sum(Path(path).stat().st_size for path in payload.get("outputs", []))
    return ConversionResult(
        input_path=str(input_path),
        output_path=str(output_path),
        source_format=source_format,
        target_format=target_format,
        route=route or "rhwp-svg-render",
        preserve_original=preserve_original,
        template=str(template) if template else None,
        input_size_bytes=input_path.stat().st_size,
        output_size_bytes=output_size,
    )


def run_hwp_to_md_layout_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    if source_format != "hwp" or target_format != "md":
        raise ValueError("run_hwp_to_md_layout_conversion only supports hwp -> md")

    from shawn_hwp.io_markdown import render_markdown
    from shawn_hwp.rhwp_adapter import parse_hwp_with_rhwp

    output_path.parent.mkdir(parents=True, exist_ok=True)
    model = parse_hwp_with_rhwp(input_path)
    output_path.write_text(render_markdown(model), encoding="utf-8")
    return ConversionResult(
        input_path=str(input_path),
        output_path=str(output_path),
        source_format=source_format,
        target_format=target_format,
        route="rhwp-layout-to-md" if route in {None, "rhwp-layout"} else route,
        preserve_original=preserve_original,
        template=str(template) if template else None,
        input_size_bytes=input_path.stat().st_size,
        output_size_bytes=output_path.stat().st_size,
    )


def run_hwp_to_docx_layout_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    if source_format != "hwp" or target_format != "docx":
        raise ValueError("run_hwp_to_docx_layout_conversion only supports hwp -> docx")

    from shawn_hwp.io_docx import write_docx
    from shawn_hwp.rhwp_adapter import parse_hwp_with_rhwp

    output_path.parent.mkdir(parents=True, exist_ok=True)
    model = parse_hwp_with_rhwp(input_path)
    write_docx(model, output_path)
    return ConversionResult(
        input_path=str(input_path),
        output_path=str(output_path),
        source_format=source_format,
        target_format=target_format,
        route="rhwp-layout-to-docx" if route in {None, "rhwp-layout"} else route,
        preserve_original=preserve_original,
        template=str(template) if template else None,
        input_size_bytes=input_path.stat().st_size,
        output_size_bytes=output_path.stat().st_size,
    )
