# Research Proposal Template Profile Spec v1

A template profile is the bridge between an official HWP/HWPX form and SHawn-hwp's structured proposal source.

## Why profiles are needed

Research proposal templates are layout-sensitive. A generic converter can produce a file that opens, while still damaging:

- table geometry
- page breaks
- text boxes
- fixed instruction areas
- signature/seal blocks
- official numbering
- margin and font rules

A profile records what must remain protected and where generated content may safely enter.

## Minimal profile fields

```yaml
template_id: nrf-basic-research-2026-v1
display_name: 2026 기초연구사업 연구계획서 양식
source_format: hwpx
source_hash: sha256:...
source_path: data/originals/...

protected_regions:
  - id: cover_fixed_labels
    reason: official labels must not be rewritten
  - id: signature_block
    reason: seal/signature layout must remain exact

editable_slots:
  - id: project_title
    source: project_title
    required: true
  - id: need
    source: sections.need.body
    required: true
  - id: objectives
    source: sections.objectives.body
    required: true

layout_baseline:
  page_count: null
  section_count: null
  table_count: null
  image_count: null
  fonts: []
  margins: []

qa_rules:
  fail_if_placeholder_remains: true
  warn_if_page_count_delta_exceeds: 1
  warn_if_table_count_delta_exceeds: 0
  require_pdf_export_check: true
```

## Slot quality levels

- `draft`: content inserted, no layout guarantee
- `edit-ready`: opens in HWP/HWPX editor and preserves major structure
- `submission-candidate`: layout baseline checked and QA report generated
- `submission-ready`: manual visual inspection completed after automated QA

## Implemented v1 behavior

- Extract profile JSON from zip-based HWPX files.
- Record source hash, XML member count, section count, table count, paragraph count, image count, and explicit slot count.
- Detect explicit slots written as `{{slot}}` or `[[slot:id]]`.
- Map known proposal slots such as `project_title`, `need`, `objectives`, `methods`, and `references` to structured proposal JSON sources.
- Detect likely protected instruction/example regions using conservative Korean submission-form patterns.
- Generate a derivative HWPX by replacing explicit slots only.
- Compare a generated candidate against the original template profile and report structural deltas.

## Non-goals for v1

- Perfect reconstruction of arbitrary `.hwp` binaries
- Automatic visual-field inference from arbitrary official forms without explicit markers
- Replacing final human visual inspection for government/IRIS submissions
- Claiming that DOCX/PDF derivatives prove HWP layout safety

## Safety rule

All profile-driven generation must write into a new derivative output path. The official template and user original must remain unchanged.
