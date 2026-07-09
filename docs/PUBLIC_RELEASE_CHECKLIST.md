# Public Release Checklist

Use this checklist before pushing or tagging a public release of SHawn-hwp.

## Required checks

- [ ] `git status -sb` is reviewed and only intended public changes are present.
- [ ] `bash scripts/public_safety_scan.sh` passes.
- [ ] `python3 -m pytest -q -k 'not real_fixture'` passes for public CI.
- [ ] Full real-fixture validation is run only when valid proprietary-format fixture inputs are available.
- [ ] README quickstart works on a clean clone.
- [ ] No private local/cloud paths, private proposal files, unpublished grant material, raw customer data, or workflow logs are present.
- [ ] No `.env`, token, credential, auth, cache, database, or large generated artifact is tracked.
- [ ] License posture is explicit in `LICENSE`, `NOTICE`, `pyproject.toml`, and `CITATION.cff`.
- [ ] Citation metadata exists in `CITATION.cff`.
- [ ] Public examples are synthetic or license-compatible.
- [ ] GitHub repository metadata has a clear description, useful topics, and the default branch set to `main`.
- [ ] A release tag exists for any application-facing version claim.

## Public positioning

SHawn-hwp is an open-source, quality-first document-conversion and QA pipeline. Public examples should demonstrate conversion integrity, loss reporting, and submission-readiness checks without exposing private proposal material.
