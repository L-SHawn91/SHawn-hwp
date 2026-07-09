# SHawn-hwp

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

SHawn-hwp is an open-source, quality-first document conversion and QA pipeline for **HWP/HWPX, DOCX, and Markdown**.

Unlike typical converters that only report whether a file was converted, SHawn-hwp is designed to preserve originals, track loss during conversion, evaluate round-trip stability, and judge whether the result is suitable for real Korean academic, government, and submission workflows.

## Why this exists

Existing commercial, web-based, and open-source converters are often unsatisfying in real work.

Common problems include:

- converted files open, but formatting is unreliable
- tables, captions, numbering, or footnotes break silently
- round-trip conversion is not trustworthy
- there is no clear explanation of what was lost
- submission suitability is left entirely to manual inspection

SHawn-hwp exists to solve that with reproducible conversion, structured loss reporting, and reviewable QA outputs.

## Core goal

Build a reproducible, quality-oriented, bidirectional conversion system centered on:

- `HWP/HWPX -> DOCX`
- `HWP/HWPX -> Markdown`
- `HWP -> HWPX` and `HWPX -> HWP` where feasible
- `DOCX -> HWPX`
- `Markdown -> HWPX`
- `DOCX/Markdown -> HWP` where feasible
- structured research proposal authoring source -> official HWPX template candidate

while preserving originals, tracking loss, and producing QA reports that explain whether the output is safe for editing, versioning, or submission.

## Design principles

1. Original preservation first
2. Quality over raw conversion count
3. Bidirectional in practice, not in marketing
4. Explain loss instead of hiding it
5. Hybrid architecture: use the best available parser/rendering route, then normalize into a reviewable internal model

## Installation

```bash
git clone https://github.com/L-SHawn91/SHawn-hwp.git
cd SHawn-hwp
python3 -m pip install -e .
```

For development:

```bash
python3 -m pip install -e .[dev]
python3 -m pytest -q -k 'not real_fixture'
bash scripts/public_safety_scan.sh
```

## Repository structure

```text
SHawn-hwp/
├─ docs/        # design notes, workflows, and release checklist
├─ data/        # small public fixtures only
├─ templates/   # template/profile experiments
├─ scripts/     # CLI-style utilities and probes
├─ src/         # Python package source
├─ tests/       # pytest suite
└─ skill/       # agent/operator support material
```

## Research proposal workflow

SHawn-hwp treats research proposals as a template-safe authoring workflow:

```text
structured JSON / Markdown draft
  -> proposal completeness validation
  -> official HWPX template injection candidate
  -> DOCX/PDF/HWPX derivatives
  -> submission QA report
```

Initial CLIs:

```bash
python3 scripts/proposal_validate.py \
  --input docs/fixtures/research-proposal.json \
  --report /tmp/proposal-validation.md \
  --json /tmp/proposal-validation.json

python3 scripts/template_profile.py \
  --template official-template.hwpx \
  --output official-template.profile.json

python3 scripts/proposal_inject.py \
  --template official-template-with-slots.hwpx \
  --proposal docs/fixtures/research-proposal.json \
  --output generated-proposal.hwpx

python3 scripts/template_qa.py \
  --template official-template-with-slots.hwpx \
  --candidate generated-proposal.hwpx \
  --report template-qa.md \
  --json template-qa.json

python3 scripts/package_submission.py \
  --source official-template-with-slots.hwpx \
  --converted generated-proposal.hwpx \
  --report template-qa.md \
  --outdir submission-bundle \
  --include-original
```

Key docs:

- `docs/research-proposal-workflow.md`
- `docs/research-proposal-template-profile.md`
- `docs/rhwp-integration-260501.md`
- `docs/hwp-perfect-conversion-roadmap.md`

## rhwp rendering/probe route

SHawn-hwp can use [`edwardkim/rhwp`](https://github.com/edwardkim/rhwp) via the optional `@rhwp/core` package as a layout/rendering probe engine.

```bash
npm install --prefix external/rhwp-core @rhwp/core

node scripts/rhwp_probe.mjs info \
  --input data/fixtures/real-hwp/source.hwp

python3 scripts/convert.py \
  --input data/fixtures/real-hwp/source.hwp \
  --from hwp \
  --to svg \
  --output outputs/rhwp-svg \
  --emit-metadata outputs/rhwp-svg.meta.json
```

Use this route for page-count/renderability checks and SVG visual QA. Keep `hwp-salvage` as the text/Markdown/DOCX recovery route.

## Public release boundary

This repository is intended to be a public open-source project under the Apache License 2.0. It should contain only source code, documentation, small synthetic or license-compatible fixtures, and public examples.

Do **not** commit private proposal files, local/cloud paths, credentials, caches, unpublished project state, patient/sample information, or generated database files.

Before release or tag, run:

```bash
bash scripts/public_safety_scan.sh
python3 -m pytest -q -k 'not real_fixture'
```

The public CI intentionally excludes real HWP/HWPX fixture validation tests because those require valid proprietary-format fixtures; run the full suite only when fixture inputs are available.

See:

- `docs/PUBLIC_RELEASE_CHECKLIST.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `CITATION.cff`

## License

Licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Status

Active public OSS hardening / architecture bootstrap.
