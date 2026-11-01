import os

# Must run before shophelper.config is imported: unit tests are offline-only.
os.environ["SHOPHELPER_ENV_FILE"] = ""
for var in ("ORDERS_TABLE", "HISTORY_TABLE", "CHECKPOINT_TABLE", "KNOWLEDGE_BASE_ID",
            "GUARDRAIL_ID", "LANGSMITH_TRACING", "LANGSMITH_API_KEY"):
    os.environ.pop(var, None)
