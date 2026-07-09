# SHawn-hwp Sample QA Report

This synthetic example shows the differentiating layer: the report names conversion loss and submission readiness instead of only saying that a file was converted.

- source: `docs/fixtures/table-heavy.md`
- candidate: `outputs/example/table-heavy.docx`
- source format: `md`
- candidate format: `docx`
- score: **84/100**
- readiness: **minor repair needed**
- loss level: **L1 — minor style loss**
- route confidence: **0.60**
- submission ready: **false**
- label: `table-heavy-smoke`

## Metrics

| Category | Score | Max |
|---|---:|---:|
| text | 24 | 25 |
| structure | 18 | 20 |
| table | 9 | 15 |
| image_caption | 10 | 10 |
| footnote_numbering | 10 | 10 |
| submission | 10 | 10 |
| roundtrip | 3 | 10 |

## Comparisons

- text similarity: `0.96`
- heading similarity: `0.90`
- source heading count: `3`
- candidate heading count: `3`
- table similarity: `0.60`
- source table count: `2`
- candidate table count: `1`
- numbering similarity: `1.0`
- footnote similarity: `1.0`
- submission similarity: `1.0`

## Top Risks

- table
- roundtrip
- structure

## Route decision

This route is useful for draft review but not final submission because table evidence changed. SHawn-hwp should either recommend a stronger route or produce a repair checklist before packaging the submission bundle.
