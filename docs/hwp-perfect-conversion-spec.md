# HWP Perfect Conversion Spec (Draft v0.1)

## Purpose

Define what “perfect” or “near-perfect” HWP conversion means for SHawn-hwp, what must be preserved, how quality is judged, what fixtures are required, and how the project should prioritize implementation work.

This document is intentionally stricter than a generic conversion checklist. The target is not merely “file opens after conversion,” but:

- semantic structure survives,
- editing intent survives,
- submission risk is explainable,
- route selection is evidence-based,
- and real HWP fixtures improve over time.

## Reality check

Absolute 100% fidelity for every HWP document is not a realistic immediate promise.

For SHawn-hwp, “perfect conversion” means one of the following:

1. **True perfect**
   - text, structure, numbering, tables, captions, footnotes, and key layout semantics survive without meaningful loss.
2. **Near-perfect practical conversion**
   - the output is safe for real editing/submission workflows with only minimal manual repair,
   - and all remaining loss is detectable and reportable.

The near-term engineering target is therefore:

> **near-perfect practical conversion for real work**

rather than marketing-style claims of universal flawless conversion.

## Core principle

The project must treat HWP as a **document-structure problem**, not a plain-text extraction problem.

Bad conversion typically happens when a route:

- extracts paragraph text only,
- loses heading hierarchy,
- flattens numbering,
- breaks tables,
- drops captions/footnotes,
- or destroys section/page intent.

Therefore the desired architecture is:

```text
HWP -> canonical document model -> target writer + QA report
```

not merely:

```text
HWP -> plain text -> guessed structure -> target writer
```

## Preservation targets

### P0: must preserve
These are required for any route to be considered near-perfect.

- full body text with negligible loss
- heading hierarchy / section structure
- ordered/unordered numbering intent
- paragraph boundaries
- table boundaries and cell content
- caption presence and attachment intent
- footnote/endnote content and linking intent
- submission-critical labels / headings / form fields when present

### P1: should preserve
These are important for strong practical quality.

- table alignment intent
- front matter / TOC separation
- list nesting depth
- checkbox / placeholder semantics
- image presence and caption adjacency
- section break intent
- repeated header-like noise suppression in bridge routes

### P2: desirable but not required for early “near-perfect”
These matter for high-end fidelity, but should not block first practical wins.

- pixel-close layout recreation
- exact line/page break reproduction
- every HWP-specific visual style nuance
- floating object positioning exactness
- all embedded drawing semantics

## Fidelity dimensions

Each evaluated route should be judged along these dimensions.

### 1. Text fidelity
Questions:
- Was body text preserved?
- Were important labels or form phrases lost?
- Was text duplicated or hallucinated?

Failure examples:
- empty paragraphs replacing content
- duplicated content after bridge conversion
- missing section text

### 2. Structure fidelity
Questions:
- Did heading levels survive?
- Did section ordering remain intact?
- Did lists and sublists remain distinguishable?

Failure examples:
- all headings collapsed into paragraphs
- front matter merged into body
- TOC/body confusion

### 3. Table fidelity
Questions:
- Are tables still tables?
- Did rows/cells survive?
- Is cell order still usable?

Failure examples:
- table flattened into paragraphs
- duplicated echo tables
- cell order corruption

### 4. Caption / figure fidelity
Questions:
- Are figures still represented?
- Are captions preserved and attached to the right blocks?

Failure examples:
- caption text separated from image context
- image placeholder dropped with no warning

### 5. Footnote / numbering fidelity
Questions:
- Did footnote content survive?
- Did numbering semantics survive enough for editing/submission?

Failure examples:
- numbering reset or flattened
- footnotes converted to plain tail text with no distinction

### 6. Submission fidelity
Questions:
- Is the output safe for real review/editing/submission?
- Are form-like labels, headings, sections, check items, and references still usable?

Failure examples:
- a file opens but is semantically unsafe
- a template looks complete but key structure is broken

### 7. Round-trip fidelity
Questions:
- Can forward conversion be returned without catastrophic loss?
- Are important semantics preserved across multi-step routes?

Failure examples:
- `hwp -> hwpx -> docx -> hwpx` causes major structural drift
- numbering/captions become unstable over repeated conversions

## Acceptance tiers

### Tier A: true near-perfect practical conversion
A route qualifies only when all of the following are true:

- weighted score >= 90
- no critical text loss
- no critical heading collapse
- no meaningful table destruction
- no submission-critical semantic loss
- remaining issues are cosmetic or easily repairable

### Tier B: strong working conversion
- weighted score 80-89
- usable for editing with minor repairs
- must still report risk categories clearly

### Tier C: draft-only conversion
- weighted score 70-79
- usable for extraction/reference only
- not safe for submission without manual repair

### Tier D: unsafe
- weighted score < 70
- route should not be recommended for practical conversion

## Hard fail conditions

Regardless of weighted score, a route is considered failed when any of these happen:

- empty or near-empty output
- critical section missing
- source has headings but candidate collapses all headings
- source has tables but candidate destroys table semantics
- candidate introduces severe duplication/noise that blocks editing
- output opens but is semantically misleading for submission use

