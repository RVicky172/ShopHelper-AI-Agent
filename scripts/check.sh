#!/usr/bin/env bash
# The fast quality gate: run before ticking any task. Offline, needs no Docker or LM Studio.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend lint"
uv run ruff check src tests evals
echo "== backend tests"
uv run pytest -q
echo "== terraform format"
terraform -chdir=infra fmt -check -recursive
echo "== frontend lint and format"
(cd web && npm run lint --silent)
echo "== frontend types"
(cd web && npm run typecheck --silent)
echo "== frontend tests"
(cd web && npm test --silent)
echo "All checks passed"
