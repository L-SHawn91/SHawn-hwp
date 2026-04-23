from __future__ import annotations

from shawn_hwp.io_markdown import render_markdown
from shawn_hwp.model import DocumentModel


def test_render_markdown_table_has_no_blank_lines_inside_table():
    model = DocumentModel()
    model.add_table([["Col1", "Col2"], ["A", "B"]])

    text = render_markdown(model)

    assert text == "| Col1 | Col2 |\n| --- | --- |\n| A | B |\n"