## Route classes and expectations

### 1. Salvage-direct HWP route
Typical form:

```text
HWP -> salvage extractor -> normalized text -> document model -> target
```

Strengths:
- good for text recovery
- robust fallback
- good anchor for QA comparison

Weaknesses:
- structure often inferred after loss
- numbering/table/caption recovery is limited

Expectation:
- treat as **survival route**, not final perfection route

### 2. Bridge route
Typical form:

```text
HWP -> HWPX bridge -> HWPX native parsing -> target
```

Strengths:
- better chance of preserving structure
- aligns with HWPX-native core

Weaknesses:
- bridge noise
- front matter duplication
- table echoes / repeated content

Expectation:
- likely best long-term production route if stabilized

### 3. Hybrid selection route
Typical form:

```text
run salvage + bridge -> compare QA -> select best route -> explain reasons
```

Expectation:
- preferred practical architecture for real fixtures
- must explain why a route was selected or rejected

## Mandatory fixture classes

A “perfect conversion” project cannot rely on tiny or synthetic cases only.

Minimum fixture classes:

1. **simple-text HWP**
   - mostly paragraphs and headings
2. **numbering-heavy HWP**
   - nested list / numbered section structure
3. **table-heavy HWP**
   - multiple tables, multi-row semantics
4. **footnote-heavy HWP**
   - dense notes/references
5. **caption/image HWP**
   - image-caption adjacency and figure semantics
6. **submission-template HWP**
   - real application/report template semantics
7. **real messy HWP**
   - noisy, legacy, or formatting-heavy document

Each fixture should have:
- original preserved untouched
- source metadata
- expected critical elements checklist
- QA comparison outputs
- operator notes when necessary

## Required fixture metadata

For every real HWP fixture, record:

- fixture id
- source format/version if known
- document type (report/template/manuscript/form/etc.)
- main risk profile (text/structure/table/footnote/caption/submission)
- critical elements expected to survive
- known bad behaviors in current routes
- best known route
- current readiness band

## QA requirements

A route is not “good” unless it is measurable.

Every evaluated route should emit:

- weighted score
- readiness band
- text similarity
- heading/structure similarity
- table similarity
- numbering similarity
- footnote similarity
- submission similarity
- risk categories
- selection reasons / justification

The QA layer must not only say **what won**, but also **what remains risky**.

## “Perfect-adjacent” pass criteria by target

### HWP -> Markdown
Near-perfect means:
- body text intact
- heading hierarchy usable in Git workflows
- numbering/list intent substantially preserved
- tables represented without destructive flattening
- footnotes/captions not silently lost

### HWP -> DOCX
Near-perfect means:
- document safe for editing in Word-like workflows
- headings/lists/tables usable without major repair
- captions and notes remain editable and intelligible
- submission-oriented documents do not become semantically misleading

### HWP -> HWPX
Near-perfect means:
- bridge preserves document semantics strongly enough for native downstream handling
- HWPX output is structurally parseable and not dominated by bridge noise

## Non-goals for the first near-perfect milestone

These should not block the first major milestone:

- exact visual cloning of all HWP layout details
- universal support for every obscure embedded object type
- zero manual touch for every pathological legacy document

The first milestone is:

> **real HWP documents become safely editable and explainably convertible**

not:

> “every HWP ever made renders identically in all targets.”

## Engineering implications

If SHawn-hwp is serious about near-perfect HWP conversion, implementation should prioritize:

### P0 engineering work
- strengthen HWP ingress before text flattening
- extract more structural signals from HWP
- map HWP structural signals into `DocumentModel`
- improve bridge-noise suppression and bridge-vs-salvage QA comparison
- expand real HWP regression fixtures

### P1 engineering work
- preserve numbering/list semantics more explicitly
- preserve caption/footnote linkage better
- improve table reconstruction scoring and recovery
- add fixture-level expected-element assertions

### P2 engineering work
- refine visual/layout fidelity
- improve floating object handling
- pursue stronger round-trip stability

## Project definition of success

SHawn-hwp should consider HWP conversion “successful” only when all of the following become true for a growing real-fixture set:

- the best route is automatically chosen with evidence,
- practical outputs are submission-safe or clearly flagged when unsafe,
- route weaknesses are explainable,
- regressions are caught automatically,
- and the percentage of real fixtures reaching Tier A or Tier B steadily rises.

## Short operational definition

For day-to-day work, use this definition:

> **A HWP conversion is near-perfect when the result preserves the meaning, structure, and editing intent of the source well enough for real downstream use, and any remaining loss is minor, detectable, and clearly reported.**

## Next documents to derive from this spec

This spec should be followed by:

1. `docs/hwp-perfect-conversion-roadmap.md`
   - implementation priorities
2. `docs/hwp-fixture-requirements.md`
   - detailed fixture schema
3. `docs/hwp-qa-gates.md`
   - pass/fail thresholds and hard fail policy
4. `docs/hwp-ingress-design.md`
   - structural ingestion plan for HWP
