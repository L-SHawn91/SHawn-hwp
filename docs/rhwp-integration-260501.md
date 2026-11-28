# rhwp integration note (260501)

## Role in SHawn-hwp

`rhwp` is now treated as an optional external rendering/probe engine for SHawn-hwp.

- Upstream: <https://github.com/edwardkim/rhwp>
- Runtime package used here: `@rhwp/core` npm package
- License: MIT
- Primary SHawn-hwp use: HWP layout probing and SVG export for visual QA

This does **not** replace the existing text-first `hwp5txt` salvage route.  The current split is intentional:

| Need | Preferred route | Metadata `route` |
| --- | --- | --- |
| Text/Markdown extraction | default `hwp -> md` (`hwp-salvage`) | `hwp-to-md` |
| DOCX draft from recovered text | default `hwp -> docx` (`hwp-salvage`) | `hwp-to-docx` |
| Layout-aware HWP -> MD/DOCX | `hwp -> md/docx` with `--route rhwp-layout` | `rhwp-layout-to-md` / `rhwp-layout-to-docx` |
| Visual/layout check | `hwp -> svg` (`rhwp-core`) | `rhwp-svg-render` |
| Page count / renderability probe | `rhwp-core` info | *(probe JSON, not convert metadata)* |

## Local setup

The external package is installed outside tracked source under `external/rhwp-core`:

```bash
npm install --prefix external/rhwp-core @rhwp/core
```

The upstream source is cloned for inspection under `external/rhwp`:

```bash
git clone --depth 1 https://github.com/edwardkim/rhwp.git external/rhwp
```

Both directories are ignored by git.

## Direct probe commands

```bash
node scripts/rhwp_probe.mjs info \
  --input data/fixtures/real-hwp/source.hwp

node scripts/rhwp_probe.mjs export-svg \
  --input data/fixtures/real-hwp/source.hwp \
  --outdir outputs/rhwp-svg \
  --pages 0
```

## SHawn-hwp CLI routes

When `@rhwp/core` is installed, `scripts/convert.py` implements these metadata route keys (see `docs/hwp-hwpx-route-matrix.md`):

| `route` in metadata | Invocation |
| --- | --- |
| `rhwp-svg-render` | `--from hwp --to svg` (no `--route`; auto-selected) |
| `rhwp-layout-to-md` | `--from hwp --to md --route rhwp-layout` |
| `rhwp-layout-to-docx` | `--from hwp --to docx --route rhwp-layout` |

Accepted `--route` values for layout conversion: `rhwp-layout`, `rhwp-layout-to-md`, `rhwp-layout-to-docx`.

```bash
python3 scripts/convert.py \
  --input data/fixtures/real-hwp/source.hwp \
  --from hwp \
  --to svg \
  --output outputs/rhwp-svg \
  --emit-metadata outputs/rhwp-svg.meta.json

python3 scripts/convert.py \
  --input data/fixtures/real-hwp/source.hwp \
  --from hwp \
  --to md \
  --route rhwp-layout \
  --output outputs/rhwp.md \
  --emit-metadata outputs/rhwp-md.meta.json
```

## Verification performed

```bash
pytest -q tests/test_rhwp_engine.py tests/test_hwp_engine.py tests/test_convert.py
# 11 passed
```

## Known limitation

Node-side rendering uses a lightweight `measureTextWidth` fallback because the browser Canvas API is not present in this CLI context.  That is good enough for automated renderability/SVG QA, but pixel-perfect layout review should eventually run through a browser/Canvas harness.
