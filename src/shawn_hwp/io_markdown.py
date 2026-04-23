"""Markdown writer helpers for SHawn-hwp DocumentModel."""

from __future__ import annotations

from shawn_hwp.model import DocumentModel


def render_markdown(model: DocumentModel) -> str:
    blocks_out: list[str] = []
    for block in model.blocks:
        if block.kind == "heading":
            level = max(1, block.level or 1)
            blocks_out.append(f"{'#' * level} {block.text.strip()}")
        elif block.kind == "paragraph":
            blocks_out.append(block.text.strip())
        elif block.kind == "table":
            rows = block.rows
            if not rows:
                continue
            width = max(len(r) for r in rows)
            normalized = [r + [""] * (width - len(r)) for r in rows]
            header = "| " + " | ".join(normalized[0]) + " |"
            divider = "| " + " | ".join(["---"] * width) + " |"
            body = ["| " + " | ".join(r) + " |" for r in normalized[1:]]
            blocks_out.append("\n".join([header, divider, *body]))
    cleaned = [p for p in blocks_out if p.strip()]
    return "\n\n".join(cleaned).strip() + ("\n" if cleaned else "")
