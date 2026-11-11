# DOCX QA package

The `shawn-docx-qa` distribution is maintained in
[`packages/shawn-docx-qa`](../packages/shawn-docx-qa). Its Python import remains
`shawn_docx_qa`; importing it does not load a conversion or rendering backend.
The conversion distribution remains `shawn-hwp`.

## Install and check

From the repository root, install both development packages into an active
virtual environment:

```bash
python3 -m pip install -e '.[dev]' -e './packages/shawn-docx-qa[dev]'
python3 -m pytest -q tests -k 'not real_fixture'
python3 -m pytest -q packages/shawn-docx-qa/tests
bash scripts/public_safety_scan.sh
```

To use only the QA package, install `./packages/shawn-docx-qa` instead. It has no
runtime dependencies and retains its Python 3.10+ support. The conversion package
requires Python 3.11+; combined maintenance uses Python 3.11 or later.

```python
from shawn_docx_qa import qa_docx

report = qa_docx('example.docx')
structure_present = report['is_docx_zip'] and report['has_document_xml']
print(structure_present, report['warnings'])
```

This checks ZIP readability, the presence of `word/document.xml`, and whether
core metadata is missing. `is_docx_zip` alone also accepts readable ZIP archives
that lack a DOCX document part. The utility does not parse or validate XML,
inspect document text, verify relationships, render pages, assess layout, or
establish submission readiness. Missing files and unrelated I/O errors still
propagate to the caller. It reads inputs without extracting or changing them;
reports expose the filename rather than its parent directory.

## Source preservation and maintenance

The compact [import manifest](../packages/shawn-docx-qa/IMPORT_MANIFEST.json)
identifies the public source repository, exact source commit, per-file SHA-256,
and excluded files. Imported source, existing tests, documentation, and
Apache-2.0 license/notice bytes are preserved. The package README and release
documents retain upstream context; this page describes their maintenance within
SHawn-hwp.

The owner repository supplies ignore rules, public-safety checks, and CI for both
packages. No second scanner or scheduler is installed. New functional tests
construct small synthetic OOXML archives at test time and cover normal input,
missing metadata, a missing document part, damaged input, filename-only output,
and input preservation. They need no private documents or rendering engines.

Keep package behavior changes and their tests here. Source-repository callers
and published releases are not redirected or retired by this import. HWP backend
tests remain conditional on their optional engines and fixtures; a skipped
backend test is not conversion evidence.
