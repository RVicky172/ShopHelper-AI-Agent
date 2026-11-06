#!/usr/bin/env bash
# Run the evals against the local stack. Needs `docker compose up` and LM Studio.
# The host's .env is skipped because it holds AWS settings.
# EVAL_RUNS=3 scripts/evals_local.sh repeats the suite (default 1); it stops at the first failed run.
# 127.0.0.1, not localhost: on Windows, localhost tries IPv6 first and stalls.
set -euo pipefail
cd "$(dirname "$0")/.."

export RUN_EVALS=1
export SHOPHELPER_ENV_FILE=""
export LLM_PROVIDER=openai_compatible
export DATABASE_URL=postgresql://shophelper:shophelper@127.0.0.1:5432/shophelper
export TOOLS_TRANSPORT=mcp
export MCP_URL=http://127.0.0.1:8765/mcp
export INTERNAL_TOKEN_SECRET=local-development-only-not-a-real-secret-0123456789
export LOCAL_GUARDRAILS=true
export LANGSMITH_TRACING=false

reset_orders() {
  uv run python -c "
from shophelper.orders import get_order_repo
from shophelper.refunds import get_refund_store
get_refund_store().cancel_open()  # refund evals open real requests
get_order_repo().reset()"
}

trap reset_orders EXIT  # leave the demo orders clean, even after a failed or stopped run

for ((run = 1; run <= ${EVAL_RUNS:-1}; run++)); do
  echo "== eval run $run of ${EVAL_RUNS:-1}"
  reset_orders  # earlier refunds would fail cases
  # One event loop: the OpenAI client caches connections between tests.
  uv run pytest evals -q -o asyncio_default_test_loop_scope=session "$@"
done
