#!/usr/bin/env python3
"""Benchmark entrypoint for SHawn-hwp."""

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


FIXTURE_ROOT = ROOT / "data" / "fixtures"


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


def _fixture_dir(name: str) -> Path:
    return FIXTURE_ROOT / name


def _fixture_source_path(fixture_dir: Path, source_format: str) -> Path:
    return fixture_dir / f"source.{source_format}"


def _fixture_candidate_path(fixture_dir: Path, target_format: str) -> Path:
    candidate = fixture_dir / f"candidate.{target_format}"
    if candidate.exists():
        return candidate
    return fixture_dir / f"source.{target_format}"


def main() -> int:
    args = build_parser().parse_args()
    fixture_dir = _fixture_dir(args.fixture)
    source = _fixture_source_path(fixture_dir, args.source_format)
    candidate = _fixture_candidate_path(fixture_dir, args.target_format)

    if not fixture_dir.exists():
        raise SystemExit(f"fixture not found: {fixture_dir}")
    if not source.exists():
        raise SystemExit(f"fixture source not found: {source}")
    if not candidate.exists():
        raise SystemExit(f"fixture candidate not found: {candidate}")

    run_dir = args.outdir / args.fixture / args.candidate
    run_dir.mkdir(parents=True, exist_ok=True)

    report_path = run_dir / "qa_report.md"
    json_path = run_dir / "qa_report.json"
    manifest_path = run_dir / "benchmark_manifest.json"

    result = generate_qa_result(
        source=source,
        candidate=candidate,
        source_format=args.source_format,
        candidate_format=args.target_format,
        label=f"{args.fixture}:{args.candidate}",
    )

    report_path.write_text(render_markdown_report(result), encoding="utf-8")
    manifest = {
        "fixture": args.fixture,
        "candidate": args.candidate,
        "source_format": args.source_format,
        "target_format": args.target_format,
        "roundtrip": args.roundtrip,
        "notes": args.notes,
        "source": str(source),
        "candidate_path": str(candidate),
        "qa_report": str(report_path),
        "qa_json": str(json_path),
        "score": result.weighted_score,
        "readiness": result.readiness,
        "risk_categories": result.risk_categories,
    }
    json_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("SHawn-hwp benchmark")
    print(f"fixture={args.fixture}")
    print(f"candidate={args.candidate}")
    print(f"score={result.weighted_score}/{result.max_score}")
    print(f"readiness={result.readiness}")
    print(f"report={report_path}")
    print(f"json={json_path}")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
