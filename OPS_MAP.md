# SHawn-hwp Ops Map

> L1 entrypoint for HWP/HWPX document-production work.

## Repo role

`SHawn-hwp` owns HWP/HWPX, DOCX, and Markdown conversion workflows plus
quality-first review/reporting for Korean document production and submission lanes.

## Trigger phrases

- HWP, HWPX, DOCX, Markdown conversion
- proposal packaging
- Korean document production
- template injection, submission QA

## Canonical paths

- Mac: `~/GitHub/SHawn-hwp`
- Linux: `~/github/SHawn-hwp`

## Project-workspace relation

This repo owns conversion tooling and QA logic. It does not own SHawn control-plane
policy or manuscript corpus truth.

## Lightweight load path

Read this file first. Escalate to `AGENTS.md` only for editing/running the repo.

## Deep refs

- `AGENTS.md`
- `README.md`
- `docs/benchmark-matrix.md`
- `docs/quality-rubric.md`

## Allowed operations

- Conversion route implementation
- QA/report bundle improvements
- Proposal-template support

## Forbidden operations

- Do not store private raw docs in git
- Do not treat this repo as citation/corpus owner
- Do not mix SHawn control-plane decisions into this repo

## Verification

```bash
git status -sb
python3 -m pytest -q -k 'not real_fixture'
bash scripts/public_safety_scan.sh
```
