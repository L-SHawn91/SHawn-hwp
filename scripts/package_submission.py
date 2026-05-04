#!/usr/bin/env python3
"""Assemble a review/submission bundle for SHawn-hwp outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _copy_role(path: Path, outdir: Path, role: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {role} file: {path}")
    safe_name = f"{role}__{path.name}"
    destination = outdir / safe_name
    shutil.copy2(path, destination)
    return {
        "role": role,
        "source_path": str(path),
        "bundle_path": safe_name,
        "size_bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Assemble review/submission bundle")
    p.add_argument("--source", required=True, type=Path, help="source draft or template")
    p.add_argument("--converted", required=True, type=Path, help="generated candidate file")
    p.add_argument("--report", required=True, type=Path, help="QA/validation report")
    p.add_argument("--outdir", required=True, type=Path, help="bundle output directory")
    p.add_argument("--include-roundtrip", type=Path, help="optional round-trip output")
    p.add_argument("--include-original", action="store_true", help="copy the source/original into the bundle")
    p.add_argument("--manifest-name", default="manifest.json", help="manifest filename inside outdir")
    return p


def main() -> int:
    args = build_parser().parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    files: list[dict[str, Any]] = []
    if args.include_original:
        files.append(_copy_role(args.source, args.outdir, "original"))
    else:
        if not args.source.exists():
            raise FileNotFoundError(f"Missing source file: {args.source}")
    files.append(_copy_role(args.converted, args.outdir, "candidate"))
    files.append(_copy_role(args.report, args.outdir, "report"))
    if args.include_roundtrip:
        files.append(_copy_role(args.include_roundtrip, args.outdir, "roundtrip"))

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(args.source),
        "include_original": args.include_original,
        "file_count": len(files),
        "files": files,
        "submission_note": "Bundle is review-ready, not automatically submission-ready; final visual inspection is still required.",
    }
    manifest_path = args.outdir / args.manifest_name
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("SHawn-hwp package_submission")
    print(f"outdir={args.outdir}")
    print(f"manifest={manifest_path}")
    print(f"file_count={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
