from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pytest

try:
    from docx import Document  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    Document = None

from shawn_hwp.io_docx import write_docx
from shawn_hwp.model import DocumentModel

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _document_xml(path: Path) -> ET.Element:
    with ZipFile(path) as docx_zip:
        xml = docx_zip.read("word/document.xml")
    return ET.fromstring(xml)


@pytest.mark.skipif(Document is None, reason="python-docx not available in test interpreter")
def test_write_docx_preserves_table_cell_spans(tmp_path: Path):
    model = DocumentModel()
    model.add_table(
        [["통합헤더", ""], ["A", "B"], ["", "C"]],
        cell_spans=[
            {"row": 0, "col": 0, "rowspan": 1, "colspan": 2},
            {"row": 1, "col": 0, "rowspan": 2, "colspan": 1},
        ],
    )
    output = tmp_path / "spans.docx"

    write_docx(model, output)

    root = _document_xml(output)
    grid_spans = [node.attrib[f"{{{W_NS}}}val"] for node in root.findall(f".//{{{W_NS}}}gridSpan")]
    vmerge_values = [node.attrib.get(f"{{{W_NS}}}val", "continue") for node in root.findall(f".//{{{W_NS}}}vMerge")]
    assert "2" in grid_spans
    assert "restart" in vmerge_values
    assert "continue" in vmerge_values
