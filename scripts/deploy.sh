#!/usr/bin/env bash
# Full deploy from a laptop: infrastructure + image + rollout to Lambda and ECS.
set -euo pipefail
cd "$(dirname "$0")/.."
export TAG=${TAG:-$(git rev-parse --short HEAD)}

terraform -chdir=infra init -input=false
# Lambda/ECS need an image to exist: create ECR first, push, then everything else.
terraform -chdir=infra apply -input=false -auto-approve -target=aws_ecr_repository.app
PUSH_ONLY=1 scripts/release.sh
terraform -chdir=infra apply -input=false -auto-approve -var "image_tag=$TAG"
scripts/release.sh            # roll the tag out (covers re-deploys after the first)
scripts/env_from_terraform.sh
terraform -chdir=infra output
