from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_HWP = REPO_ROOT / 'data' / 'fixtures' / 'real-hwp' / 'source.hwp'


@pytest.mark.skipif(not REAL_HWP.exists(), reason='real HWP fixture missing')
def test_compare_hwp_routes_generates_summary(tmp_path: Path):
    outdir = tmp_path / 'compare'
    cmd = [
        sys.executable,
        str(REPO_ROOT / 'scripts' / 'compare_hwp_routes.py'),
        '--input', str(REAL_HWP),
        '--outdir', str(outdir),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    assert 'SHawn-hwp compare_hwp_routes' in result.stdout
    summary = json.loads((outdir / 'comparison_summary.json').read_text(encoding='utf-8'))
    assert 'artifacts' in summary
    assert 'scores' in summary
    assert (outdir / 'direct.md').exists()
    assert (outdir / 'bridge.hwpx').exists()
    assert (outdir / 'bridge.md').exists()
