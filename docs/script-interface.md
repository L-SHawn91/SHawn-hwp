# Script Interface Draft v1

## scripts/convert.py

### Purpose
Run a single conversion route.

### Proposed arguments
- `--input PATH`
- `--from {hwp,hwpx,docx,md}`
- `--to {hwpx,docx,md,pdf,html}`
- `--output PATH`
- `--route NAME` (optional explicit route override)
- `--template PATH` (optional reference HWPX/template)
- `--preserve-original` (default behavior; explicit flag for logging)
- `--emit-metadata PATH`

### Expected behavior
- never modify source
- print chosen route
- write output artifact
- optionally emit metadata json

## scripts/qa_report.py

### Purpose
Score source/output pair and emit risk summary.

### Proposed arguments
- `--source PATH`
- `--candidate PATH`
- `--source-format {hwp,hwpx,docx,md}`
- `--candidate-format {hwpx,docx,md,pdf,html}`
- `--report PATH`
- `--json PATH` (optional)
- `--label TEXT`

### Expected behavior
- compute weighted score
- classify submission readiness
- list top risk categories

## scripts/benchmark.py

### Purpose
Run one or more fixtures against one or more candidate routes.

### Proposed arguments
- `--fixture NAME`
- `--candidate NAME`
- `--from FORMAT`
- `--to FORMAT`
- `--outdir PATH`
- `--roundtrip`
- `--notes TEXT`

### Expected behavior
- execute selected route
- trigger QA
- collect outputs under benchmark run directory
- print summary table

## scripts/package_submission.py

### Purpose
Assemble deliverables for human review or submission handoff.

### Proposed arguments
- `--source PATH`
- `--converted PATH`
- `--report PATH`
- `--outdir PATH`
- `--include-roundtrip PATH` (optional)
- `--include-original`

### Expected behavior
- create review bundle
- include source, converted file, and QA report
- preserve traceability between artifacts
