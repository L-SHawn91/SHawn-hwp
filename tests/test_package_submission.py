from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_package_submission_copies_files_and_writes_manifest(tmp_path: Path):
    source = tmp_path / "template.hwpx"
    candidate = tmp_path / "generated.hwpx"
    report = tmp_path / "template-qa.md"
    outdir = tmp_path / "bundle"
    source.write_text("source", encoding="utf-8")
    candidate.write_text("candidate", encoding="utf-8")
    report.write_text("report", encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "package_submission.py"),
        "--source",
        str(source),
        "--converted",
        str(candidate),
        "--report",
        str(report),
        "--outdir",
        str(outdir),
        "--include-original",
    ]
    completed = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    assert "package_submission" in completed.stdout
    manifest_path = outdir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["file_count"] == 3
    assert {item["role"] for item in manifest["files"]} == {"original", "candidate", "report"}
    for item in manifest["files"]:
        assert (outdir / item["bundle_path"]).exists()
        assert item["sha256"].startswith("sha256:")


def test_package_submission_can_include_roundtrip(tmp_path: Path):
    source = tmp_path / "source.md"
    candidate = tmp_path / "generated.hwpx"
    report = tmp_path / "template-qa.md"
    roundtrip = tmp_path / "roundtrip.md"
    outdir = tmp_path / "bundle"
    for path in (source, candidate, report, roundtrip):
        path.write_text(path.name, encoding="utf-8")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "package_submission.py"),
        "--source",
        str(source),
        "--converted",
        str(candidate),
        "--report",
        str(report),
        "--include-roundtrip",
        str(roundtrip),
        "--outdir",
        str(outdir),
    ]
    subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)

    manifest = json.loads((outdir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["file_count"] == 3
    assert {item["role"] for item in manifest["files"]} == {"candidate", "report", "roundtrip"}
    assert manifest["include_original"] is False
