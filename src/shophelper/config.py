"""Runtime settings, read from environment variables (and a local .env file)."""

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Tests set SHOPHELPER_ENV_FILE="" so a developer .env never leaks into them.
    model_config = SettingsConfigDict(
        env_file=os.getenv("SHOPHELPER_ENV_FILE", ".env") or None, extra="ignore"
    )

    aws_region: str = "ap-south-1"
    agent_model_id: str = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    judge_model_id: str = "global.anthropic.claude-sonnet-4-6"
    max_tokens: int = 1024
    # Hard cap on model calls per user turn - stops runaway tool loops.
    max_steps: int = 6

    # Unset tables/KB/guardrail fall back to local implementations so the agent
    # runs on a laptop before any infrastructure exists.
    orders_table: str | None = None
    history_table: str | None = None
    history_ttl_days: int = 30
    history_turns: int = 10
    checkpoint_table: str | None = None
    checkpoint_ttl_days: int = 7
    knowledge_base_id: str | None = None
    guardrail_id: str | None = None
    guardrail_version: str = "DRAFT"

    tools_transport: Literal["local", "mcp"] = "local"
    # Label for metrics/logs: local | lambda | ecs
    runtime: str = "local"
    # LangSmith: key from env/.env locally, or from this SSM SecureString when deployed.
    langsmith_tracing: bool = True
    langsmith_project: str = "shophelper"
    langsmith_api_key: str | None = None
    langsmith_api_key_param: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
