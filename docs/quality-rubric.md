# Quality Rubric v1

SHawn-hwp scores conversion candidates as reviewable submission artifacts, not merely as successful file exports.

## Weighted score

| Dimension | Weight | What it checks |
|---|---:|---|
| text preservation | 25 | body text retention and gross text drift |
| structure preservation | 20 | headings, sections, hierarchy, paragraph segmentation |
| table preservation | 15 | table count, row/column stability, merged-cell risk |
| image/caption preservation | 10 | figure presence, caption attachment, image evidence |
| footnote/numbering preservation | 10 | footnote/reference and list-number continuity |
| submission suitability | 10 | checkboxes, placeholders, protected-template signals |
| round-trip stability | 10 | whether a candidate remains stable after a second route |

## Readiness bands

| Score | Label | Meaning |
|---:|---|---|
| 90-100 | near submission-ready | candidate may be reviewed for final submission |
| 80-89 | minor repair needed | usable draft with targeted repair |
| 70-79 | working draft quality | useful for editing, not final submission |
| below 70 | unsafe without repair | do not submit without manual repair |

## Loss taxonomy

| Code | Label | Submission meaning |
|---|---|---|
| L0 | no visible loss | nearly lossless for the tracked dimensions |
| L1 | minor style loss | likely usable after visual skim |
| L2 | structure loss | headings/tables/numbering need manual review |
| L3 | content loss | content may be missing or misplaced |
| L4 | submission-blocking loss | do not submit without repair |

Submission-blocking risks such as template/protected-region damage, unresolved placeholders, or missing candidates force `L4` even when the numeric score looks high.

## Route confidence

Route confidence combines:

1. weighted QA score,
2. known risk categories,
3. whether the claimed engine/route was actually available.

This keeps the project positioned as a QA/orchestration layer: the score explains why a route is safe, questionable, or blocked instead of claiming that any single converter is perfect.
