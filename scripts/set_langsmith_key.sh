#!/usr/bin/env bash
# Copy LANGSMITH_API_KEY from .env into SSM Parameter Store (SecureString), where the
# deployed app reads it at startup. The key never goes into Terraform state or git.
set -euo pipefail
cd "$(dirname "$0")/.."
REGION=${REGION:-ap-south-1}
KEY=$(grep -E '^LANGSMITH_API_KEY=' .env | cut -d= -f2- | tr -d '"\r')
[ -n "$KEY" ] || { echo "Set LANGSMITH_API_KEY in .env first"; exit 1; }
aws ssm put-parameter --region "$REGION" --name /shophelper/langsmith-api-key \
  --type SecureString --value "$KEY" --overwrite --query Version --output text >/dev/null
echo "Stored /shophelper/langsmith-api-key. New Lambda environments / ECS tasks will pick it up;"
echo "force it now with: scripts/release.sh (or aws ecs update-service --force-new-deployment)"
