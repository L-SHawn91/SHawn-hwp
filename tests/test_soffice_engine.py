from __future__ import annotations

from pathlib import Path

import pytest

from shawn_hwp.converters.soffice_engine import run_soffice_conversion, soffice_available


@pytest.mark.skipif(not soffice_available(), reason="soffice not available")
def test_run_soffice_conversion_docx_to_pdf(tmp_path: Path):
    source = tmp_path / "source.docx"
    pdf = tmp_path / "out.pdf"

    # minimal docx generated via pandoc-compatible zip signature fixture copy is handled in higher-level CLI tests;
    # here we just reuse a real docx payload from the repository fixture path if available.
    repo_docx = Path('/tmp/shawn_hwp_probe.docx')
    if not repo_docx.exists():
        pytest.skip('probe docx not available')
    source.write_bytes(repo_docx.read_bytes())

    result = run_soffice_conversion(source, pdf, 'docx', 'pdf')
    assert pdf.exists()
    assert pdf.read_bytes()[:4] == b'%PDF'
    assert result.route == 'docx-to-pdf'
