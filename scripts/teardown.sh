#!/usr/bin/env bash
# Remove everything this project created in AWS, and switch CI back to tests-only.
set -euo pipefail
cd "$(dirname "$0")/.."
REGION=${REGION:-ap-south-1}

terraform -chdir=infra destroy -input=false -auto-approve
# Task definition revisions registered by release.sh are outside Terraform state.
revs=$(aws ecs list-task-definitions --region "$REGION" --family-prefix shophelper --status ACTIVE   --query "taskDefinitionArns" --output text)
for arn in $revs; do aws ecs deregister-task-definition --region "$REGION" --task-definition "$arn" >/dev/null; done
revs=$(aws ecs list-task-definitions --region "$REGION" --family-prefix shophelper --status INACTIVE   --query "taskDefinitionArns" --output text)
[ -n "$revs" ] && aws ecs delete-task-definitions --region "$REGION" --task-definitions $revs >/dev/null   && echo "Deleted ECS task definitions"
aws ssm delete-parameter --region "$REGION" --name /shophelper/langsmith-api-key 2>/dev/null \
  && echo "Deleted SSM /shophelper/langsmith-api-key" || echo "No SSM LangSmith parameter"
scripts/set_github_vars.sh off || echo "Could not update GitHub variables (gh not logged in?)"

echo
echo "Leftovers check (should be empty; deleted ECS items can linger in this index for a while):"
aws resourcegroupstaggingapi get-resources --region "$REGION" \
  --tag-filters Key=Project,Values=ShopHelper --query "ResourceTagMappingList[].ResourceARN" --output text
