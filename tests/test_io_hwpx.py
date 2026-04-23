from __future__ import annotations

import zipfile
from pathlib import Path

from shawn_hwp.io_hwpx import default_reference_hwpx, write_hwpx
from shawn_hwp.model import DocumentModel, InlineRun


def test_default_reference_hwpx_exists():
    ref = default_reference_hwpx()
    assert ref.exists()
    assert ref.suffix == ".hwpx"


def test_write_hwpx_uses_reference_template(tmp_path: Path):
    model = DocumentModel()
    model.add_heading("Sample Title")
    model.add_paragraph("First paragraph.")
    output = tmp_path / "out.hwpx"

    write_hwpx(model, output)

    assert output.exists()
    with zipfile.ZipFile(output) as zf:
        names = set(zf.namelist())
        assert "Contents/section0.xml" in names
        assert "mimetype" in names
        section = zf.read("Contents/section0.xml").decode("utf-8", errors="ignore")
        assert "Sample Title" in section
        assert "First paragraph." in section


def test_write_hwpx_respects_custom_reference(tmp_path: Path):
    reference = tmp_path / "ref.hwpx"
    with zipfile.ZipFile(reference, "w") as zf:
        zf.writestr("mimetype", "application/hwp+zip")
        zf.writestr("Contents/header.xml", "<header>custom</header>")
        zf.writestr("Contents/section0.xml", "<old/>")
        zf.writestr("custom.txt", "marker")

    model = DocumentModel()
    model.add_paragraph("Hello")
    output = tmp_path / "out.hwpx"
    write_hwpx(model, output, reference_path=reference)

    with zipfile.ZipFile(output) as zf:
        assert zf.read("custom.txt").decode("utf-8") == "marker"
        section = zf.read("Contents/section0.xml").decode("utf-8")
        assert "Hello" in section


def test_write_hwpx_preserves_inline_runs(tmp_path: Path):
    model = DocumentModel()
    model.add_paragraph("Bold plain", runs=[InlineRun(text="Bold", bold=True), InlineRun(text=" plain")])
    output = tmp_path / "runs.hwpx"

    write_hwpx(model, output)

    with zipfile.ZipFile(output) as zf:
        section = zf.read("Contents/section0.xml").decode("utf-8")
        assert section.count("<hp:run") >= 2
        assert 'charPrIDRef="bold"' in section
        assert "Bold" in section and " plain" in section
