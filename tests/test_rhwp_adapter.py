from __future__ import annotations

from pathlib import Path

import pytest

from shawn_hwp.io_markdown import render_markdown
from shawn_hwp.rhwp_adapter import parse_hwp_with_rhwp, rhwp_layout_to_model
from shawn_hwp.converters.rhwp_engine import rhwp_core_available

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_HWP = REPO_ROOT / "data" / "fixtures" / "real-hwp" / "source.hwp"


def test_rhwp_layout_to_model_groups_runs_infers_heading_and_extracts_table():
    payload = {
        "page_count": 1,
        "input": "fixture.hwp",
        "pages": [
            {
                "page_index": 0,
                "text_layout": {
                    "runs": [
                        {"text": "1. ", "x": 0, "y": 0, "secIdx": 0, "paraIdx": 1, "charStart": 0, "bold": True},
                        {"text": "연구개발과제의 필요성", "x": 20, "y": 0, "secIdx": 0, "paraIdx": 1, "charStart": 3, "bold": True},
                        {"text": "본문", "x": 0, "y": 30, "secIdx": 0, "paraIdx": 2, "charStart": 0},
                        {"text": "셀 중복 방지", "x": 0, "y": 60, "secIdx": 0, "paraIdx": 3, "parentParaIdx": 9, "cellIdx": 0},
                    ]
                },
                "render_tree": {
                    "type": "Page",
                    "children": [
                        {
                            "type": "Table",
                            "pi": 9,
                            "ci": 0,
                            "bbox": {"y": 15},
                            "children": [
                                {"type": "Cell", "row": 0, "col": 0, "children": [{"type": "TextRun", "text": "성명"}]},
                                {"type": "Cell", "row": 0, "col": 1, "children": [{"type": "TextRun", "text": "소속"}]},
                                {"type": "Cell", "row": 1, "col": 0, "children": [{"type": "TextRun", "text": "홍길동"}]},
                                {"type": "Cell", "row": 1, "col": 1, "children": [{"type": "TextRun", "text": "건국대"}]},
                            ],
                        }
                    ],
                },
            }
        ],
    }

    model = rhwp_layout_to_model(payload)

    assert model.metadata["source_engine"] == "rhwp-core"
    assert len(model.blocks) == 3
    assert model.blocks[0].kind == "heading"
    assert model.blocks[0].level == 1
    assert model.blocks[0].text == "1. 연구개발과제의 필요성"
    assert model.blocks[1].kind == "table"
    assert model.blocks[1].rows == [["성명", "소속"], ["홍길동", "건국대"]]
    assert model.blocks[2].kind == "paragraph"
    assert model.blocks[2].text == "본문"


@pytest.mark.skipif(not REAL_HWP.exists() or not rhwp_core_available(), reason="real HWP fixture or rhwp core missing")
def test_parse_hwp_with_rhwp_real_first_page():
    model = parse_hwp_with_rhwp(REAL_HWP, pages="0")
    rendered = render_markdown(model)

    assert model.blocks
    assert model.metadata["source_engine"] == "rhwp-core"
    assert "연구" in rendered
