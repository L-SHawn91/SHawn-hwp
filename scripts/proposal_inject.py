#!/usr/bin/env python3
"""Inject validated proposal JSON into explicit HWPX template slots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.proposal import validate_proposal_json
from shawn_hwp.template_profile import inject_payload_into_hwpx_template


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inject proposal JSON into explicit HWPX template slots")
    parser.add_argument("--template", required=True, type=Path, help="HWPX template containing {{slot}} markers")
    parser.add_argument("--proposal", required=True, type=Path, help="validated proposal JSON")
    parser.add_argument("--output", required=True, type=Path, help="generated HWPX derivative")
    parser.add_argument("--allow-invalid", action="store_true", help="inject even if proposal validation fails")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    validation = validate_proposal_json(args.proposal)
    if not validation.valid and not args.allow_invalid:
        print("proposal validation failed; use --allow-invalid to force injection", file=sys.stderr)
        for issue in validation.issues:
            print(f"{issue.level} {issue.code} {issue.location}: {issue.message}", file=sys.stderr)
        return 2

    import json

    payload = json.loads(args.proposal.read_text(encoding="utf-8"))
    profile = inject_payload_into_hwpx_template(args.template, payload, args.output)
    print(
        "proposal injected: "
        f"template={args.template} "
        f"slots={profile.layout_baseline.slot_count} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
