from __future__ import annotations

from shawn_hwp.converters.hwp_engine import parse_hwp_text_to_model
from shawn_hwp.io_markdown import render_markdown


def test_parse_hwp_text_to_model_creates_nested_headings_and_paragraph():
    text = "목        차\n\n1. 연구개발과제의 필요성\n  (1) 세부 항목\n가. 세부 소항목\n본문 문단\n"
    model = parse_hwp_text_to_model(text)

    assert model.blocks[0].kind == "heading"
    assert model.blocks[0].text == "목        차"
    assert model.blocks[0].level == 1
    assert model.blocks[1].kind == "heading"
    assert model.blocks[1].text == "1. 연구개발과제의 필요성"
    assert model.blocks[1].level == 1
    assert model.blocks[2].kind == "heading"
    assert model.blocks[2].text == "(1) 세부 항목"
    assert model.blocks[2].level == 2
    assert model.blocks[3].kind == "heading"
    assert model.blocks[3].text == "가. 세부 소항목"
    assert model.blocks[3].level == 3
    assert model.blocks[4].kind == "paragraph"
    assert model.blocks[4].text == "본문 문단"


def test_parse_hwp_text_to_model_splits_compound_heading_line():
    text = "1. 연구개발기관 현황\n가. 참여연구자 편성 총괄 현황  나. 주관연구기관 주요 연구개발 실적\n"
    model = parse_hwp_text_to_model(text)

    headings = [(block.text, block.level) for block in model.blocks if block.kind == "heading"]
    assert headings == [
        ("1. 연구개발기관 현황", 1),
        ("가. 참여연구자 편성 총괄 현황", 3),
        ("나. 주관연구기관 주요 연구개발 실적", 3),
    ]


def test_hwp_model_renders_markdown():
    text = "목        차\n\n1. 연구개발과제의 필요성\n\n본문 문단\n"
    model = parse_hwp_text_to_model(text)
    md = render_markdown(model)

    assert "# 목        차" in md
    assert "# 1. 연구개발과제의 필요성" in md
    assert "본문 문단" in md


def test_hwp_model_renders_nested_heading_levels():
    text = "1. 연구개발과제의 필요성\n(1) 세부 항목\n가. 세부 소항목\n"
    model = parse_hwp_text_to_model(text)
    md = render_markdown(model)

    assert "# 1. 연구개발과제의 필요성" in md
    assert "## (1) 세부 항목" in md
    assert "### 가. 세부 소항목" in md
