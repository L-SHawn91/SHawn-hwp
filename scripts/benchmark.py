#!/usr/bin/env python3
"""Benchmark entrypoint for SHawn-hwp (draft CLI)."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run benchmark fixture(s) against candidate route(s)")
    p.add_argument("--fixture", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--from", dest="source_format", required=True)
    p.add_argument("--to", dest="target_format", required=True)
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--roundtrip", action="store_true")
    p.add_argument("--notes")
    return p


def main() -> int:
    args = build_parser().parse_args()
    print("SHawn-hwp benchmark (draft)")
    print(f"fixture={args.fixture}")
    print(f"candidate={args.candidate}")
    print(f"source_format={args.source_format}")
    print(f"target_format={args.target_format}")
    print(f"outdir={args.outdir}")
    print(f"roundtrip={args.roundtrip}")
    if args.notes:
        print(f"notes={args.notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
