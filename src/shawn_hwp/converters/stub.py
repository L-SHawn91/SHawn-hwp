"""Minimal conversion stub for SHawn-hwp MVP."""

from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from shawn_hwp.converters.strategy_router import choose_route


@dataclass
class ConversionResult:
    input_path: str
    output_path: str
    source_format: str
    target_format: str
    route: str
    preserve_original: bool
    template: str | None
    input_size_bytes: int
    output_size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_stub_conversion(
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

    text = input_path.read_text(encoding="utf-8", errors="ignore")
    converted_text = text
    if source_format != target_format:
        converted_text += f"\n\n<!-- converted by SHawn-hwp stub: {chosen_route} -->\n"
    output_path.write_text(converted_text, encoding="utf-8")

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
