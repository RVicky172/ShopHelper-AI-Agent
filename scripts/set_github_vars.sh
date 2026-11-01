#!/usr/bin/env bash
# Publish Terraform outputs as GitHub Actions repository variables (none are secrets).
#   scripts/set_github_vars.sh          # enable evals + deploy in CI
#   scripts/set_github_vars.sh off      # after `terraform destroy`: CI runs tests only
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=${REPO:-RVicky172/ShopHelper-AI-Agent}

if [ "${1:-on}" = off ]; then
  gh variable set AWS_DEPLOY_ENABLED --repo "$REPO" --body false
  echo "CI evals/deploy disabled"; exit 0
fi

out() { terraform -chdir=infra output -raw "$1" 2>/dev/null || true; }
declare -A VARS=(
  [AWS_REGION]=ap-south-1
  [AWS_ROLE_ARN]=$(out github_deploy_role_arn)
  [ORDERS_TABLE]=$(out orders_table)
  [HISTORY_TABLE]=$(out history_table)
  [CHECKPOINT_TABLE]=$(out checkpoint_table)
  [KNOWLEDGE_BASE_ID]=$(out knowledge_base_id)
  [GUARDRAIL_ID]=$(out guardrail_id)
  [GUARDRAIL_VERSION]=$(out guardrail_version)
  [API_GATEWAY_URL]=$(out api_gateway_url)
  [ALB_URL]=$(out alb_url)
)
for k in "${!VARS[@]}"; do
  gh variable set "$k" --repo "$REPO" --body "${VARS[$k]}"
done
gh variable set AWS_DEPLOY_ENABLED --repo "$REPO" --body "${AWS_DEPLOY_ENABLED:-true}"
echo "GitHub variables set for $REPO"
