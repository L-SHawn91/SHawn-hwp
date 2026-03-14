#!/usr/bin/env python3
"""QA report entrypoint for SHawn-hwp (draft CLI)."""

from __future__ import annotations

import argparse
from pathlib import Path


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
    print("SHawn-hwp qa_report (draft)")
    print(f"source={args.source}")
    print(f"candidate={args.candidate}")
    print(f"report={args.report}")
    if args.json_path:
        print(f"json={args.json_path}")
    if args.label:
        print(f"label={args.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
