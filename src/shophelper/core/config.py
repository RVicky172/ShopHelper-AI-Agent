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
    # MCP over HTTP (the docker-compose `mcp` service). Unset = spawn a stdio subprocess.
    mcp_url: str | None = None
    # Interface the MCP server binds to with --http. Containers need 0.0.0.0.
    mcp_host: str = "127.0.0.1"

    # --- Local stack (docker-compose). Every default below keeps the AWS behaviour. ---
    # bedrock = Claude on Bedrock; openai_compatible = any OpenAI-style server (LM Studio).
    llm_provider: Literal["bedrock", "openai_compatible"] = "bedrock"
    llm_base_url: str = "http://localhost:1234/v1"
    llm_api_key: str = "lm-studio"  # LM Studio ignores it, the OpenAI client requires one
    local_chat_model: str = "qwen/qwen3-30b-a3b-2507"
    embedding_model: str = "text-embedding-nomic-embed-text-v1.5"
    # Set = Postgres holds orders, history, checkpoints and embeddings (replaces DynamoDB + KB).
    database_url: str | None = None
    # Regex stand-in for the Bedrock Guardrail, used only when guardrail_id is unset.
    local_guardrails: bool = False

    # --- Accounts (feature 020). Off on AWS: see accounts_enabled. ---
    auth_enabled: bool = False  # lets offline tests use accounts without a database
    # Signs the short-lived token that carries a user's identity from the API to the MCP server.
    internal_token_secret: str | None = None
    web_origin: str = "http://localhost:5173"  # the site allowed to send state-changing requests
    extra_web_origins: str = ""  # comma-separated exact origins, for the same site under another name
    seed_demo_users: bool = False  # only docker-compose.yml turns this on
    # Label for metrics/logs: local | lambda | ecs
    runtime: str = "local"
    # LangSmith: key from env/.env locally, or from this SSM SecureString when deployed.
    langsmith_tracing: bool = True
    langsmith_project: str = "shophelper"
    langsmith_api_key: str | None = None
    langsmith_api_key_param: str | None = None


    @property
    def web_origins(self) -> set[str]:
        extra = (origin.strip() for origin in self.extra_web_origins.split(","))
        return {self.web_origin, *(origin for origin in extra if origin)}

    @property
    def accounts_enabled(self) -> bool:
        """A database always means accounts, so the local stack can't run without logins."""
        return self.auth_enabled or bool(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
