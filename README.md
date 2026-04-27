# SHawn-hwp

SHawn-hwp is a quality-first document conversion pipeline for **HWP/HWPX, DOCX, and Markdown**.

Unlike typical converters that only report whether a file was converted, SHawn-hwp is designed to preserve originals, track loss during conversion, evaluate round-trip stability, and judge whether the result is suitable for real submission workflows.

## Why this exists

Existing commercial, web-based, and open-source converters are often unsatisfying in real work.

Common problems include:

- converted files open, but formatting is unreliable
- tables, captions, numbering, or footnotes break silently
- round-trip conversion is not trustworthy
- there is no clear explanation of what was lost
- submission suitability is left entirely to manual inspection

SHawn-hwp exists to solve that.

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
4. Explain loss
5. Hybrid architecture

## Repository structure

```text
SHawn-hwp/
├─ docs/
├─ data/
├─ templates/
├─ scripts/
├─ src/
├─ tests/
└─ skill/
```

## Research proposal workflow

SHawn-hwp now treats research proposals as a template-safe authoring workflow:

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
```

Key docs:

- `docs/research-proposal-workflow.md`
- `docs/research-proposal-template-profile.md`

## Status

Active build / architecture bootstrap.
