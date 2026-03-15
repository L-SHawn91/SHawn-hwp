# Fixture: real-hwpx

Purpose: store a real minimal `.hwpx` sample for validation.

Expected files:
- `source.hwpx` ← user-provided real sample
- optional derived outputs generated under benchmark/validation runs

Rules:
- preserve the original file untouched
- do not overwrite the original fixture file
- generated outputs must go to run directories only

Quick start:
```bash
python3 scripts/validate_real_fixture_batch.py \
  --fixture real-hwpx \
  --from hwpx \
  --outdir /tmp/shawn-hwp-real-runs
```
