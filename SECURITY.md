# Security Policy

## Supported scope

SHawn-hwp is a public open-source repository. The public branch should contain only source code, documentation, small synthetic or license-compatible fixtures, and public examples.

## Report a vulnerability or accidental disclosure

Please do not open a public issue containing secrets, credentials, private file paths, unreleased research data, patient/sample information, exploit details, or unpublished document contents.

Use GitHub's private vulnerability reporting if available, or contact the repository owner through GitHub.

## Public boundary

The repository must not contain:

- API keys, tokens, OAuth credentials, cookies, or private keys
- `.env`, auth, or credential files
- private cloud paths, local workstation paths, or internal workflow logs
- raw private research data, patient/sample data, manuscripts, or unpublished project state
- generated caches, database files, or large intermediate outputs

## Maintainer checks

Before a public release or tag, run:

```bash
bash scripts/public_safety_scan.sh
python3 -m pytest -q -k 'not real_fixture'
```
