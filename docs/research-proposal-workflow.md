# Research Proposal HWP Workflow v1

SHawn-hwp should handle research proposal production as a **quality-first authoring and template-injection workflow**, not as a blind file converter.

## Goal

Produce high-quality Korean research proposal packages while preserving official HWP/HWPX templates and making every transformation reviewable.

Recommended pipeline:

```text
official HWP/HWPX template
        |
        v
template profile + protected layout map
        |
structured proposal JSON / Markdown draft
        |
content QA + proposal completeness validation
        |
HWPX template injection
        |
DOCX/PDF/HWPX derived outputs
        |
submission QA report
```

## Operating principle

- Never overwrite the official template or original submitted files.
- Treat generated files as derivatives.
- Keep content quality and layout fidelity as separate checks.
- Prefer HWPX template injection for layout-sensitive submissions.
- Use DOCX/Markdown as authoring and review intermediates, not as proof of final HWP readiness.

## Authoring input

The stable authoring source should be either:

1. structured JSON for automation, or
2. Markdown for human-friendly drafting.

The JSON shape should include:

```json
{
  "project_title": "...",
  "principal_investigator": "...",
  "host_institution": "...",
  "sections": [
    {"id": "need", "title": "1. 연구개발 필요성", "body": "..."},
    {"id": "objectives", "title": "2. 연구목표", "body": "..."},
    {"id": "innovation", "title": "3. 창의성 및 혁신성", "body": "..."},
    {"id": "methods", "title": "4. 연구내용 및 방법", "body": "..."},
    {"id": "timeline", "title": "5. 추진일정", "body": "..."},
    {"id": "expected_outcomes", "title": "6. 기대효과", "body": "..."},
    {"id": "references", "title": "7. 참고문헌", "body": "..."}
  ]
}
```

## Required proposal sections

The first automated completeness gate checks for:

- `need`: research need / rationale
- `objectives`: aims and milestones
- `innovation`: novelty and differentiation
- `methods`: research design and methods
- `timeline`: schedule and execution plan
- `expected_outcomes`: expected outputs and impact
- `references`: references with author, year, title, DOI when available

This is intentionally conservative. Institution-specific templates can add more fields later.

## Template profile

Each official template should eventually produce a profile:

```yaml
template_id: institution-program-year
source_file: original template path
protected_regions:
  - cover
  - fixed instruction boxes
  - signature/seal areas
editable_slots:
  - project_title
  - principal_investigator
  - sections.need
  - sections.objectives
  - sections.methods
layout_checks:
  - page_count_delta
  - table_count_delta
  - margin_profile
  - font_profile
  - placeholder_removed
```

## Submission readiness gates

A generated proposal is not submission-ready until these pass:

1. original/template hash recorded
2. required proposal sections present
3. required section bodies non-empty
4. template instructions/examples removed
5. HWPX opens without structural errors
6. table count and critical table dimensions checked
7. page/margin/font profile reviewed
8. DOCX/PDF derivatives generated only from reviewed candidate
9. final QA report saved next to outputs

## CLI entry points added in v1

Validate structured proposal content:

```bash
python3 scripts/proposal_validate.py \
  --input proposal.json \
  --report proposal-validation.md \
  --json proposal-validation.json
```

Extract an HWPX template profile:

```bash
python3 scripts/template_profile.py \
  --template official-template.hwpx \
  --output official-template.profile.json \
  --template-id institution-program-year
```

Inject validated proposal content into explicit HWPX slots:

```bash
python3 scripts/proposal_inject.py \
  --template official-template-with-slots.hwpx \
  --proposal proposal.json \
  --output generated-proposal.hwpx
```

Run template-vs-generated QA:

```bash
python3 scripts/template_qa.py \
  --template official-template-with-slots.hwpx \
  --candidate generated-proposal.hwpx \
  --report template-qa.md \
  --json template-qa.json
```

The injection route is conservative: it only replaces explicit `{{slot}}` or `[[slot:id]]` markers and preserves every other HWPX zip member. It does **not** yet infer arbitrary blank fields from visual layout.

The QA route compares section/XML member/table/image/paragraph/slot-count deltas and fails if explicit slot placeholders remain. This is a structural safety gate, not a visual proof of submission readiness.

Assemble a review/submission bundle:

```bash
python3 scripts/package_submission.py \
  --source official-template-with-slots.hwpx \
  --converted generated-proposal.hwpx \
  --report template-qa.md \
  --outdir submission-bundle \
  --include-original
```

The bundle includes copied artifacts plus a `manifest.json` with file roles, byte sizes, hashes, and a reminder that final visual inspection is still required.

## Next implementation steps

1. Add non-marker slot detection for common official HWPX table forms.
2. Add real official-template fixture validation once user-approved samples are selected.
3. Add PDF/DOCX derivative generation hooks into the package builder.
