from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.route_selector import _build_selection_reasons


def test_route_selector_md_to_hwpx_produces_manifest(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("# Title\n\nhello world\n", encoding="utf-8")
    outdir = tmp_path / "route-select"

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "route_selector.py"),
        "--input",
        str(source),
        "--from",
        "md",
        "--to",
        "hwpx",
        "--outdir",
        str(outdir),
    ]
    completed = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert completed.returncode == 0
    manifest = outdir / "best_route_manifest.json"
    assert manifest.exists()

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["source_format"] == "md"
    assert payload["target_format"] == "hwpx"
    assert payload["selected_route"] == "hwpx-native"
    assert isinstance(payload["candidates"], list)
    assert payload["candidates"][0]["route"] == "hwpx-native"


def test_build_selection_reasons_does_not_flag_structure_below_old_threshold_only():
    qa_payload = {
        "comparisons": {
            "text_similarity": 0.69,
            "heading_similarity": 0.65,
            "table_similarity": 1.0,
            "source_heading_count": 3,
            "candidate_heading_count": 3,
            "source_table_count": 0,
            "candidate_table_count": 0,
        },
        "metrics": {"text": 29, "structure": 13, "table": 10},
    }

    reasons = _build_selection_reasons(qa_payload, "ok")

    assert any("Text similarity low" in reason for reason in reasons)
    assert all("Heading/structure similarity low" not in reason for reason in reasons)
    assert all("Low structure score" not in reason for reason in reasons)


def test_build_selection_reasons_still_flags_structure_when_clearly_low():
    qa_payload = {
        "comparisons": {
            "text_similarity": 0.92,
            "heading_similarity": 0.55,
            "table_similarity": 1.0,
            "source_heading_count": 4,
            "candidate_heading_count": 1,
            "source_table_count": 0,
            "candidate_table_count": 0,
        },
        "metrics": {"text": 38, "structure": 9, "table": 10},
    }

    reasons = _build_selection_reasons(qa_payload, "ok")

    assert any("Heading/structure similarity low" in reason for reason in reasons)
    assert any("Low structure score" in reason for reason in reasons)
