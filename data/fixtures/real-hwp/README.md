# Fixture: real-hwp

Purpose: store a real minimal `.hwp` sample for validation.

Expected files:
- `source.hwp` ← user-provided real sample
- optional derived outputs generated under benchmark/validation runs

Rules:
- preserve the original file untouched
- do not overwrite the original fixture file
- generated outputs must go to run directories only
