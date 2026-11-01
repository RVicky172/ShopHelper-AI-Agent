#!/usr/bin/env bash
# Remove everything this project created in AWS, and switch CI back to tests-only.
set -euo pipefail
cd "$(dirname "$0")/.."
REGION=${REGION:-ap-south-1}

terraform -chdir=infra destroy -input=false -auto-approve
aws ssm delete-parameter --region "$REGION" --name /shophelper/langsmith-api-key 2>/dev/null \
  && echo "Deleted SSM /shophelper/langsmith-api-key" || echo "No SSM LangSmith parameter"
scripts/set_github_vars.sh off || echo "Could not update GitHub variables (gh not logged in?)"

echo
echo "Leftovers check (should be empty):"
aws resourcegroupstaggingapi get-resources --region "$REGION" \
  --tag-filters Key=Project,Values=ShopHelper --query "ResourceTagMappingList[].ResourceARN" --output text
