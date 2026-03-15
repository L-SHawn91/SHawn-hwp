# HWP/HWPX Validation Plan

## Goal
Move SHawn-hwp from generic document conversion MVP into a HWP/HWPX-focused validation system.

## Phase 1: real fixture intake
- add one tiny real `hwpx` fixture
- add one tiny real `hwp` fixture
- preserve originals untouched under fixture directories

## Phase 2: first route probes
For each real fixture, run:
- `-> docx`
- `-> pdf`
- `-> html`
- `-> md` when practical through a controlled bridge

## Phase 3: QA scoring
For each output:
- compute QA report
- record score and top risks
- attach operator notes

## Phase 4: return-route probes
When forward conversion is acceptable, test:
- `docx -> hwpx`
- `md -> hwpx`
- `hwp <-> hwpx` where available

## Required metadata per probe
- input path
- input format
- output path
- output format
- engine
- command route
- score
- readiness
- notes

## Stop conditions
Pause a route when:
- conversion produces empty output
- QA score is below 70
- structural loss is obvious
- output opens but is not semantically usable
