#!/usr/bin/env python3
"""Conversion entrypoint for SHawn-hwp (draft CLI)."""

from __future__ import annotations

import argparse
from pathlib import Path

from shawn_hwp.converters.strategy_router import choose_route


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
    route = args.route or choose_route(args.source_format, args.target_format)
    print("SHawn-hwp convert (draft)")
    print(f"input={args.input}")
    print(f"source_format={args.source_format}")
    print(f"target_format={args.target_format}")
    print(f"route={route}")
    print(f"output={args.output}")
    if args.template:
        print(f"template={args.template}")
    if args.emit_metadata:
        print(f"emit_metadata={args.emit_metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
