#!/usr/bin/env bash
# Write/refresh the AWS resource ids in .env from `terraform output` (keeps other lines).
set -euo pipefail
cd "$(dirname "$0")/.."
touch .env
set_var() {
  grep -v "^$1=" .env > .env.tmp || true
  echo "$1=$2" >> .env.tmp && mv .env.tmp .env
}
out() { terraform -chdir=infra output -raw "$1"; }
set_var ORDERS_TABLE "$(out orders_table)"
set_var HISTORY_TABLE "$(out history_table)"
set_var CHECKPOINT_TABLE "$(out checkpoint_table)"
set_var KNOWLEDGE_BASE_ID "$(out knowledge_base_id)"
set_var GUARDRAIL_ID "$(out guardrail_id)"
set_var GUARDRAIL_VERSION "$(out guardrail_version)"
echo ".env updated"
