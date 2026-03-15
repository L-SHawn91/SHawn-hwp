#!/usr/bin/env python3
"""Batch validation runner for real HWP/HWPX fixtures."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_TARGETS = ["docx", "pdf", "html"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run a batch of validation routes for one real fixture")
    p.add_argument("--fixture", required=True, choices=["real-hwp", "real-hwpx"])
    p.add_argument("--from", dest="source_format", required=True, choices=["hwp", "hwpx"])
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--targets", nargs="*", default=DEFAULT_TARGETS)
    p.add_argument("--notes")
    return p


def main() -> int:
    args = build_parser().parse_args()
    summary: list[dict] = []

    for target in args.targets:
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "validate_real_fixture.py"),
            "--fixture",
            args.fixture,
            "--from",
            args.source_format,
            "--to",
            target,
            "--outdir",
            str(args.outdir),
        ]
        if args.notes:
            cmd.extend(["--notes", args.notes])
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)

        manifest_path = args.outdir / args.fixture / f"{args.source_format}-to-{target}" / "validation_manifest.json"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        summary.append(
            {
                "target": target,
                "qa_score": payload["qa_score"],
                "qa_readiness": payload["qa_readiness"],
                "qa_risks": payload["qa_risks"],
                "manifest": str(manifest_path),
                "stdout": completed.stdout,
            }
        )

    summary_path = args.outdir / args.fixture / f"{args.source_format}-batch-summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("SHawn-hwp real fixture batch validation")
    print(f"fixture={args.fixture}")
    print(f"source_format={args.source_format}")
    print(f"targets={','.join(args.targets)}")
    print(f"summary={summary_path}")
    for row in summary:
        print(f"- {row['target']}: {row['qa_score']} ({row['qa_readiness']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
