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
    """Collect visible TextRun strings below a render-tree node.

    rhwp represents multi-line table cell content as multiple TextLine nodes.
    Preserve those line boundaries so proposal-form cells do not collapse
    separate lines into a single glued string.
    """

    if isinstance(node, dict):
        if node.get("type") == "TextRun":
            return str(node.get("text", ""))
        if node.get("type") == "TextLine":
            return "".join(_text_from_render_node(child) for child in node.get("children", []))
        line_texts = [
            _text_from_render_node(child)
            for child in node.get("children", [])
            if isinstance(child, dict) and child.get("type") == "TextLine"
        ]
        if line_texts:
            return "\n".join(text for text in line_texts if text)
        return "".join(_text_from_render_node(child) for child in node.get("children", []))
    if isinstance(node, list):
        return "".join(_text_from_render_node(item) for item in node)
    return ""


def _int_attr(node: dict[str, Any], *names: str, default: int = 0) -> int:
    for name in names:
        if name not in node:
            continue
        try:
            return int(node[name])
        except (TypeError, ValueError):
            return default
    return default


def _explicit_span(node: dict[str, Any], *names: str) -> int | None:
    for name in names:
        if name not in node:
            continue
        try:
            return max(int(node[name]), 1)
        except (TypeError, ValueError):
            return None
    return None


def _bbox_rect(node: dict[str, Any]) -> tuple[float, float, float, float] | None:
    bbox = node.get("bbox")
    if not isinstance(bbox, dict):
        return None
    try:
        x = float(bbox.get("x"))
        y = float(bbox.get("y"))
        width = float(bbox.get("w", bbox.get("width")))
        height = float(bbox.get("h", bbox.get("height")))
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    return x, y, width, height


def _cluster_positions(values: list[float], tolerance: float = 1.0) -> list[float]:
    """Merge near-identical rhwp coordinates caused by rounding noise."""

    clusters: list[list[float]] = []
    for value in sorted(values):
        if clusters and abs(value - (sum(clusters[-1]) / len(clusters[-1]))) <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return [sum(cluster) / len(cluster) for cluster in clusters]


def _nearest_boundary_index(boundaries: list[float], value: float, tolerance: float = 1.5) -> int | None:
    if not boundaries:
        return None
    index = min(range(len(boundaries)), key=lambda item: abs(boundaries[item] - value))
    if abs(boundaries[index] - value) <= tolerance:
        return index
    return None


def _span_from_bbox(cell: dict[str, Any], boundaries: list[float], axis: str) -> int:
    rect = _bbox_rect(cell)
    if rect is None or len(boundaries) < 2:
        return 1
    x, y, width, height = rect
    start = x if axis == "x" else y
    end = start + (width if axis == "x" else height)
    start_index = _nearest_boundary_index(boundaries, start)
    end_index = _nearest_boundary_index(boundaries, end)
    if start_index is None or end_index is None or end_index <= start_index:
        return 1
    return max(end_index - start_index, 1)


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
        x_boundaries: list[float] = []
        y_boundaries: list[float] = []
        for cell in cell_nodes:
            rect = _bbox_rect(cell)
            if rect is None:
                continue
            x, y, width, height = rect
            x_boundaries.extend([x, x + width])
            y_boundaries.extend([y, y + height])
        x_boundaries = _cluster_positions(x_boundaries)
        y_boundaries = _cluster_positions(y_boundaries)

        cell_infos: list[dict[str, Any]] = []
        for cell in cell_nodes:
            explicit_rowspan = _explicit_span(cell, "rowSpan", "rowspan", "row_span")
            explicit_colspan = _explicit_span(cell, "colSpan", "colspan", "col_span")
            row = _int_attr(cell, "row")
            col = _int_attr(cell, "col")
            cell_infos.append(
                {
                    "cell": cell,
                    "row": row,
                    "col": col,
                    "rowspan": explicit_rowspan or _span_from_bbox(cell, y_boundaries, "y"),
                    "colspan": explicit_colspan or _span_from_bbox(cell, x_boundaries, "x"),
                }
            )

        by_row: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for info in cell_infos:
            by_row[int(info["row"])].append(info)
        for row_infos in by_row.values():
            row_infos.sort(key=lambda info: int(info["col"]))
            for index, info in enumerate(row_infos):
                if index + 1 >= len(row_infos):
                    continue
                next_col = int(row_infos[index + 1]["col"])
                col_gap_span = max(next_col - int(info["col"]), 1)
                info["colspan"] = max(int(info["colspan"]), col_gap_span)
        grid_width = max(info["col"] + max(int(info["colspan"]), 1) for info in cell_infos)
        grid_height = max(info["row"] + max(int(info["rowspan"]), 1) for info in cell_infos)
        rows = [["" for _ in range(grid_width)] for _ in range(grid_height)]
        cell_spans: list[dict[str, int]] = []
        for info in cell_infos:
            cell = info["cell"]
            row = int(info["row"])
            col = int(info["col"])
            rowspan = max(int(info["rowspan"]), 1)
            colspan = max(int(info["colspan"]), 1)
            rows[row][col] = _clean_text(_text_from_render_node(cell))
            if rowspan > 1 or colspan > 1:
                cell_spans.append({"row": row, "col": col, "rowspan": rowspan, "colspan": colspan})
        if any(any(value for value in row) for row in rows):
            pi = table.get("pi", "?")
            ci = table.get("ci", "?")
            y = _bbox_y(table)
            trace = f"rhwp:page={page_index} table={table_idx} pi={pi} ci={ci} y={y}"
            tables.append({"page": page_index, "y": y, "rows": rows, "cell_spans": cell_spans, "trace": trace})
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
            model.add_table(item["rows"], source_trace=item["trace"], cell_spans=item.get("cell_spans"))
        elif item["kind"] == "heading":
            model.add_heading(item["text"], level=int(item["level"]), source_trace=item["trace"], runs=item["runs"])
        else:
            model.add_paragraph(item["text"], source_trace=item["trace"], runs=item["runs"])

    return model


def parse_hwp_with_rhwp(input_path: Path, pages: str | None = None) -> DocumentModel:
    return rhwp_layout_to_model(export_hwp_layout_with_rhwp(input_path, pages=pages))
