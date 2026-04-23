#!/usr/bin/env python3
"""Compare SHawn-hwp HWP conversion routes on a real HWP fixture."""

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

from shawn_hwp.qa.reporting import generate_qa_result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compare direct/bridge HWP routes")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--outdir", required=True, type=Path)
    return p


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _docx_available() -> bool:
    try:
        import docx  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def main() -> int:
    args = build_parser().parse_args()
    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    direct_md = outdir / "direct.md"
    bridge_hwpx = outdir / "bridge.hwpx"
    bridge_md = outdir / "bridge.md"
    direct_docx = outdir / "direct.docx"
    bridge_docx = outdir / "bridge.docx"

    py = sys.executable
    convert = ROOT / "scripts" / "convert.py"

    _run([py, str(convert), "--input", str(args.input), "--from", "hwp", "--to", "md", "--output", str(direct_md)], ROOT)
    _run([py, str(convert), "--input", str(args.input), "--from", "hwp", "--to", "hwpx", "--output", str(bridge_hwpx)], ROOT)
    _run([py, str(convert), "--input", str(bridge_hwpx), "--from", "hwpx", "--to", "md", "--output", str(bridge_md)], ROOT)

    docx_enabled = _docx_available()
    if docx_enabled:
        _run([py, str(convert), "--input", str(args.input), "--from", "hwp", "--to", "docx", "--output", str(direct_docx)], ROOT)
        _run([py, str(convert), "--input", str(bridge_hwpx), "--from", "hwpx", "--to", "docx", "--output", str(bridge_docx)], ROOT)

    direct_vs_bridge = generate_qa_result(
        source=direct_md,
        candidate=bridge_md,
        source_format="md",
        candidate_format="md",
        label="direct-vs-bridge-md",
    )

    summary = {
        "input": str(args.input),
        "artifacts": {
            "direct_md": str(direct_md),
            "bridge_hwpx": str(bridge_hwpx),
            "bridge_md": str(bridge_md),
            "direct_docx": str(direct_docx) if docx_enabled else None,
            "bridge_docx": str(bridge_docx) if docx_enabled else None,
        },
        "scores": {
            "direct_vs_bridge_md": direct_vs_bridge.to_dict(),
        },
        "docx_enabled": docx_enabled,
        "route_recommendation": "direct" if direct_vs_bridge.comparisons["text_similarity"] < 0.9 else "bridge-or-direct",
    }

    summary_path = outdir / "comparison_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("SHawn-hwp compare_hwp_routes")
    print(f"input={args.input}")
    print(f"summary={summary_path}")
    print(f"direct_vs_bridge_md_score={direct_vs_bridge.weighted_score}/{direct_vs_bridge.max_score}")
    print(f"route_recommendation={summary['route_recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
