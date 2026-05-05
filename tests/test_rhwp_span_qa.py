from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from shawn_hwp.model import DocumentModel
from shawn_hwp.qa.rhwp_span import build_span_qa_result, render_span_qa_markdown

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_span_qa_result_summarizes_table_spans_and_low_confidence_cases():
    model = DocumentModel()
    model.add_table([["A", "B"], ["C", "D"]], source_trace="rhwp:page=0 table=0")
    model.add_table(
        [["통합헤더", ""], ["A", "B"], ["", "C"]],
        source_trace="rhwp:page=0 table=1",
        cell_spans=[
            {"row": 0, "col": 0, "rowspan": 1, "colspan": 2},
            {"row": 1, "col": 0, "rowspan": 2, "colspan": 1},
        ],
    )
    model.add_table(
        [["큰 병합", "", ""], ["", "", ""], ["", "", ""]],
        source_trace="rhwp:page=1 table=0",
        cell_spans=[{"row": 0, "col": 0, "rowspan": 3, "colspan": 3}],
    )

    result = build_span_qa_result(model, label="fixture")

    assert result.total_tables == 3
    assert result.span_tables == 2
    assert result.total_spans == 3
    assert result.max_span_area == 9
    assert result.low_confidence_table_count == 1
    assert result.tables[1].span_count == 2
    assert result.tables[2].low_confidence_reasons == ["large_span_area"]

    markdown = render_span_qa_markdown(result)
    assert "# SHawn-hwp rhwp Span QA Report" in markdown
    assert "span tables: `2/3`" in markdown
    assert "low-confidence tables: `1`" in markdown
    assert "large_span_area" in markdown


def test_rhwp_span_qa_cli_writes_report_and_json(tmp_path: Path):
    model_payload = {
        "metadata": {"source_engine": "rhwp-core"},
        "blocks": [
            {
                "kind": "table",
                "rows": [["통합헤더", ""], ["A", "B"]],
                "cell_spans": [{"row": 0, "col": 0, "rowspan": 1, "colspan": 2}],
                "source_trace": "rhwp:page=0 table=0",
            }
        ],
    }
    model_json = tmp_path / "model.json"
    report = tmp_path / "span-qa.md"
    json_path = tmp_path / "span-qa.json"
    model_json.write_text(json.dumps(model_payload, ensure_ascii=False), encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "rhwp_span_qa.py"),
        "--model-json",
        str(model_json),
        "--report",
        str(report),
        "--json",
        str(json_path),
        "--label",
        "smoke",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "span_tables=1/1" in result.stdout
    assert report.exists()
    assert json_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["label"] == "smoke"
    assert payload["span_tables"] == 1
    assert payload["tables"][0]["span_count"] == 1
