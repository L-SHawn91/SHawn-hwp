# HWP Perfect Conversion Roadmap (Draft v0.1)

## Goal

Turn SHawn-hwp from a quality-first prototype into a near-perfect practical HWP conversion system for real editing and submission workflows.

This roadmap follows `docs/hwp-perfect-conversion-spec.md`.

## Phase 0: baseline freeze

Purpose:
- lock current behavior,
- document known route strengths/weaknesses,
- prevent vague progress claims.

Deliverables:
- current real HWP benchmark snapshots
- known issues list by route (`salvage`, `bridge`, `hybrid`)
- fixture inventory with risk tags
- baseline Tier distribution (A/B/C/D)

Exit criteria:
- every current real HWP fixture has a recorded benchmark result
- at least one reproducible “best known route” result is stored per fixture

## Phase 1: HWP ingress hardening (P0)

Purpose:
- improve structural extraction before flattening into generic text.

Priority work:
- strengthen heading detection from HWP salvage output
- preserve numbering/list semantics more explicitly
- identify table boundaries and repeated table noise more reliably
- detect captions / notes / front matter signals earlier
- map structural signals into `DocumentModel`

Deliverables:
- improved `hwp_engine.py` parsing logic
- new HWP ingress tests
- comparison report: before vs after on real HWP fixtures

Exit criteria:
- structure-related false negatives reduced on real HWP fixtures
- at least one real fixture improves in heading/structure similarity without regressing text

## Phase 2: HWP -> HWPX bridge stabilization (P0)

Purpose:
- make the bridge route viable as the main structure-preserving path.

Priority work:
- bridge-noise suppression
- front matter / TOC duplicate filtering
- repeated heading/table echo suppression
- better HWPX parse recovery after bridge conversion

Deliverables:
- stabilized bridge comparison script outputs
- fixture-level route notes
- improved selection reasons for bridge-vs-salvage decisions

Exit criteria:
- bridge route becomes best route for a meaningful subset of real fixtures
- noise categories become explicitly detectable and test-covered

## Phase 3: Hybrid selection and QA gates (P0/P1)

Purpose:
- choose the least destructive route automatically and explainably.

Priority work:
- tune route scoring thresholds based on real fixtures
- improve `selection_reasons` so they distinguish text loss vs structure loss vs bridge noise
- add hard-fail policies for semantically unsafe outputs
- add fixture-level expected-element assertions

Deliverables:
- updated route selector thresholds and tests
- fixture-aware QA gates
- route recommendation matrix per fixture class

Exit criteria:
- best route selection is reproducible
- major false-positive / false-negative route warnings reduced

## Phase 4: Target-specific quality upgrades (P1)

### HWP -> Markdown
Focus:
- Git-friendly headings
- numbering/list readability
- table survivability
- note/caption survivability

### HWP -> DOCX
Focus:
- editing-safe structure
- heading/list/table usability
- submission template integrity
- notes/captions preserved intelligibly

### HWP -> HWPX
Focus:
- structurally parseable HWPX
- low bridge noise
- downstream stability for HWPX-native paths

Exit criteria:
- at least one target route per fixture class reaches Tier A or high Tier B

## Phase 5: Real-fixture expansion (P1)

Purpose:
- stop optimizing only for synthetic or easy cases.

Required additions:
- more real institutional templates
- more table-heavy forms
- more numbering-heavy policy/report documents
- more caption/footnote-rich documents
- at least one deliberately messy legacy HWP

Exit criteria:
- fixture corpus covers all mandatory classes from the spec
- regressions are caught across heterogeneous documents

## Phase 6: Advanced fidelity work (P2)

Purpose:
- improve high-end fidelity after practical usability is secured.

Focus:
- visual/layout nuances
- floating object behavior
- caption anchoring improvements
- stronger round-trip stability
- submission polish scoring refinements

Exit criteria:
- practical conversion remains stable while visual fidelity improves

## Implementation priorities

### P0 (do now)
1. HWP ingress hardening
2. Bridge stabilization
3. Hybrid QA gating
4. Real fixture benchmark automation

### P1 (do next)
1. Numbering/caption/footnote semantics
2. Fixture schema and expected-element assertions
3. Target-specific output polish

### P2 (later)
1. Layout nuance fidelity
2. Round-trip refinement
3. advanced object handling

## Success metrics

The roadmap is succeeding only if real-fixture metrics improve.

Track at minimum:
- Tier A count
- Tier B count
- average weighted score per fixture class
- structure similarity trend
- table similarity trend
- number of hard fails
- best-route stability across reruns

## Immediate next actions

1. add ingress design document
2. implement one concrete HWP ingress improvement against a real fixture symptom
3. benchmark before/after
4. add fixture-aware regression tests
