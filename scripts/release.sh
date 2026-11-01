#!/usr/bin/env bash
# Build the image, push it to ECR and roll it out to Lambda and ECS.
# Used by CI (step 11) and locally. Needs: aws, docker, python.
#   REGION=ap-south-1 NAME=shophelper TAG=<git sha> scripts/release.sh
#   PUSH_ONLY=1 scripts/release.sh      # build + push, no rollout (first deploy)
set -euo pipefail
cd "$(dirname "$0")/.."

REGION=${REGION:-ap-south-1}
NAME=${NAME:-shophelper}
TAG=${TAG:-$(git rev-parse --short HEAD)}
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
IMAGE="$REGISTRY/$NAME:$TAG"

# Tags are immutable in ECR, so an existing tag is reused rather than re-pushed.
if aws ecr describe-images --region "$REGION" --repository-name "$NAME"      --image-ids "imageTag=$TAG" >/dev/null 2>&1; then
  echo "==> $IMAGE already in ECR"
else
  echo "==> Building $IMAGE"
  aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"
  # --provenance=false: Lambda rejects multi-manifest (attestation) image indexes.
  docker build --platform linux/amd64 --provenance=false -t "$IMAGE" .
  docker push "$IMAGE"
fi
[ "${PUSH_ONLY:-0}" = 1 ] && exit 0

echo "==> Lambda"
aws lambda update-function-code --region "$REGION" --function-name "$NAME" --image-uri "$IMAGE" \
  --query LastUpdateStatus --output text
aws lambda wait function-updated-v2 --region "$REGION" --function-name "$NAME"

if aws ecs describe-services --region "$REGION" --cluster "$NAME" --services "$NAME" \
     --query "services[?status=='ACTIVE'] | length(@)" --output text 2>/dev/null | grep -q 1; then
  echo "==> ECS"
  mkdir -p build && TD_FILE=build/taskdef.json  # repo-relative: works for Windows aws.exe too
  aws ecs describe-task-definition --region "$REGION" --task-definition "$NAME" \
    --query taskDefinition --output json > "$TD_FILE"
  # Swap the image and keep only the fields register-task-definition accepts.
  python - "$TD_FILE" "$IMAGE" <<'PY'
import json, sys
path, image = sys.argv[1], sys.argv[2]
td = json.load(open(path))
td["containerDefinitions"][0]["image"] = image
keep = ["family", "taskRoleArn", "executionRoleArn", "networkMode", "containerDefinitions",
        "requiresCompatibilities", "cpu", "memory", "runtimePlatform"]
json.dump({k: td[k] for k in keep if k in td}, open(path, "w"))
PY
  TD_ARN=$(aws ecs register-task-definition --region "$REGION" --cli-input-json "file://$TD_FILE" \
    --query taskDefinition.taskDefinitionArn --output text)
  aws ecs update-service --region "$REGION" --cluster "$NAME" --service "$NAME" \
    --task-definition "$TD_ARN" --query service.taskDefinition --output text
  aws ecs wait services-stable --region "$REGION" --cluster "$NAME" --services "$NAME"
  rm -f "$TD_FILE"
else
  echo "==> ECS disabled (enable_ecs=false) - skipped"
fi
echo "==> Released $TAG"
