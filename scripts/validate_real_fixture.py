#!/usr/bin/env python3
"""Validate real HWP/HWPX fixtures through selected routes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.qa.reporting import generate_qa_result, render_markdown_report

FIXTURE_ROOT = ROOT / "data" / "fixtures"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate a real HWP/HWPX fixture across one route")
    p.add_argument("--fixture", required=True, choices=["real-hwp", "real-hwpx"])
    p.add_argument("--from", dest="source_format", required=True, choices=["hwp", "hwpx"])
    p.add_argument("--to", dest="target_format", required=True, choices=["docx", "pdf", "html"])
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--notes")
    return p


def main() -> int:
    args = build_parser().parse_args()
    fixture_dir = FIXTURE_ROOT / args.fixture
    source = fixture_dir / f"source.{args.source_format}"
    if not source.exists():
        raise SystemExit(f"real fixture source not found: {source}")

    run_dir = args.outdir / args.fixture / f"{args.source_format}-to-{args.target_format}"
    run_dir.mkdir(parents=True, exist_ok=True)
    converted = run_dir / f"converted.{args.target_format}"
    metadata = run_dir / "convert_metadata.json"
    qa_md = run_dir / "qa_report.md"
    qa_json = run_dir / "qa_report.json"
    manifest = run_dir / "validation_manifest.json"

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "convert.py"),
        "--input",
        str(source),
        "--from",
        args.source_format,
        "--to",
        args.target_format,
        "--output",
        str(converted),
        "--emit-metadata",
        str(metadata),
        "--preserve-original",
    ]
    completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)

    result = generate_qa_result(
        source=source,
        candidate=converted,
        source_format=args.source_format,
        candidate_format=args.target_format,
        label=f"{args.fixture}:{args.source_format}-to-{args.target_format}",
    )
    qa_md.write_text(render_markdown_report(result), encoding="utf-8")
    qa_json.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    convert_payload = json.loads(metadata.read_text(encoding="utf-8"))
    manifest_payload = {
        "fixture": args.fixture,
        "source": str(source),
        "source_format": args.source_format,
        "target_format": args.target_format,
        "converted": str(converted),
        "convert_metadata": convert_payload,
        "qa_score": result.weighted_score,
        "qa_readiness": result.readiness,
        "qa_risks": result.risk_categories,
        "notes": args.notes,
        "convert_stdout": completed.stdout,
    }
    manifest.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("SHawn-hwp real fixture validation")
    print(f"fixture={args.fixture}")
    print(f"route={args.source_format}-to-{args.target_format}")
    print(f"converted={converted}")
    print(f"qa_score={result.weighted_score}/{result.max_score}")
    print(f"qa_readiness={result.readiness}")
    print(f"manifest={manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
