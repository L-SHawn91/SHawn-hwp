"""HWPX writer helpers for SHawn-hwp DocumentModel."""

from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from shawn_hwp.model import DocumentModel, InlineRun


def default_reference_hwpx() -> Path:
    candidate = Path("/tmp/pypandoc-hwpx/pypandoc_hwpx/blank.hwpx")
    if candidate.exists():
        return candidate
    repo_fallback = Path(__file__).resolve().parents[2] / "data" / "reference" / "blank.hwpx"
    return repo_fallback


def _table_to_hwpx(rows: list[list[str]]) -> str:
    row_xml: list[str] = []
    for row in rows:
        cell_xml = "".join(
            f'<hp:tc><hp:p><hp:run><hp:t>{escape(cell)}</hp:t></hp:run></hp:p></hp:tc>'
            for cell in row
        )
        row_xml.append(f"<hp:tr>{cell_xml}</hp:tr>")
    return f"<hp:tbl>{''.join(row_xml)}</hp:tbl>"


def _render_runs(runs: list[InlineRun], fallback_text: str) -> str:
    if not runs:
        return f'<hp:run><hp:t>{escape(fallback_text)}</hp:t></hp:run>'
    parts: list[str] = []
    for run in runs:
        attrs: list[str] = []
        if run.bold:
            attrs.append('charPrIDRef="bold"')
        if run.italic:
            attrs.append('style-name="italic"')
        if run.underline:
            attrs.append('style-name="underline"')
        attr_text = f" {' '.join(attrs)}" if attrs else ""
        parts.append(f'<hp:run{attr_text}><hp:t>{escape(run.text)}</hp:t></hp:run>')
    return ''.join(parts)


def render_hwpx_section_xml(model: DocumentModel) -> str:
    xml_blocks: list[str] = []
    for block in model.blocks:
        if block.kind == "table":
            xml_blocks.append(_table_to_hwpx(block.rows))
            continue
        style_attr = ' style-name="Title"' if block.kind == "heading" else ""
        runs_xml = _render_runs(block.runs, block.text)
        xml_blocks.append(
            f'<hp:p{style_attr}>{runs_xml}</hp:p>'
        )
    inner = "\n  ".join(xml_blocks)
    return (
        '<hp:section xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">\n'
        f'  {inner}\n'
        '</hp:section>\n'
    )


def write_hwpx(model: DocumentModel, output_path: Path, reference_path: Path | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    section_xml = render_hwpx_section_xml(model)
    reference = reference_path or default_reference_hwpx()

    if reference.exists() and zipfile.is_zipfile(reference):
        with zipfile.ZipFile(reference, "r") as ref_zip:
            with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
                wrote_section = False
                wrote_mimetype = False
                for item in ref_zip.infolist():
                    data = ref_zip.read(item.filename)
                    if item.filename == "Contents/section0.xml":
                        out_zip.writestr(item.filename, section_xml)
                        wrote_section = True
                    else:
                        out_zip.writestr(item, data)
                    if item.filename == "mimetype":
                        wrote_mimetype = True
                if not wrote_section:
                    out_zip.writestr("Contents/section0.xml", section_xml)
                if not wrote_mimetype:
                    out_zip.writestr("mimetype", "application/hwp+zip")
        return

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/hwp+zip")
        zf.writestr("Contents/section0.xml", section_xml)
        zf.writestr("version.xml", "<version app='SHawn-hwp' format='hwpx' version='0.1'/>\n")
