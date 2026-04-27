from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from shawn_hwp.proposal import validate_proposal_payload, render_validation_markdown


REPO_ROOT = Path(__file__).resolve().parents[1]


VALID_PROPOSAL = {
    "project_title": "Endometrial organoid platform for regenerative screening",
    "principal_investigator": "PI Name",
    "host_institution": "Host Institution",
    "sections": [
        {"id": "need", "title": "1. 연구개발 필요성", "body": "Unmet need and rationale."},
        {"id": "objectives", "title": "2. 연구목표", "body": "Specific aims and milestones."},
        {"id": "innovation", "title": "3. 창의성 및 혁신성", "body": "Novel contribution."},
        {"id": "methods", "title": "4. 연구내용 및 방법", "body": "Experimental design."},
        {"id": "timeline", "title": "5. 추진일정", "body": "Year-by-year plan."},
        {"id": "expected_outcomes", "title": "6. 기대효과", "body": "Expected scientific and translational outputs."},
        {"id": "references", "title": "7. 참고문헌", "body": "Author, year, title, DOI."},
    ],
}


def test_valid_proposal_payload_passes():
    result = validate_proposal_payload(VALID_PROPOSAL)

    assert result.valid is True
    assert result.present_required_section_count == result.required_section_count
    assert result.issues == []

    report = render_validation_markdown(result)
    assert "PASS" in report
    assert "7/7" in report


def test_missing_required_section_fails():
    payload = dict(VALID_PROPOSAL)
    payload["sections"] = [section for section in VALID_PROPOSAL["sections"] if section["id"] != "methods"]

    result = validate_proposal_payload(payload)

    assert result.valid is False
    assert any(issue.code == "missing_required_section" and issue.location == "sections.methods" for issue in result.issues)


def test_submission_noise_is_warning_not_failure():
    payload = json.loads(json.dumps(VALID_PROPOSAL, ensure_ascii=False))
    payload["sections"][0]["body"] = "작성요령: 제출 시 삭제"

    result = validate_proposal_payload(payload)

    assert result.valid is True
    assert any(issue.code == "submission_noise_detected" for issue in result.issues)


def test_cli_outputs_report_and_json(tmp_path: Path):
    source = tmp_path / "proposal.json"
    report = tmp_path / "proposal_report.md"
    json_path = tmp_path / "proposal_report.json"
    source.write_text(json.dumps(VALID_PROPOSAL, ensure_ascii=False), encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "proposal_validate.py"),
        "--input",
        str(source),
        "--report",
        str(report),
        "--json",
        str(json_path),
    ]
    completed = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "PASS" in completed.stdout
    assert report.exists()
    assert json_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["present_required_section_count"] == 7
