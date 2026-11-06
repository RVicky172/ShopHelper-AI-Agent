"""Routes that exist only for the local learning UI.

Every route returns 404 unless accounts are enabled, so a deployed AWS API exposes none of them
(listing all orders on a public URL would be a data leak).
"""

import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from shophelper.agent.graph import request_refund
from shophelper.api.auth_routes import current_principal, require_role
from shophelper.core import db
from shophelper.core.config import get_settings
from shophelper.core.identity import Principal
from shophelper.rag import pipeline as rag
from shophelper.shop.orders import get_order_repo
from shophelper.shop.refunds import get_refund_store


def _local_only() -> None:
    if not get_settings().accounts_enabled:
        raise HTTPException(status_code=404)


router = APIRouter(dependencies=[Depends(_local_only)])


def _check(fn) -> dict[str, Any]:
    try:
        return {"ok": True, "detail": fn()}
    except Exception as exc:
        return {"ok": False, "detail": type(exc).__name__}


def _count_chunks() -> str:
    with db.connect() as conn:
        return f"{conn.execute('SELECT count(*) AS n FROM policy_chunks').fetchone()['n']} chunks"


def _list_models() -> str:
    return f"{len(rag._client().with_options(timeout=3).models.list().data)} models"


@router.get("/system")
def system(request: Request) -> dict[str, Any]:
    """What this running instance is wired to. The UI's status bar and Tools page read this."""
    s = get_settings()
    mcp_tools = [
        {"name": t.name, "description": t.description, "args": t.args, "via": s.tools_transport}
        for t in request.app.state.service.tools
    ]
    refund = {
        "name": request_refund.name, "description": request_refund.description,
        "args": request_refund.args, "via": "graph node (never MCP)",
    }
    return {
        "chat_model": s.local_chat_model,
        "embedding_model": s.embedding_model,
        "llm_base_url": s.llm_base_url,
        "tools_transport": s.tools_transport,
        "mcp_url": s.mcp_url,
        "guardrails": "local rules" if s.local_guardrails else "off",
        "max_steps": s.max_steps,
        "tools": [*mcp_tools, refund],
        "services": {"llm": _check(_list_models), "database": _check(_count_chunks)},
    }


@router.get("/orders")
def orders(principal: Annotated[Principal, Depends(current_principal)]) -> list[dict[str, Any]]:
    if principal.role == "customer":
        return get_order_repo().list_for_owner(principal.user_id)
    return get_order_repo().list_all()


@router.post("/demo/reset", dependencies=[Depends(require_role("admin"))])
def reset_orders() -> dict[str, str]:
    """Undo refunds made while testing. Open requests are cancelled, so they can't be decided."""
    get_refund_store().cancel_open()
    get_order_repo().reset()
    return {"status": "ok"}


@router.get("/rag/chunks")
def rag_chunks() -> list[dict[str, Any]]:
    """Every stored chunk, without its vector."""
    with db.connect() as conn:
        return conn.execute(
            "SELECT source, chunk_index, content AS text FROM policy_chunks ORDER BY source, chunk_index"
        ).fetchall()


@router.get("/rag/search")
def rag_search(
    q: str = Query(min_length=1, max_length=500), k: int = Query(4, ge=1, le=20)
) -> dict[str, Any]:
    """The agent's retrieval step on its own: no LLM involved, just vectors and SQL."""
    start = time.perf_counter()
    vector = rag.embed([q], rag.QUERY_PREFIX)[0]
    embed_ms = int((time.perf_counter() - start) * 1000)
    return {
        "query": q,
        "embedding_dimensions": len(vector),
        "embedding_preview": [round(v, 4) for v in vector[:8]],
        "embed_ms": embed_ms,
        "passages": rag.search(q, k),
    }
