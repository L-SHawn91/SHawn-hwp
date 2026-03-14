#!/usr/bin/env python3
"""Submission packaging entrypoint for SHawn-hwp (draft CLI)."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Assemble review/submission bundle")
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--converted", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--include-roundtrip", type=Path)
    p.add_argument("--include-original", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    print("SHawn-hwp package_submission (draft)")
    print(f"source={args.source}")
    print(f"converted={args.converted}")
    print(f"report={args.report}")
    print(f"outdir={args.outdir}")
    if args.include_roundtrip:
        print(f"include_roundtrip={args.include_roundtrip}")
    print(f"include_original={args.include_original}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
