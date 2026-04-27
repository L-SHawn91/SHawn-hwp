#!/usr/bin/env python3
"""Extract a SHawn-hwp template profile from an HWPX template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.template_profile import extract_template_profile, write_profile_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract a template profile from an HWPX file")
    parser.add_argument("--template", required=True, type=Path, help="official/reference HWPX template")
    parser.add_argument("--output", required=True, type=Path, help="profile JSON output")
    parser.add_argument("--template-id", help="stable template id")
    parser.add_argument("--display-name", help="human-readable display name")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile = extract_template_profile(args.template, template_id=args.template_id, display_name=args.display_name)
    write_profile_json(profile, args.output)
    print(
        "profile extracted: "
        f"template_id={profile.template_id} "
        f"sections={profile.layout_baseline.section_count} "
        f"tables={profile.layout_baseline.table_count} "
        f"slots={profile.layout_baseline.slot_count} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
