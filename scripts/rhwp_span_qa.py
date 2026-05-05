#!/usr/bin/env python3
"""Summarize rhwp-derived table span metadata in a SHawn-hwp DocumentModel JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.model import Block, DocumentModel, InlineRun
from shawn_hwp.qa.rhwp_span import build_span_qa_result, render_span_qa_markdown


def _block_from_payload(payload: dict) -> Block:
    runs = [InlineRun(**run) for run in payload.get("runs", [])]
    return Block(
        kind=payload.get("kind", "paragraph"),
        text=payload.get("text", ""),
        level=int(payload.get("level", 0) or 0),
        rows=payload.get("rows", []) or [],
        cell_spans=payload.get("cell_spans", []) or [],
        runs=runs,
        source_trace=payload.get("source_trace"),
    )


def load_model_json(path: Path) -> DocumentModel:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DocumentModel(
        blocks=[_block_from_payload(block) for block in payload.get("blocks", [])],
        metadata=payload.get("metadata", {}) or {},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate rhwp table span QA from SHawn-hwp model JSON")
    parser.add_argument("--model-json", required=True, type=Path, help="JSON emitted by scripts/rhwp_to_model.py")
    parser.add_argument("--report", required=True, type=Path, help="write markdown span QA report")
    parser.add_argument("--json", dest="json_path", type=Path, help="write machine-readable span QA result")
    parser.add_argument("--label")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    model = load_model_json(args.model_json)
    result = build_span_qa_result(model, label=args.label)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_span_qa_markdown(result), encoding="utf-8")
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("SHawn-hwp rhwp_span_qa")
    print(f"model_json={args.model_json}")
    print(f"span_tables={result.span_tables}/{result.total_tables}")
    print(f"total_spans={result.total_spans}")
    print(f"low_confidence_tables={result.low_confidence_table_count}")
    print(f"report={args.report}")
    if args.json_path:
        print(f"json={args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
