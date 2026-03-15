#!/usr/bin/env python3
"""QA report entrypoint for SHawn-hwp."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.qa.reporting import generate_qa_result, render_markdown_report


VALID_FORMATS = ["hwp", "hwpx", "docx", "md", "pdf", "html"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Score source/output pair and emit QA summary")
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--source-format", required=True, choices=VALID_FORMATS)
    p.add_argument("--candidate-format", required=True, choices=VALID_FORMATS)
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--json", dest="json_path", type=Path)
    p.add_argument("--label")
    return p


def main() -> int:
    args = build_parser().parse_args()
    result = generate_qa_result(
        source=args.source,
        candidate=args.candidate,
        source_format=args.source_format,
        candidate_format=args.candidate_format,
        label=args.label,
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_markdown_report(result), encoding="utf-8")

    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"SHawn-hwp qa_report: {result.weighted_score}/{result.max_score}")
    print(f"readiness={result.readiness}")
    print(f"report={args.report}")
    if args.json_path:
        print(f"json={args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
