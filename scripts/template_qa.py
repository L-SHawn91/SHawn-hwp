#!/usr/bin/env python3
"""Compare a generated HWPX candidate against its source template profile."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.template_profile import compare_template_profiles, render_template_qa_markdown, write_template_qa_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run HWPX template-vs-candidate QA")
    parser.add_argument("--template", required=True, type=Path, help="source HWPX template")
    parser.add_argument("--candidate", required=True, type=Path, help="generated HWPX candidate")
    parser.add_argument("--report", type=Path, help="write markdown QA report")
    parser.add_argument("--json", type=Path, help="write machine-readable QA result")
    parser.add_argument("--allow-remaining-slots", action="store_true", help="warn only; do not fail if explicit slots remain")
    parser.add_argument("--warn-table-delta", type=int, default=0)
    parser.add_argument("--warn-image-delta", type=int, default=0)
    parser.add_argument("--warn-section-delta", type=int, default=0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = compare_template_profiles(
        args.template,
        args.candidate,
        warn_table_delta=args.warn_table_delta,
        warn_image_delta=args.warn_image_delta,
        warn_section_delta=args.warn_section_delta,
        fail_if_slot_remains=not args.allow_remaining_slots,
    )
    markdown = render_template_qa_markdown(result)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown, encoding="utf-8")
    if args.json:
        write_template_qa_json(result, args.json)
    print(markdown)
    return 0 if result.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
