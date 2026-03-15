from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from shawn_hwp.converters.pandoc_engine import pandoc_available, run_pandoc_conversion


@pytest.mark.skipif(not pandoc_available(), reason="pandoc not available")
def test_run_pandoc_conversion_md_to_html(tmp_path: Path):
    source = tmp_path / "source.md"
    output = tmp_path / "out.html"
    source.write_text("# Title\n\nhello\n", encoding="utf-8")

    result = run_pandoc_conversion(source, output, "md", "html")

    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "<h1" in html
    assert "Title" in html
    assert result.route == "md-to-html"
