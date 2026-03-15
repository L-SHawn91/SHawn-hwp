#!/usr/bin/env python3
"""Conversion entrypoint for SHawn-hwp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.converters.pandoc_engine import pandoc_available, run_pandoc_conversion
from shawn_hwp.converters.soffice_engine import soffice_available, run_soffice_conversion
from shawn_hwp.converters.stub import run_stub_conversion


VALID_FORMATS = ["hwp", "hwpx", "docx", "md", "pdf", "html"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run a single SHawn-hwp conversion route")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--from", dest="source_format", required=True, choices=VALID_FORMATS)
    p.add_argument("--to", dest="target_format", required=True, choices=VALID_FORMATS)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--route")
    p.add_argument("--template", type=Path)
    p.add_argument("--preserve-original", action="store_true")
    p.add_argument("--emit-metadata", type=Path)
    return p


def main() -> int:
    args = build_parser().parse_args()

    use_pandoc = (
        pandoc_available()
        and args.source_format in {"md", "html", "docx"}
        and args.target_format in {"md", "html", "docx"}
    )
    use_soffice = (
        soffice_available()
        and args.source_format in {"docx", "hwp", "hwpx"}
        and args.target_format in {"pdf", "html", "docx"}
    )

    if use_pandoc:
        result = run_pandoc_conversion(
            input_path=args.input,
            output_path=args.output,
            source_format=args.source_format,
            target_format=args.target_format,
            route=args.route,
            template=args.template,
            preserve_original=args.preserve_original,
        )
        engine = "pandoc"
    elif use_soffice:
        result = run_soffice_conversion(
            input_path=args.input,
            output_path=args.output,
            source_format=args.source_format,
            target_format=args.target_format,
            route=args.route,
            template=args.template,
            preserve_original=args.preserve_original,
        )
        engine = "soffice"
    else:
        result = run_stub_conversion(
            input_path=args.input,
            output_path=args.output,
            source_format=args.source_format,
            target_format=args.target_format,
            route=args.route,
            template=args.template,
            preserve_original=args.preserve_original,
        )
        engine = "stub"

    if args.emit_metadata:
        args.emit_metadata.parent.mkdir(parents=True, exist_ok=True)
        args.emit_metadata.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print("SHawn-hwp convert")
    print(f"engine={engine}")
    print(f"input={args.input}")
    print(f"source_format={args.source_format}")
    print(f"target_format={args.target_format}")
    print(f"route={result.route}")
    print(f"output={args.output}")
    if args.template:
        print(f"template={args.template}")
    if args.emit_metadata:
        print(f"emit_metadata={args.emit_metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
