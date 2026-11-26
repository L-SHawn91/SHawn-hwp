from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from shawn_hwp.converters.soffice_engine import (
    SofficeConversionError,
    run_soffice_conversion,
    soffice_available,
)


def _outdir_from_cmd(cmd: list[str]) -> Path:
    outdir_index = cmd.index("--outdir")
    return Path(cmd[outdir_index + 1])


def _input_from_cmd(cmd: list[str]) -> Path:
    return Path(cmd[-1])


def test_run_soffice_conversion_subprocess_failure_preserves_caller_files(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "report.pdf"
    destination.write_bytes(b"ORIGINAL-DESTINATION")
    sibling = tmp_path / "source.pdf"
    sibling.write_bytes(b"ORIGINAL-SIBLING")

    def fail_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="fake soffice failure")

    monkeypatch.setattr(subprocess, "run", fail_run)

    with pytest.raises(subprocess.CalledProcessError):
        run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"ORIGINAL-DESTINATION"
    assert sibling.read_bytes() == b"ORIGINAL-SIBLING"


def test_run_soffice_conversion_exit_zero_without_output_preserves_caller_files(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "custom-name.pdf"
    destination.write_bytes(b"KEEP-DEST")
    sibling = tmp_path / "source.pdf"
    sibling.write_bytes(b"KEEP-SIBLING")

    def empty_success(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="no output")

    monkeypatch.setattr(subprocess, "run", empty_success)

    with pytest.raises(SofficeConversionError):
        run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"KEEP-DEST"
    assert sibling.read_bytes() == b"KEEP-SIBLING"


def test_run_soffice_conversion_exit_zero_empty_pdf_preserves_destination(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "out.pdf"
    destination.write_bytes(b"UNCHANGED")

    def empty_pdf(cmd, **kwargs):
        staging = _outdir_from_cmd(cmd)
        input_path = _input_from_cmd(cmd)
        (staging / f"{input_path.stem}.pdf").write_bytes(b"")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", empty_pdf)

    with pytest.raises(SofficeConversionError, match="empty pdf"):
        run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"UNCHANGED"


def test_run_soffice_conversion_publish_error_preserves_destination(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "out.pdf"
    destination.write_bytes(b"PRESERVE-ME")

    def succeed(cmd, **kwargs):
        staging = _outdir_from_cmd(cmd)
        input_path = _input_from_cmd(cmd)
        (staging / f"{input_path.stem}.pdf").write_bytes(b"%PDF-1.4\n")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    def fail_replace(src, dst):
        raise OSError(13, "permission denied")

    monkeypatch.setattr(subprocess, "run", succeed)
    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(SofficeConversionError, match="failed to publish output"):
        run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"PRESERVE-ME"


def test_run_soffice_conversion_directory_destination_fails_without_touching_contents(
    tmp_path: Path, monkeypatch
):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "out.pdf"
    destination.mkdir()
    keep = destination / "keep.txt"
    keep.write_bytes(b"IN-DIR")

    def succeed(cmd, **kwargs):
        staging = _outdir_from_cmd(cmd)
        input_path = _input_from_cmd(cmd)
        (staging / f"{input_path.stem}.pdf").write_bytes(b"%PDF-1.4\n")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    with pytest.raises(SofficeConversionError, match="directory"):
        run_soffice_conversion(source, destination, "docx", "pdf")

    assert keep.read_bytes() == b"IN-DIR"


def test_run_soffice_conversion_success_publishes_to_exact_destination(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "custom-name.pdf"
    destination.write_bytes(b"OLD-DEST")
    sibling = tmp_path / "source.pdf"
    sibling.write_bytes(b"OLD-SIBLING")

    def succeed(cmd, **kwargs):
        staging = _outdir_from_cmd(cmd)
        input_path = _input_from_cmd(cmd)
        assert staging.parent == tmp_path
        (staging / f"{input_path.stem}.pdf").write_bytes(b"%PDF-NEW-CONTENT")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    result = run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"%PDF-NEW-CONTENT"
    assert sibling.read_bytes() == b"OLD-SIBLING"
    assert result.route == "docx-to-pdf"


def test_run_soffice_conversion_symlink_destination_replaces_link_not_target(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    real_target = tmp_path / "real.pdf"
    real_target.write_bytes(b"REAL-TARGET")
    link = tmp_path / "out.pdf"
    link.symlink_to(real_target)

    def succeed(cmd, **kwargs):
        staging = _outdir_from_cmd(cmd)
        input_path = _input_from_cmd(cmd)
        (staging / f"{input_path.stem}.pdf").write_bytes(b"%PDF-SYMLINK")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    run_soffice_conversion(source, link, "docx", "pdf")

    assert link.is_file()
    assert not link.is_symlink()
    assert link.read_bytes() == b"%PDF-SYMLINK"
    assert real_target.read_bytes() == b"REAL-TARGET"


def test_run_soffice_conversion_hardlink_alias_updates_shared_inode(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    source.write_bytes(b"source-input")
    destination = tmp_path / "out.pdf"
    destination.write_bytes(b"OLD")
    alias = tmp_path / "alias.pdf"
    os.link(destination, alias)

    def succeed(cmd, **kwargs):
        staging = _outdir_from_cmd(cmd)
        input_path = _input_from_cmd(cmd)
        (staging / f"{input_path.stem}.pdf").write_bytes(b"%PDF-ALIAS")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    run_soffice_conversion(source, destination, "docx", "pdf")

    assert destination.read_bytes() == b"%PDF-ALIAS"
    # os.replace updates only the destination directory entry; other hardlinks keep the old inode.
    assert alias.read_bytes() == b"OLD"


def test_run_soffice_html_keeps_sidecar_files_in_output_parent(tmp_path: Path, monkeypatch):
    source = tmp_path / "doc.docx"
    source.write_bytes(b"docx-bytes")
    destination = tmp_path / "custom.html"

    def succeed(cmd, **kwargs):
        outdir = _outdir_from_cmd(cmd)
        assert outdir == tmp_path
        input_path = _input_from_cmd(cmd)
        (outdir / f"{input_path.stem}.html").write_text("<html><body>ok</body></html>", encoding="utf-8")
        sidecar = outdir / f"{input_path.stem}_files"
        sidecar.mkdir()
        (sidecar / "image.png").write_bytes(b"PNG-BYTES")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    result = run_soffice_conversion(source, destination, "docx", "html")

    assert destination.read_text(encoding="utf-8").startswith("<html>")
    assert (tmp_path / "doc_files" / "image.png").read_bytes() == b"PNG-BYTES"
    assert result.route == "docx-to-html"


def test_run_soffice_docx_route_uses_output_parent_outdir(tmp_path: Path, monkeypatch):
    source = tmp_path / "input" / "doc.docx"
    source.parent.mkdir()
    source.write_bytes(b"docx-bytes")
    destination = tmp_path / "output" / "renamed.docx"
    destination.parent.mkdir()

    def succeed(cmd, **kwargs):
        outdir = _outdir_from_cmd(cmd)
        assert outdir == destination.parent
        input_path = _input_from_cmd(cmd)
        (outdir / f"{input_path.stem}.docx").write_bytes(b"PK-DOCX")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    run_soffice_conversion(source, destination, "docx", "docx")

    assert destination.read_bytes() == b"PK-DOCX"
    assert source.read_bytes() == b"docx-bytes"


@pytest.mark.skipif(not soffice_available(), reason="soffice not available")
def test_run_soffice_conversion_docx_to_pdf_isolated_profile(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.docx"
    pdf = tmp_path / "out.pdf"

    repo_docx = Path("/tmp/shawn_hwp_probe.docx")
    if not repo_docx.exists():
        pytest.skip("probe docx not available")
    source.write_bytes(repo_docx.read_bytes())

    home = tmp_path / "home"
    home.mkdir()
    xdg = tmp_path / "xdg-config"
    xdg.mkdir()
    tmpdir = tmp_path / "tmp"
    tmpdir.mkdir()
    lo_profile = tmp_path / "lo-profile"
    default_lo_config = Path.home() / ".config" / "libreoffice"
    before_mtime = default_lo_config.stat().st_mtime if default_lo_config.exists() else None

    run_env = {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(xdg),
        "TMPDIR": str(tmpdir),
        "_SHAWN_TEST_LO_PROFILE": str(lo_profile),
    }
    real_run = subprocess.run

    def patched_run(cmd, **kwargs):
        profile_path = Path(run_env["_SHAWN_TEST_LO_PROFILE"])
        user_env = f"-env:UserInstallation={profile_path.resolve().as_uri()}"
        assert user_env.startswith("-env:UserInstallation=file://")
        isolated_cmd = [cmd[0], user_env, *cmd[1:]]
        kwargs["env"] = {
            **os.environ,
            "HOME": run_env["HOME"],
            "XDG_CONFIG_HOME": run_env["XDG_CONFIG_HOME"],
            "TMPDIR": run_env["TMPDIR"],
        }
        return real_run(isolated_cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", patched_run)

    result = run_soffice_conversion(source, pdf, "docx", "pdf")

    assert pdf.exists()
    assert pdf.read_bytes()[:4] == b"%PDF"
    assert result.route == "docx-to-pdf"
    assert lo_profile.exists()
    if before_mtime is not None and default_lo_config.exists():
        assert default_lo_config.stat().st_mtime == before_mtime