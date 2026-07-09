# Benchmark Matrix

SHawn-hwp should not be benchmarked as a standalone mature HWP parser. Its useful comparison point is the missing QA layer above existing engines: route selection, conversion-loss reporting, template integrity checks, and submission bundle creation.

## Route comparison

| Route / project | Primary role | Strength | Typical gap | SHawn-hwp strategy |
|---|---|---|---|---|
| `rhwp` | HWP parser / renderer / WASM primitives | Strong HWP parsing and visual/layout probing | Not a full Korean submission QA workflow by itself | Treat as a backend for page/renderability and layout evidence |
| `pyhwp` / HWP v5 parsers | Legacy HWP text/model extraction | More mature HWP v5 extraction path | HWPX and modern submission workflow coverage is limited | Treat as a text/model salvage route where applicable |
| LibreOffice | Broad office conversion route | Practical DOCX/PDF/HTML conversion when import filters work | Silent structure/layout loss is common | Wrap with QA reports and route confidence |
| Pandoc | Markdown/DOCX/HTML conversion | Stable document pipeline for open formats | Not HWP-native | Use for Markdown/DOCX legs and round-trip checks |
| Web/commercial converters | Convenience conversion | Sometimes best visual result | Hard to audit, may be unsuitable for private drafts | Use only when privacy/license constraints permit; record externally |
| SHawn-hwp | QA/orchestration/submission layer | Loss taxonomy, route scoring, template QA, bundles | Not a replacement parser | Compare routes and make failures reviewable |

## Minimum public benchmark matrix

| Fixture class | Source | Candidate route | Target | Current public status | Loss tracked | Notes |
|---|---|---|---|---|---|---|
| Simple prose | Markdown fixture spec | Pandoc/Markdown route | DOCX/HTML/MD | documented | text, headings, lists | Good for baseline text/structure scoring |
| Numbering-heavy | Markdown fixture spec | Pandoc/Markdown route | DOCX/HTML/MD | documented | numbering, lists | Detects list reset/drift |
| Footnote-heavy | Markdown fixture spec | Pandoc/Markdown route | DOCX/HTML/MD | documented | footnotes, references | Detects citation/footnote loss |
| Table-heavy | Markdown fixture spec | Pandoc/Markdown route | DOCX/HTML/MD | documented | table count, merged-cell risk | Public fixture is synthetic/spec-level |
| HWP visual probe | Real HWP fixture | `rhwp` route | SVG/meta | local/private fixture required | renderability, page count | Public repo excludes proprietary/private source files |
| HWPX template workflow | Public synthetic HWPX/template slot candidate | internal template QA | HWPX/report | partial | slot integrity, placeholders | Core differentiator for Korean proposal workflows |
| Real HWPX validation | Real license-compatible HWPX | external route + QA | DOCX/HTML/report | skipped unless fixture exists | conversion loss, route confidence | Tests are skipped in public CI when fixture is absent |

## Decision rule

A route wins only when it improves at least one of the following without introducing unacceptable content loss:

1. higher weighted QA score,
2. lower loss level (`L0` better than `L4`),
3. better submission readiness,
4. better auditability of failure modes,
5. safer public/private boundary.

## Reporting fields

Every benchmark row should be reducible to:

```json
{
  "route": "hwpx-to-docx",
  "engine": "rhwp/hwp-salvage/external",
  "weighted_score": 74,
  "max_score": 100,
  "loss_level": {"code": "L2", "label": "structure loss"},
  "confidence": 0.58,
  "submission_ready": false,
  "risk_categories": ["table", "structure"]
}
```
