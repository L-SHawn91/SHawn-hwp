#!/usr/bin/env python3
"""Export rhwp-derived SHawn-hwp DocumentModel artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.io_markdown import render_markdown
from shawn_hwp.rhwp_adapter import parse_hwp_with_rhwp


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert HWP through rhwp layout JSON into SHawn-hwp DocumentModel")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--model-json", required=True, type=Path)
    p.add_argument("--markdown", type=Path)
    p.add_argument("--pages", help="Comma-separated 0-based page indexes")
    return p


def main() -> int:
    args = build_parser().parse_args()
    model = parse_hwp_with_rhwp(args.input, pages=args.pages)
    args.model_json.parent.mkdir(parents=True, exist_ok=True)
    args.model_json.write_text(json.dumps(asdict(model), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(model), encoding="utf-8")
    print("SHawn-hwp rhwp_to_model")
    print(f"input={args.input}")
    print(f"blocks={len(model.blocks)}")
    print(f"model_json={args.model_json}")
    if args.markdown:
        print(f"markdown={args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
