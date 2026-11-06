#!/usr/bin/env bash
# Compare the two deployments: cold start, warm latency and streaming.
#   scripts/compare_deployments.sh
set -euo pipefail
cd "$(dirname "$0")/.."
REGION=${REGION:-ap-south-1}
API=$(terraform -chdir=infra output -raw api_gateway_url)
ALB=$(terraform -chdir=infra output -raw alb_url)
Q='{"session_id":"SID","message":"How much does express shipping cost?"}'

chat() {  # url -> total seconds
  curl -s -o /dev/null -w "%{time_total}" -X POST "$1/chat" -H 'content-type: application/json' \
    -d "${Q/SID/cmp-$RANDOM$RANDOM}"
}
ttfb() {  # url -> "first token / total" for the SSE endpoint
  # Not curl's time_starttransfer: step events (guardrail, tool calls) arrive before any token.
  local start first="" now
  start=$(date +%s.%N)
  while IFS= read -r line; do
    if [[ -z "$first" && "$line" == "event: token"* ]]; then first=$(date +%s.%N); fi
  done < <(curl -sN -X POST "$1/chat/stream" -H 'content-type: application/json'     -d "${Q/SID/cmp-$RANDOM$RANDOM}")
  now=$(date +%s.%N)
  awk -v s="$start" -v f="${first:-$now}" -v n="$now"     'BEGIN { printf "%.3fs first token / %.3fs total", f - s, n - s }'
}

echo "== Lambda cold start (forcing a new execution environment)"
aws lambda update-function-configuration --region "$REGION" --function-name shophelper \
  --description "cold-start probe $(date +%s)" --query LastUpdateStatus --output text >/dev/null
aws lambda wait function-updated-v2 --region "$REGION" --function-name shophelper
echo "  /health cold : $(curl -s -o /dev/null -w '%{time_total}' "$API/health")s"
echo "  /health warm : $(curl -s -o /dev/null -w '%{time_total}' "$API/health")s"

for name in "Lambda+APIGW:$API" "ECS+ALB:$ALB"; do
  label=${name%%:*}; url=${name#*:}
  echo "== $label"
  echo "  /chat warm x3 : $(chat "$url")s  $(chat "$url")s  $(chat "$url")s"
  echo "  /chat/stream  : $(ttfb "$url")"
done

echo "== Lambda REPORT lines (Init Duration = cold start)"
MSYS_NO_PATHCONV=1 aws logs filter-log-events --region "$REGION" --log-group-name /aws/lambda/shophelper \
  --start-time $(( ($(date +%s) - 600) * 1000 )) --filter-pattern REPORT \
  --query "events[].message" --output text | grep -o "Init Duration: [0-9.]* ms" | tail -3 || true
