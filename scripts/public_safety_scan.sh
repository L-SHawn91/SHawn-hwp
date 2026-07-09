#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

hard_fail='(ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY=|ANTHROPIC_API_KEY=|BEGIN RSA PRIVATE KEY|BEGIN OPENSSH PRIVATE KEY|/Users/[^[:space:]]+|/home/[^[:space:]]+|CloudStorage|OneDrive|GDrive|Google Drive|corpus\.db|\.sqlite|\.duckdb)'
review_terms='(unpublished|patient|sample manifest|workflow log|credential|secret|oauth|api key)'

scan_args=(
  --hidden -S
  -g '!.git/**'
  -g '!__pycache__/**'
  -g '!*.egg-info/**'
  -g '!scripts/public_safety_scan.sh'
)

if rg -n "${scan_args[@]}" "$hard_fail" "$repo_root"; then
  echo "Public safety scan found hard-fail matches." >&2
  exit 1
fi

review_scan_args=(
  "${scan_args[@]}"
  -g '!README.md'
  -g '!AGENTS.md'
  -g '!SECURITY.md'
  -g '!CONTRIBUTING.md'
  -g '!CODE_OF_CONDUCT.md'
  -g '!docs/PUBLIC_RELEASE_CHECKLIST.md'
  -g '!.github/ISSUE_TEMPLATE/**'
  -g '!.github/pull_request_template.md'
)

if rg -n "${review_scan_args[@]}" "$review_terms" "$repo_root"; then
  echo "Public safety scan found review terms above; review manually before release." >&2
fi

echo "Public safety scan passed."
