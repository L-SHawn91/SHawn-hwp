"""DOCX writer helpers for SHawn-hwp DocumentModel."""

from __future__ import annotations

from pathlib import Path

from shawn_hwp.model import DocumentModel


def _write_runs(paragraph, block) -> None:
    if block.runs:
        for run_spec in block.runs:
            run = paragraph.add_run(run_spec.text)
            run.bold = run_spec.bold
            run.italic = run_spec.italic
            run.underline = run_spec.underline
    else:
        paragraph.add_run(block.text)


def write_docx(model: DocumentModel, output_path: Path) -> None:
    from docx import Document

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    for block in model.blocks:
        if block.kind == "heading":
            level = max(1, min(block.level or 1, 9))
            paragraph = document.add_heading("", level=level)
            _write_runs(paragraph, block)
        elif block.kind == "paragraph":
            paragraph = document.add_paragraph("")
            _write_runs(paragraph, block)
        elif block.kind == "table":
            rows = block.rows
            if not rows:
                continue
            width = max(len(r) for r in rows)
            table = document.add_table(rows=len(rows), cols=width)
            for r_idx, row in enumerate(rows):
                for c_idx in range(width):
                    table.cell(r_idx, c_idx).text = row[c_idx] if c_idx < len(row) else ""
    document.save(output_path)
