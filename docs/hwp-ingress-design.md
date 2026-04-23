# HWP Ingress Design (Draft v0.1)

## Purpose

Describe how SHawn-hwp should ingest HWP documents so that structure survives early enough to support near-perfect practical conversion.

## Problem statement

Current HWP salvage flow is useful for text recovery but structurally fragile:

```text
HWP -> hwp5txt-like text -> normalization -> heuristic reconstruction -> DocumentModel
```

This causes losses such as:
- heading collapse
- numbering ambiguity
- paragraph boundary errors
- table flattening
- caption/note ambiguity
- bridge-vs-direct evaluation blind spots

## Desired direction

Move toward:

```text
HWP -> structural signal extraction -> canonical block assembly -> DocumentModel -> writer + QA
```

## Ingress layers

### Layer 1: raw extraction
Input sources may include:
- salvage text output
- pyhwp-derived intermediate data
- bridge-derived HWPX as a companion route

Output of Layer 1:
- raw textual stream
- any recoverable structure markers
- source trace metadata per fragment

### Layer 2: structural signal detection
Detect and annotate:
- heading candidates
- numbering/list markers
- table boundaries
- caption markers
- footnote/endnote markers
- front matter / TOC markers
- submission-template labels / field markers

Key principle:
- do not immediately flatten everything into plain paragraphs
- preserve uncertainty as signal when possible

### Layer 3: canonical block assembly
Construct `DocumentModel` blocks with the strongest available semantics.

Current block classes are:
- heading
- paragraph
- table

Near-term extension targets:
- list-like paragraph semantics via metadata or trace
- caption-like paragraph semantics via source trace / metadata
- footnote-like paragraph semantics via source trace / metadata

### Layer 4: cleanup and de-noising
Apply safe cleanup only after signal capture.

Examples:
- repeated bridge front matter suppression
- table echo suppression
- whitespace normalization
- duplicated heading noise suppression

Rule:
- cleanup must not silently erase semantically meaningful blocks

## Structural signals to prioritize

### P0 signals
- top-level numbered sections (`1.`, `2.`)
- parenthesized sections (`(1)`, `(2)`)
- Korean letter sections (`가.`, `나.`)
- compound Korean-number sections (`가-1.`, `나-2.`)
- numeric subitems (`1)`, `2)`)
- TOC markers
- obvious table markers

### P1 signals
- captions (`그림`, `표`-like forms where detectable)
- footnote-style tails
- checkbox / placeholder markers
- appendix-like section boundaries

### P2 signals
- richer object anchoring
- fine layout cues

## Parsing policy

### 1. Preserve before infer
If a marker exists in the source text, preserve it as a candidate structural signal before normalizing it away.

### 2. Prefer stable heuristics over aggressive heuristics
A conservative heading detector is better than a noisy one that corrupts paragraphs.

### 3. Distinguish direct-salvage noise from meaningful repeats
Repeated headings may be either:
- real appendices/repeated forms, or
- extraction noise.

This should be handled by fixture-backed heuristics, not blind deletion.

### 4. Use source traces aggressively
Every inferred block should carry a `source_trace` where practical.
This helps:
- QA explanation
- debugging
- future rule tuning

## Proposed near-term engineering steps

### Step 1: improve heading recognition
Extend HWP heading detection to capture:
- compound Korean-number markers (`다-1.` etc.)
- TOC normalized forms
- noisy spacing variants

### Step 2: add fixture-backed expected heading checks
For selected real fixtures, assert that critical heading markers become headings, not paragraphs.

### Step 3: separate front matter / TOC handling
When TOC-like repeated headings appear, distinguish:
- true body headings
- front matter / TOC echoes
- bridge duplication

### Step 4: expose ingress diagnostics
Emit optional diagnostics such as:
- detected heading markers
- heading count before/after cleanup
- suspicious repeated section markers

## Expected benefits

A stronger HWP ingress should improve:
- heading similarity
- selection reason accuracy
- markdown readability
- DOCX editing safety
- route comparison confidence

## Non-goals

This document does not yet define:
- a full binary HWP parser replacement,
- complete visual fidelity handling,
- or universal object semantics.

It is focused on the immediate structural bottleneck between HWP input and `DocumentModel`.

## Immediate implementation target

The first concrete implementation target after this design should be:

> improve HWP heading detection and fixture-backed structural regression checks using real HWP output symptoms already observed in the repository.
