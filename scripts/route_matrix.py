#!/usr/bin/env python3
"""Route capability reporter for SHawn-hwp."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROUTES = [
    ("hwp", "docx"),
    ("hwp", "md"),
    ("hwp", "hwpx"),
    ("hwpx", "docx"),
    ("hwpx", "md"),
    ("hwpx", "hwp"),
    ("docx", "hwpx"),
    ("docx", "hwp"),
    ("md", "hwpx"),
    ("md", "hwp"),
]


def detect_engine(source: str, target: str) -> str:
    has_pandoc = shutil.which("pandoc") is not None
    has_soffice = shutil.which("soffice") is not None or shutil.which("libreoffice") is not None

    if has_pandoc and source in {"md", "html", "docx"} and target in {"md", "html", "docx"}:
        return "pandoc"
    if has_soffice and source in {"docx", "hwp", "hwpx"} and target in {"pdf", "html", "docx"}:
        return "soffice"
    if has_soffice and source == "docx" and target == "hwpx":
        return "soffice-probe"
    if has_soffice and source in {"hwp", "hwpx"} and target in {"docx"}:
        return "soffice-probe"
    return "unmapped"


def main() -> int:
    rows = []
    for source, target in ROUTES:
        rows.append({
            "source": source,
            "target": target,
            "engine": detect_engine(source, target),
        })
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
