from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from shawn_hwp.converters.hwp_engine import hwp_bridge_available

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_HWP = REPO_ROOT / 'data' / 'fixtures' / 'real-hwp' / 'source.hwp'


@pytest.mark.skipif(not hwp_bridge_available(), reason='hwp2hwpx bridge missing')
def test_hwp_bridge_environment_available():
    assert hwp_bridge_available() is True


@pytest.mark.skipif(not REAL_HWP.exists() or not hwp_bridge_available(), reason='real HWP fixture or hwp2hwpx bridge missing')
def test_convert_cli_hwp_to_hwpx_real_fixture(tmp_path: Path):
    output = tmp_path / 'out.hwpx'
    metadata = tmp_path / 'meta.json'
    cmd = [
        sys.executable,
        str(REPO_ROOT / 'scripts' / 'convert.py'),
        '--input', str(REAL_HWP),
        '--from', 'hwp',
        '--to', 'hwpx',
        '--output', str(output),
        '--emit-metadata', str(metadata),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    assert 'engine=hwp-bridge' in result.stdout
    assert output.exists()
    with zipfile.ZipFile(output) as zf:
        assert 'Contents/section0.xml' in zf.namelist()
    payload = json.loads(metadata.read_text(encoding='utf-8'))
    assert payload['source_format'] == 'hwp'
    assert payload['target_format'] == 'hwpx'
