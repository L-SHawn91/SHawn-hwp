# Fixture: real-hwp

Purpose: store a real minimal `.hwp` sample for validation.

Expected files:
- `source.hwp` ← user-provided real sample
- optional derived outputs generated under benchmark/validation runs

Rules:
- preserve the original file untouched
- do not overwrite the original fixture file
- generated outputs must go to run directories only

Quick start:
```bash
python3 scripts/validate_real_fixture_batch.py \
  --fixture real-hwp \
  --from hwp \
  --outdir /tmp/shawn-hwp-real-runs
```
