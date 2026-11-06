"""Read-only tool implementations shared by the raw loop, the LangGraph agent and the MCP server."""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import boto3

from shophelper import identity
from shophelper.config import get_settings
from shophelper.orders import get_order_repo

LOCAL_POLICY_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "policies"


class NoIdentity(Exception):
    """Accounts are on but nobody is named. Refusing is safer than returning any data."""


def get_order_status(order_id: str) -> dict[str, Any]:
    """Look up an order by its numeric id (e.g. '1001')."""
    clean_id = order_id.strip().lstrip("#")
    if get_settings().accounts_enabled:
        user_id = identity.current_user()
        if user_id is None:
            raise NoIdentity
        order = get_order_repo().get_for_owner(clean_id, user_id)
    else:
        order = get_order_repo().get(clean_id)
    return order or {"error": f"No order found with id {order_id}"}


@lru_cache
def _kb_client():
    return boto3.client("bedrock-agent-runtime", region_name=get_settings().aws_region)


def search_policy(query: str, top_k: int = 4) -> dict[str, Any]:
    """Search store policies (returns, refunds, shipping, warranty, payments, privacy...)."""
    settings = get_settings()
    if settings.database_url:  # local stack: our own pgvector pipeline (see rag.py)
        from shophelper import rag

        return {"passages": rag.search(query, top_k)}
    kb_id = settings.knowledge_base_id
    if not kb_id:
        return {"passages": _local_search(query, top_k)}
    resp = _kb_client().retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": top_k}},
    )
    return {
        "passages": [
            {
                "source": r["location"]["s3Location"]["uri"].rsplit("/", 1)[-1],
                "score": round(r.get("score", 0.0), 3),
                "text": r["content"]["text"],
            }
            for r in resp["retrievalResults"]
        ]
    }


def _local_search(query: str, top_k: int) -> list[dict[str, Any]]:
    """Keyword-overlap fallback so the agent works offline before the KB exists."""
    words = set(re.findall(r"[a-z]{3,}", query.lower()))
    scored = []
    for path in LOCAL_POLICY_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        score = len(words & set(re.findall(r"[a-z]{3,}", text.lower())))
        scored.append({"source": path.name, "score": score, "text": text})
    return sorted(scored, key=lambda p: p["score"], reverse=True)[:top_k]
