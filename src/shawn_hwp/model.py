"""Canonical document model for SHawn-hwp."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

BlockKind = Literal["heading", "paragraph", "table"]


@dataclass
class InlineRun:
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    style_hint: str | None = None
    source_trace: str | None = None


@dataclass
class Block:
    kind: BlockKind
    text: str = ""
    level: int = 0
    rows: list[list[str]] = field(default_factory=list)
    cell_spans: list[dict[str, int]] = field(default_factory=list)
    runs: list[InlineRun] = field(default_factory=list)
    source_trace: str | None = None


@dataclass
class DocumentModel:
    blocks: list[Block] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def add_heading(
        self,
        text: str,
        level: int = 1,
        source_trace: str | None = None,
        runs: list[InlineRun] | None = None,
    ) -> None:
        self.blocks.append(Block(kind="heading", text=text, level=level, runs=runs or [], source_trace=source_trace))

    def add_paragraph(self, text: str, source_trace: str | None = None, runs: list[InlineRun] | None = None) -> None:
        self.blocks.append(Block(kind="paragraph", text=text, runs=runs or [], source_trace=source_trace))

    def add_table(
        self,
        rows: list[list[str]],
        source_trace: str | None = None,
        cell_spans: list[dict[str, int]] | None = None,
    ) -> None:
        self.blocks.append(Block(kind="table", rows=rows, cell_spans=cell_spans or [], source_trace=source_trace))
