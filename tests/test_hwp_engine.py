from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from shawn_hwp.converters.hwp_engine import hwp_salvage_available, parse_hwp_text_to_model
from shawn_hwp.io_markdown import render_markdown

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_HWP = REPO_ROOT / "data" / "fixtures" / "real-hwp" / "source.hwp"


def test_hwp_salvage_environment_available():
    assert hwp_salvage_available() is True


@pytest.mark.skipif(not REAL_HWP.exists(), reason="real HWP fixture missing")
def test_convert_cli_hwp_to_txt_real_fixture(tmp_path: Path):
    output = tmp_path / "out.txt"
    metadata = tmp_path / "meta.json"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "convert.py"),
        "--input",
        str(REAL_HWP),
        "--from",
        "hwp",
        "--to",
        "txt",
        "--output",
        str(output),
        "--emit-metadata",
        str(metadata),
    ]

    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "engine=hwp-salvage" in result.stdout
    assert output.exists()
    body = output.read_text(encoding="utf-8")
    assert "연구개발과제의 필요성" in body
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["source_format"] == "hwp"
    assert payload["target_format"] == "txt"


@pytest.mark.skipif(not REAL_HWP.exists(), reason="real HWP fixture missing")
def test_convert_cli_hwp_to_md_real_fixture(tmp_path: Path):
    output = tmp_path / "out.md"
    metadata = tmp_path / "meta.json"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "convert.py"),
        "--input",
        str(REAL_HWP),
        "--from",
        "hwp",
        "--to",
        "md",
        "--output",
        str(output),
        "--emit-metadata",
        str(metadata),
    ]

    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "engine=hwp-salvage" in result.stdout
    assert output.exists()
    body = output.read_text(encoding="utf-8")
    assert "# 목        차" in body
    assert "연구개발과제의 필요성" in body
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    assert payload["source_format"] == "hwp"
    assert payload["target_format"] == "md"


def test_parse_hwp_text_to_model_recognizes_compound_korean_heading():
    model = parse_hwp_text_to_model("다-1. 공동연구기관 주요 연구개발 실적\n")

    assert len(model.blocks) == 1
    assert model.blocks[0].kind == "heading"
    assert model.blocks[0].level == 3
    assert model.blocks[0].text == "다-1. 공동연구기관 주요 연구개발 실적"


def test_parse_hwp_text_to_model_strips_toc_echo_when_body_repeats_heading_run():
    text = """목        차
1. 연구개발과제의 필요성
2. 연구개발과제의 목표
1. 연구개발과제의 필요성
본문 첫 문단
2. 연구개발과제의 목표
본문 둘째 문단
"""

    model = parse_hwp_text_to_model(text)
    rendered = render_markdown(model)

    assert "# 목        차" not in rendered
    assert rendered.count("# 1. 연구개발과제의 필요성") == 1
    assert rendered.count("# 2. 연구개발과제의 목표") == 1
    assert "본문 첫 문단" in rendered
    assert "본문 둘째 문단" in rendered
