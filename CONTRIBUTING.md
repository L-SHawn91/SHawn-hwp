# Contributing to SHawn-hwp

Thank you for considering a contribution.

SHawn-hwp focuses on quality-first conversion and QA for Korean document workflows involving HWP/HWPX, DOCX, and Markdown.

## Good contribution areas

- Small, reproducible fixtures that are synthetic or clearly license-compatible
- Conversion-loss reporting and QA improvements
- HWPX/DOCX/Markdown parser and writer tests
- Documentation for public workflows and limitations
- Bug reports with minimal public reproduction cases

## Public-data boundary

Do not submit:

- private proposal files, manuscripts, contracts, or unreleased documents
- patient/sample data, lab-internal files, or non-public research material
- API keys, credentials, cookies, `.env` files, local/cloud paths, or database files
- large generated outputs or cache directories

If a bug requires a sensitive document, reduce it to a synthetic minimal fixture before opening an issue or pull request.

## Development setup

```bash
git clone https://github.com/L-SHawn91/SHawn-hwp.git
cd SHawn-hwp
python3 -m pip install -e .[dev]
python3 -m pytest -q -k 'not real_fixture'
bash scripts/public_safety_scan.sh
```

## Pull request checklist

- [ ] The change is small and reviewable.
- [ ] Tests were added or updated when behavior changed.
- [ ] `python3 -m pytest -q -k 'not real_fixture'` passes.
- [ ] `bash scripts/public_safety_scan.sh` passes.
- [ ] No private files, credentials, local paths, or generated caches are included.
- [ ] Documentation was updated when public behavior changed.

## License of contributions

Unless explicitly stated otherwise, intentional contributions are submitted under the Apache License 2.0, the same license as this repository.
