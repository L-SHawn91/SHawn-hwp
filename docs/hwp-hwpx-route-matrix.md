# HWP/HWPX Route Matrix

## Primary scope

SHawn-hwp is primarily about these routes:

### Extraction / forward conversion
- `hwp -> docx`
- `hwp -> md`
- `hwp -> hwpx`
- `hwpx -> docx`
- `hwpx -> md`
- `hwpx -> hwp` (if feasible)

### Regeneration / return conversion
- `docx -> hwpx`
- `docx -> hwp` (if feasible)
- `md -> hwpx`
- `md -> hwp` (if feasible)

## Priority order

### Tier 1
- `hwp/hwpx -> docx`
- `hwp/hwpx -> md`

### Tier 2
- `docx/md -> hwpx`

### Tier 3
- `hwp <-> hwpx`
- `docx/md -> hwp`

## Current engine hypothesis

| Route | Preferred first probe | Notes |
|---|---|---|
| `hwp -> docx` | `soffice` | Real file validation still needed |
| `hwpx -> docx` | `soffice` | Real file validation still needed |
| `hwp -> md` | `hwp -> docx -> pandoc/md` or direct parser | direct path uncertain |
| `hwpx -> md` | `hwpx -> docx -> pandoc/md` or direct parser | direct path uncertain |
| `hwp -> hwpx` | native/LibreOffice/open-source probe | feasibility not proven |
| `docx -> hwpx` | `soffice` first probe | high-value route |
| `md -> hwpx` | `pandoc -> docx -> soffice?` or dedicated hwpx writer | likely needs hybrid route |
| `docx/md -> hwp` | last-tier exploratory | likely difficult |

## Validation rule

A route is not considered usable just because a tool accepts the command.
It must be evaluated with:
- actual file generation
- QA score
- risk summary
- manual inspection notes

## Next required fixtures
- minimal `sample.hwpx`
- minimal `sample.hwp`
- paired expected outputs when available
