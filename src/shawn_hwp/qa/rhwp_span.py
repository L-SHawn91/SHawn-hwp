"""rhwp table-span QA helpers for SHawn-hwp.

This module summarizes span preservation/inference at the DocumentModel level.
It intentionally does not decide whether every inferred merge is correct; instead
it highlights tables that deserve visual comparison against rhwp SVG/page output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from shawn_hwp.model import Block, DocumentModel


@dataclass
class SpanQaTable:
    index: int
    source_trace: str | None
    row_count: int
    column_count: int
    cell_count: int
    span_count: int
    max_span_area: int
    blank_anchor_count: int
    low_confidence_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SpanQaResult:
    label: str | None
    total_tables: int
    span_tables: int
    total_spans: int
    max_span_area: int
    low_confidence_table_count: int
    tables: list[SpanQaTable]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tables"] = [table.to_dict() for table in self.tables]
        return payload


def _table_width(block: Block) -> int:
    return max((len(row) for row in block.rows), default=0)


def _span_area(span: dict[str, Any]) -> int:
    try:
        rowspan = max(int(span.get("rowspan", 1)), 1)
        colspan = max(int(span.get("colspan", 1)), 1)
    except (TypeError, ValueError):
        return 1
    return rowspan * colspan


def _anchor_text(block: Block, span: dict[str, Any]) -> str:
    try:
        row = int(span.get("row", 0))
        col = int(span.get("col", 0))
    except (TypeError, ValueError):
        return ""
    if row < 0 or row >= len(block.rows):
        return ""
    if col < 0 or col >= len(block.rows[row]):
        return ""
    return block.rows[row][col].strip()


def _low_confidence_reasons(block: Block, span_count: int, max_span_area: int, blank_anchor_count: int) -> list[str]:
    row_count = len(block.rows)
    column_count = _table_width(block)
    cell_count = row_count * column_count
    reasons: list[str] = []
    if max_span_area >= max(6, cell_count // 2 if cell_count else 6):
        reasons.append("large_span_area")
    if cell_count and span_count / cell_count >= 0.5:
        reasons.append("high_span_density")
    if blank_anchor_count:
        reasons.append("blank_span_anchor")
    return reasons


def summarize_table_span(block: Block, index: int) -> SpanQaTable:
    row_count = len(block.rows)
    column_count = _table_width(block)
    cell_count = row_count * column_count
    span_count = len(block.cell_spans)
    span_areas = [_span_area(span) for span in block.cell_spans]
    max_span_area = max(span_areas, default=0)
    blank_anchor_count = sum(1 for span in block.cell_spans if not _anchor_text(block, span))
    return SpanQaTable(
        index=index,
        source_trace=block.source_trace,
        row_count=row_count,
        column_count=column_count,
        cell_count=cell_count,
        span_count=span_count,
        max_span_area=max_span_area,
        blank_anchor_count=blank_anchor_count,
        low_confidence_reasons=_low_confidence_reasons(block, span_count, max_span_area, blank_anchor_count),
    )


def build_span_qa_result(model: DocumentModel, label: str | None = None) -> SpanQaResult:
    table_blocks = [block for block in model.blocks if block.kind == "table"]
    tables = [summarize_table_span(block, index) for index, block in enumerate(table_blocks)]
    return SpanQaResult(
        label=label,
        total_tables=len(tables),
        span_tables=sum(1 for table in tables if table.span_count > 0),
        total_spans=sum(table.span_count for table in tables),
        max_span_area=max((table.max_span_area for table in tables), default=0),
        low_confidence_table_count=sum(1 for table in tables if table.low_confidence_reasons),
        tables=tables,
    )


def render_span_qa_markdown(result: SpanQaResult) -> str:
    lines = [
        "# SHawn-hwp rhwp Span QA Report",
        "",
    ]
    if result.label:
        lines.append(f"- label: `{result.label}`")
    lines.extend(
        [
            f"- total tables: `{result.total_tables}`",
            f"- span tables: `{result.span_tables}/{result.total_tables}`",
            f"- total spans: `{result.total_spans}`",
            f"- max span area: `{result.max_span_area}`",
            f"- low-confidence tables: `{result.low_confidence_table_count}`",
            "",
            "## Table Summary",
            "",
            "| Table | Rows | Cols | Spans | Max span area | Low-confidence reasons | Source trace |",
            "|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for table in result.tables:
        reasons = ", ".join(table.low_confidence_reasons) if table.low_confidence_reasons else "-"
        trace = table.source_trace or "-"
        lines.append(
            f"| {table.index} | {table.row_count} | {table.column_count} | {table.span_count} | "
            f"{table.max_span_area} | {reasons} | `{trace}` |"
        )
    if not result.tables:
        lines.append("| - | 0 | 0 | 0 | 0 | - | - |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `span tables` shows how many extracted tables carry merge metadata in the SHawn DocumentModel.",
            "- `large_span_area` means at least one merge covers a large fraction of its table and should be visually checked.",
            "- `high_span_density` means many cells in the table are merged; this is common in official HWP forms but worth QA attention.",
            "- `blank_span_anchor` means a merged-cell anchor position has no text, which can indicate a geometry over-merge or an intentionally blank merged field.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
