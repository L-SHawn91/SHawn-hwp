from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from shawn_hwp.template_profile import (
    compare_template_profiles,
    extract_template_profile,
    inject_payload_into_hwpx_template,
    render_template_qa_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_slot_template(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/hwp+zip")
        zf.writestr(
            "Contents/section0.xml",
            """
            <hp:section xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
              <hp:p><hp:run><hp:t>작성요령(제출 시 삭제)</hp:t></hp:run></hp:p>
              <hp:p><hp:run><hp:t>{{project_title}}</hp:t></hp:run></hp:p>
              <hp:tbl>
                <hp:tr><hp:tc><hp:p><hp:run><hp:t>{{need}}</hp:t></hp:run></hp:p></hp:tc></hp:tr>
              </hp:tbl>
            </hp:section>
            """.strip(),
        )
        zf.writestr("BinData/image1.png", b"fake")


PROPOSAL = {
    "project_title": "High-quality HWP proposal automation",
    "principal_investigator": "PI Name",
    "host_institution": "Host Institution",
    "sections": [
        {"id": "need", "title": "1. 연구개발 필요성", "body": "Need body"},
        {"id": "objectives", "title": "2. 연구목표", "body": "Objectives body"},
        {"id": "innovation", "title": "3. 창의성 및 혁신성", "body": "Innovation body"},
        {"id": "methods", "title": "4. 연구내용 및 방법", "body": "Methods body"},
        {"id": "timeline", "title": "5. 추진일정", "body": "Timeline body"},
        {"id": "expected_outcomes", "title": "6. 기대효과", "body": "Outcomes body"},
        {"id": "references", "title": "7. 참고문헌", "body": "References body"},
    ],
}


def test_extract_template_profile_counts_layout_and_slots(tmp_path: Path):
    template = tmp_path / "template.hwpx"
    _make_slot_template(template)

    profile = extract_template_profile(template, template_id="test-template")

    assert profile.template_id == "test-template"
    assert profile.source_hash.startswith("sha256:")
    assert profile.layout_baseline.section_count == 1
    assert profile.layout_baseline.table_count == 1
    assert profile.layout_baseline.image_count == 1
    assert profile.layout_baseline.slot_count == 2
    assert {slot.id for slot in profile.editable_slots} == {"project_title", "need"}
    assert profile.protected_regions


def test_inject_payload_into_hwpx_template_replaces_explicit_slots(tmp_path: Path):
    template = tmp_path / "template.hwpx"
    output = tmp_path / "out.hwpx"
    _make_slot_template(template)

    profile = inject_payload_into_hwpx_template(template, PROPOSAL, output)

    assert profile.layout_baseline.slot_count == 2
    with zipfile.ZipFile(output) as zf:
        text = zf.read("Contents/section0.xml").decode("utf-8")
        assert "{{project_title}}" not in text
        assert "{{need}}" not in text
        assert "High-quality HWP proposal automation" in text
        assert "Need body" in text
        assert zf.read("BinData/image1.png") == b"fake"


def test_template_profile_cli_writes_json(tmp_path: Path):
    template = tmp_path / "template.hwpx"
    output = tmp_path / "profile.json"
    _make_slot_template(template)

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "template_profile.py"),
        "--template",
        str(template),
        "--output",
        str(output),
        "--template-id",
        "cli-template",
    ]
    completed = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "profile extracted" in completed.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["template_id"] == "cli-template"
    assert payload["layout_baseline"]["slot_count"] == 2


def test_proposal_inject_cli_writes_derivative(tmp_path: Path):
    template = tmp_path / "template.hwpx"
    proposal = tmp_path / "proposal.json"
    output = tmp_path / "generated.hwpx"
    _make_slot_template(template)
    proposal.write_text(json.dumps(PROPOSAL, ensure_ascii=False), encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "proposal_inject.py"),
        "--template",
        str(template),
        "--proposal",
        str(proposal),
        "--output",
        str(output),
    ]
    completed = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "proposal injected" in completed.stdout
    assert output.exists()
    with zipfile.ZipFile(output) as zf:
        assert "Need body" in zf.read("Contents/section0.xml").decode("utf-8")


def test_compare_template_profiles_passes_after_slot_injection(tmp_path: Path):
    template = tmp_path / "template.hwpx"
    output = tmp_path / "generated.hwpx"
    _make_slot_template(template)
    inject_payload_into_hwpx_template(template, PROPOSAL, output)

    result = compare_template_profiles(template, output)

    assert result.passed is True
    assert result.deltas["table_count"] == 0
    assert result.deltas["image_count"] == 0
    assert result.candidate_profile.layout_baseline.slot_count == 0
    report = render_template_qa_markdown(result)
    assert "Template QA Report" in report
    assert "PASS" in report


def test_compare_template_profiles_fails_when_slots_remain(tmp_path: Path):
    template = tmp_path / "template.hwpx"
    _make_slot_template(template)

    result = compare_template_profiles(template, template)

    assert result.passed is False
    assert any(issue.code == "slot_placeholder_remaining" for issue in result.issues)


def test_template_qa_cli_writes_report_and_json(tmp_path: Path):
    template = tmp_path / "template.hwpx"
    proposal = tmp_path / "proposal.json"
    output = tmp_path / "generated.hwpx"
    report = tmp_path / "qa.md"
    json_path = tmp_path / "qa.json"
    _make_slot_template(template)
    proposal.write_text(json.dumps(PROPOSAL, ensure_ascii=False), encoding="utf-8")
    inject_payload_into_hwpx_template(template, PROPOSAL, output)

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "template_qa.py"),
        "--template",
        str(template),
        "--candidate",
        str(output),
        "--report",
        str(report),
        "--json",
        str(json_path),
    ]
    completed = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "Template QA Report" in completed.stdout
    assert report.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["deltas"]["table_count"] == 0
