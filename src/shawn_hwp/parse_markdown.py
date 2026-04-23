"""Markdown parser helpers for SHawn-hwp DocumentModel."""

from __future__ import annotations

from shawn_hwp.model import DocumentModel


def _is_markdown_table(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    return len(lines) >= 2 and lines[0].startswith("|") and set(lines[1].replace("|", "").replace("-", "").replace(" ", "")) == set()


def parse_markdown(markdown_text: str) -> DocumentModel:
    model = DocumentModel()
    for raw in [part.strip() for part in markdown_text.split("\n\n") if part.strip()]:
        if raw.startswith("# "):
            model.add_heading(raw[2:].strip(), level=1, source_trace="markdown:heading")
        elif _is_markdown_table(raw):
            rows: list[list[str]] = []
            for idx, line in enumerate([ln.strip() for ln in raw.splitlines() if ln.strip()]):
                if idx == 1:
                    continue
                rows.append([cell.strip() for cell in line.strip("|").split("|")])
            model.add_table(rows, source_trace="markdown:table")
        else:
            model.add_paragraph(raw, source_trace="markdown:paragraph")
    return model
