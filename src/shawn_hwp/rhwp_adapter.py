"""Adapter from rhwp layout JSON into SHawn-hwp's DocumentModel.

This is intentionally a thin adapter layer: rhwp remains an external parser /
renderer, while SHawn-hwp owns the canonical conversion model and writers.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from shawn_hwp.converters.rhwp_engine import export_hwp_layout_with_rhwp
from shawn_hwp.model import DocumentModel, InlineRun


def _clean_text(text: str) -> str:
    text = text.replace("\u000b", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _heading_level(text: str, runs: list[InlineRun]) -> int | None:
    stripped = text.strip()
    if not stripped:
        return None
    if re.match(r"^\d+\.\s+", stripped):
        return 1
    if re.match(r"^\d+\)\s+", stripped) or re.match(r"^\(\d+\)\s+", stripped):
        return 2
    if re.match(r"^[가-힣]\.\s+", stripped) or re.match(r"^[가-힣]-\d+\.\s+", stripped):
        return 3
    if re.match(r"^[가-힣]\)\s+", stripped):
        return 4
    if runs and all(run.bold for run in runs if run.text.strip()) and len(stripped) <= 80:
        return 2
    return None


def _bbox_y(node: dict[str, Any]) -> float:
    bbox = node.get("bbox") or {}
    try:
        return float(bbox.get("y", 0))
    except (TypeError, ValueError):
        return 0.0


def _run_to_inline(run: dict[str, Any]) -> InlineRun:
    return InlineRun(
        text=str(run.get("text", "")),
        bold=bool(run.get("bold", False)),
        italic=bool(run.get("italic", False)),
        underline=bool(run.get("underline", False)),
        style_hint=f"font={run.get('fontFamily')} size={run.get('fontSize')} color={run.get('textColor')}",
        source_trace=(
            f"rhwp:p{run.get('pageIndex')} s{run.get('secIdx')} pi{run.get('paraIdx')} "
            f"cell={run.get('cellIdx')} y={run.get('y')}"
        ),
    )


def _walk_render_nodes(node: Any, node_type: str) -> list[dict[str, Any]]:
    """Return all render-tree nodes whose ``type`` matches ``node_type``."""

    matches: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if node.get("type") == node_type:
            matches.append(node)
        for child in node.get("children", []):
            matches.extend(_walk_render_nodes(child, node_type))
    elif isinstance(node, list):
        for item in node:
            matches.extend(_walk_render_nodes(item, node_type))
    return matches


def _text_from_render_node(node: Any) -> str:
    """Collect visible TextRun strings below a render-tree node."""

    if isinstance(node, dict):
        text = str(node.get("text", "")) if node.get("type") == "TextRun" else ""
        child_text = "".join(_text_from_render_node(child) for child in node.get("children", []))
        return text + child_text
    if isinstance(node, list):
        return "".join(_text_from_render_node(item) for item in node)
    return ""


def _tables_from_render_tree(render_tree: dict[str, Any], page_index: int) -> list[dict[str, Any]]:
    """Extract best-effort tables from rhwp's render tree.

    rhwp render trees expose table geometry as Table -> Cell -> TextLine ->
    TextRun. The adapter preserves row/column order and y-position so tables can
    be interleaved with paragraph blocks in original page order.
    """

    tables: list[dict[str, Any]] = []
    for table_idx, table in enumerate(_walk_render_nodes(render_tree, "Table")):
        cell_nodes = _walk_render_nodes(table, "Cell")
        if not cell_nodes:
            continue
        max_row = max(int(cell.get("row", 0)) for cell in cell_nodes)
        max_col = max(int(cell.get("col", 0)) for cell in cell_nodes)
        rows = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]
        for cell in cell_nodes:
            row = int(cell.get("row", 0))
            col = int(cell.get("col", 0))
            rows[row][col] = _clean_text(_text_from_render_node(cell))
        if any(any(value for value in row) for row in rows):
            pi = table.get("pi", "?")
            ci = table.get("ci", "?")
            y = _bbox_y(table)
            trace = f"rhwp:page={page_index} table={table_idx} pi={pi} ci={ci} y={y}"
            tables.append({"page": page_index, "y": y, "rows": rows, "trace": trace})
    return tables


def _paragraph_item(key: tuple[int, int, int, int, int | None], runs_raw: list[dict[str, Any]]) -> dict[str, Any] | None:
    runs_raw = sorted(
        runs_raw,
        key=lambda run: (float(run.get("y", 0)), float(run.get("x", 0)), int(run.get("charStart", 0))),
    )
    text = _clean_text("".join(str(run.get("text", "")) for run in runs_raw))
    if not text:
        return None
    runs = [_run_to_inline(run) for run in runs_raw]
    y = min(float(run.get("y", 0)) for run in runs_raw)
    trace = f"rhwp:page={key[0]} sec={key[1]} para={key[2]} parent={key[3]} cell={key[4]} y={y}"
    level = _heading_level(text, runs)
    return {"page": key[0], "y": y, "kind": "heading" if level else "paragraph", "text": text, "level": level, "runs": runs, "trace": trace}


def rhwp_layout_to_model(layout_payload: dict[str, Any]) -> DocumentModel:
    """Convert rhwp `export-layout` JSON into a best-effort DocumentModel.

    This pass prioritizes text order, paragraph grouping, basic heading
    inference, table extraction, and page y-order interleaving.
    """

    model = DocumentModel()
    model.metadata = {
        "source_engine": "rhwp-core",
        "page_count": str(layout_payload.get("page_count", "")),
        "input": str(layout_payload.get("input", "")),
    }

    items: list[dict[str, Any]] = []
    paragraph_runs: dict[tuple[int, int, int, int, int | None], list[dict[str, Any]]] = defaultdict(list)
    for page in layout_payload.get("pages", []):
        page_index = int(page.get("page_index", 0))
        for table_item in _tables_from_render_tree(page.get("render_tree", {}), page_index):
            items.append({"kind": "table", **table_item})
        for run in page.get("text_layout", {}).get("runs", []):
            text = str(run.get("text", ""))
            if not text.strip():
                continue
            # Cell text is represented more faithfully through render_tree
            # Table/Cell nodes. Skipping it here prevents duplicate paragraph
            # blocks for table content.
            if run.get("cellIdx") is not None or run.get("parentParaIdx") is not None:
                continue
            enriched = dict(run)
            enriched["pageIndex"] = page_index
            key = (
                page_index,
                int(run.get("secIdx", 0)),
                int(run.get("paraIdx", 0)),
                int(run.get("parentParaIdx", -1)),
                run.get("cellIdx"),
            )
            paragraph_runs[key].append(enriched)

    for key, runs_raw in paragraph_runs.items():
        item = _paragraph_item(key, runs_raw)
        if item:
            items.append(item)

    # Tables and paragraphs from a page are sorted by their page-local y
    # coordinate.  Ties prefer normal text before tables, which keeps headings
    # adjacent to following table blocks in most HWP templates.
    kind_rank = {"heading": 0, "paragraph": 1, "table": 2}
    for item in sorted(items, key=lambda value: (int(value.get("page", 0)), float(value.get("y", 0)), kind_rank.get(str(value.get("kind")), 9))):
        if item["kind"] == "table":
            model.add_table(item["rows"], source_trace=item["trace"])
        elif item["kind"] == "heading":
            model.add_heading(item["text"], level=int(item["level"]), source_trace=item["trace"], runs=item["runs"])
        else:
            model.add_paragraph(item["text"], source_trace=item["trace"], runs=item["runs"])

    return model


def parse_hwp_with_rhwp(input_path: Path, pages: str | None = None) -> DocumentModel:
    return rhwp_layout_to_model(export_hwp_layout_with_rhwp(input_path, pages=pages))
