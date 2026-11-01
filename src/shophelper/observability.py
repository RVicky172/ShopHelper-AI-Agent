"""Step 10: structured logs (-> CloudWatch metric filters) and LangSmith tracing setup.

One JSON line per turn on stdout. CloudWatch metric filters (infra/observability.tf)
turn these into Requests / InputTokens / OutputTokens / LatencyMs / Errors /
GuardrailBlocks metrics - identical for Lambda and ECS, no agent or SDK needed.
"""

import json
import os
import sys
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from shophelper.config import get_settings

_tracing_initialised = False


def log_event(event: str, **fields: Any) -> None:
    record = {"event": event, "runtime": get_settings().runtime, "ts": time.time(), **fields}
    print(json.dumps(record, default=str), file=sys.stdout, flush=True)


def init_tracing() -> None:
    """Enable LangSmith if a key is available: env/.env locally, SSM SecureString when deployed.

    LangChain/LangGraph trace automatically once LANGSMITH_TRACING/LANGSMITH_API_KEY are set
    in os.environ (pydantic-settings reads .env but doesn't export it, so we do).
    """
    global _tracing_initialised
    if _tracing_initialised:
        return
    _tracing_initialised = True
    s = get_settings()
    key = os.getenv("LANGSMITH_API_KEY") or s.langsmith_api_key
    if not key and s.langsmith_api_key_param:
        try:
            key = boto3.client("ssm", region_name=s.aws_region).get_parameter(
                Name=s.langsmith_api_key_param, WithDecryption=True
            )["Parameter"]["Value"]
        except (ClientError, BotoCoreError) as exc:
            log_event("tracing_disabled", reason=type(exc).__name__)
            return
    if not key or not s.langsmith_tracing:
        return
    os.environ["LANGSMITH_API_KEY"] = key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ.setdefault("LANGSMITH_PROJECT", s.langsmith_project)
    log_event("tracing_enabled", project=os.environ["LANGSMITH_PROJECT"])
