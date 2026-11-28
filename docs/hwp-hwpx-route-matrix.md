# HWP/HWPX Route Matrix

## Primary scope

SHawn-hwp is primarily about these routes:

### Extraction / forward conversion
- `hwp -> docx`
- `hwp -> md`
- `hwp -> hwpx`
- `hwp -> svg` (optional; `rhwp-core` when installed)
- `hwpx -> docx`
- `hwpx -> md`
- `hwpx -> hwp` (if feasible)

### Regeneration / return conversion
- `docx -> hwpx`
- `docx -> hwp` (if feasible)
- `md -> hwpx`
- `md -> hwp` (if feasible)

## Priority order

### Tier 1
- `hwp/hwpx -> docx`
- `hwp/hwpx -> md`

### Tier 2
- `docx/md -> hwpx`

### Tier 3
- `hwp <-> hwpx`
- `docx/md -> hwp`

## Implemented route keys (HWP, `scripts/convert.py`)

These rows match metadata `route` values emitted today. `engine` is what `convert.py` prints on stdout; it is not always identical to the route key.

| Format pair | Metadata `route` | `engine` | `--route` override | Backend | Status |
|---|---|---|---|---|---|
| `hwp -> md` (default) | `hwp-to-md` | `hwp-salvage` | *(omit)* | `hwp5txt` salvage | implemented when `.venv-hwp` exists |
| `hwp -> docx` (default) | `hwp-to-docx` | `hwp-salvage` | *(omit)* | `hwp5txt` salvage | implemented when `.venv-hwp` exists |
| `hwp -> txt` | `hwp-to-txt` | `hwp-salvage` | *(omit)* | `hwp5txt` salvage | implemented when `.venv-hwp` exists |
| `hwp -> md` (layout) | `rhwp-layout-to-md` | `rhwp-core` | `rhwp-layout`, `rhwp-layout-to-md` | `@rhwp/core` layout model | implemented when npm package installed |
| `hwp -> docx` (layout) | `rhwp-layout-to-docx` | `rhwp-core` | `rhwp-layout`, `rhwp-layout-to-docx` | `@rhwp/core` layout model | implemented when npm package installed |
| `hwp -> svg` | `rhwp-svg-render` | `rhwp-core` | *(omit; auto when rhwp available)* | `@rhwp/core` SVG export | implemented when npm package installed |
| `hwp -> hwpx` | `hwp-to-hwpx` | `hwp-bridge` | *(omit)* | external bridge | environment-dependent |

### rhwp vs `hwp-salvage`

| Need | Prefer |
|---|---|
| Fast text-first recovery, TOC heuristics | default `hwp -> md/docx` (`hwp-salvage` / `hwp-to-*`) |
| Layout-aware tables, headings, structure from HWP render tree | `--route rhwp-layout` (`rhwp-layout-to-md` / `rhwp-layout-to-docx`) |
| Visual/page QA | `hwp -> svg` (`rhwp-svg-render`) |

`hwp-salvage` remains the default when both engines are available; rhwp layout routes are opt-in via `--route`. See `docs/rhwp-integration-260501.md` and `docs/benchmark-matrix.md` for benchmark context.

Setup for rhwp routes:

```bash
npm install --prefix external/rhwp-core @rhwp/core
```

## Current engine hypothesis (remaining / exploratory routes)

| Route | Preferred first probe | Notes |
|---|---|---|
| `hwp -> docx` (non-salvage) | `soffice` / rhwp layout | rhwp layout path implemented; LibreOffice still unproven here |
| `hwpx -> docx` | `soffice` | Real file validation still needed |
| `hwp -> md` (non-salvage) | `hwp -> docx -> pandoc/md` or direct parser | rhwp layout path implemented |
| `hwpx -> md` | `hwpx -> docx -> pandoc/md` or direct parser | direct path uncertain |
| `hwp -> hwpx` | native/LibreOffice/open-source probe | bridge route exists; feasibility not proven |
| `docx -> hwpx` | `soffice` first probe | high-value route |
| `md -> hwpx` | `pandoc -> docx -> soffice?` or dedicated hwpx writer | likely needs hybrid route |
| `docx/md -> hwp` | last-tier exploratory | likely difficult |

## Validation rule

A route is not considered usable just because a tool accepts the command.
It must be evaluated with:
- actual file generation
- QA score
- risk summary
- manual inspection notes

## Next required fixtures
- minimal `sample.hwpx`
- minimal `sample.hwp`
- paired expected outputs when available

## References

- CLI: `docs/script-interface.md`, `python3 scripts/convert.py --help`
- rhwp setup and probes: `docs/rhwp-integration-260501.md`
- Regression: `pytest -q tests/test_rhwp_engine.py` (skips when `@rhwp/core` is not installed)