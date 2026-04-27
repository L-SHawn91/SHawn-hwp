#!/usr/bin/env python3
"""Validate structured research proposal JSON before HWPX template injection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.proposal import render_validation_markdown, validate_proposal_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate SHawn-hwp research proposal JSON")
    parser.add_argument("--input", required=True, type=Path, help="proposal JSON input")
    parser.add_argument("--report", type=Path, help="write markdown validation report")
    parser.add_argument("--json", type=Path, help="write machine-readable validation result")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = validate_proposal_json(args.input)
    markdown = render_validation_markdown(result)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown, encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    print(markdown)
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
