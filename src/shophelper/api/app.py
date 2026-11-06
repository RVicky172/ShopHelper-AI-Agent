"""FastAPI front door for ShopHelper."""

import json
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from shophelper.accounts.conversations import get_conversation_store
from shophelper.agent.graph import postgres_checkpointer
from shophelper.agent.memory import get_history_store
from shophelper.agent.schemas import ChatResponse
from shophelper.agent.service import NoPendingApproval, ShopHelperService
from shophelper.api.auth_routes import AccountsGate, accounts_only, current_principal, require_role
from shophelper.api.auth_routes import router as auth_router
from shophelper.api.local_routes import router as local_router
from shophelper.api.schemas import ApprovalRequest, ChatRequest
from shophelper.api.shop_routes import router as shop_router
from shophelper.core.config import get_settings
from shophelper.core.identity import Principal
from shophelper.core.observability import log_event
from shophelper.mcp.client import mcp_tools
from shophelper.shop.orders import get_order_repo
from shophelper.shop.refunds import RefundRequest, ReviewForbidden, authorize_review, get_refund_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Built once per process (per Lambda execution environment / ECS task).
    async with AsyncExitStack() as stack:
        if not hasattr(app.state, "service"):
            settings = get_settings()
            tools = None  # in-process tools
            if settings.tools_transport == "mcp":
                tools = await stack.enter_async_context(mcp_tools())
            checkpointer = None  # DynamoDB or in-memory, see graph.default_checkpointer
            if settings.database_url:
                checkpointer = await stack.enter_async_context(postgres_checkpointer())
            app.state.service = ShopHelperService(tools=tools, checkpointer=checkpointer)
        yield


app = FastAPI(title="ShopHelper", version="0.2.0", lifespan=lifespan)
app.add_middleware(AccountsGate)  # passes everything through unless accounts are enabled
app.include_router(auth_router)  # every route in it returns 404 unless accounts are enabled
app.include_router(local_router)  # every route in it returns 404 unless DATABASE_URL is set
app.include_router(shop_router)  # every route in it returns 404 unless accounts are enabled


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


NOT_FOUND = HTTPException(status_code=404, detail="No such conversation")


def _owned_by_caller(request: Request, session_id: str) -> Principal | None:
    """The caller, if this conversation is theirs. Someone else's and a missing one both give the
    same 404. With accounts off (AWS) there is no caller, and any session id is accepted."""
    if not get_settings().accounts_enabled:
        return None
    principal = current_principal(request)
    if get_conversation_store().owner_of(session_id) != principal.user_id:
        raise NOT_FOUND
    return principal


def _log_turn(endpoint: str, resp: ChatResponse) -> None:
    log_event(
        "chat_completed", endpoint=endpoint, session_id=resp.session_id, status=resp.status,
        tools=resp.tools_used, input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
        latency_ms=resp.latency_ms,
    )


async def _observed(endpoint: str, session_id: str, coro):
    try:
        resp = await coro
    except Exception as exc:
        log_event("chat_error", endpoint=endpoint, session_id=session_id, error=repr(exc)[:500])
        raise
    _log_turn(endpoint, resp)
    return resp


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    principal = await run_in_threadpool(_owned_by_caller, request, req.session_id)
    turn = app.state.service.chat(req.session_id, req.message, principal)
    return await _observed("chat", req.session_id, turn)


def _sse(endpoint: str, session_id: str, stream) -> StreamingResponse:
    """Turns (event, data) pairs from the service into server-sent events."""

    async def events():
        try:
            async for kind, data in stream:
                if kind == "final":
                    _log_turn(endpoint, data)
                payload = data.model_dump() if kind == "final" else data
                yield f"event: {kind}\ndata: {json.dumps(payload)}\n\n"
        except NoPendingApproval:
            yield f"event: error\ndata: {json.dumps('No refund is pending for this session')}\n\n"
        except Exception as exc:
            log_event("chat_error", endpoint=endpoint, session_id=session_id, error=repr(exc)[:500])
            yield f"event: error\ndata: {json.dumps('Something went wrong')}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request) -> StreamingResponse:
    """Server-sent events: one event per step of the turn, ending with `final`.
    Streams through the ALB (ECS); API Gateway + Lambda buffers it into one response."""
    principal = await run_in_threadpool(_owned_by_caller, request, req.session_id)
    stream = app.state.service.stream(req.session_id, req.message, principal)
    return _sse("chat_stream", req.session_id, stream)


@dataclass(frozen=True)
class Review:
    refund: RefundRequest
    reviewer: Principal


NOTHING_PENDING = HTTPException(status_code=409, detail="No refund is pending for this session")


def _start_review(request: Request, req: ApprovalRequest) -> Review | None:
    """Checks every rule, then claims the request. Returns None with accounts off (AWS)."""
    if not get_settings().accounts_enabled:
        return None
    reviewer = current_principal(request)
    if reviewer.role == "customer":  # before any lookup, so it reveals nothing about the session
        raise HTTPException(status_code=403, detail="Only support staff can review refunds")
    store = get_refund_store()
    refund = store.open_for_session(req.session_id)
    if refund is None or refund.status != "pending":
        raise NOTHING_PENDING
    try:
        authorize_review(refund, reviewer)
    except ReviewForbidden as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not store.claim(refund.id, reviewer.user_id, req.note):
        raise NOTHING_PENDING  # another reviewer got there first
    return Review(refund, reviewer)


def _decision(req: ApprovalRequest, review: Review | None) -> tuple:
    if review is None:
        return req.session_id, req.approved, req.reviewer, req.note
    who = review.reviewer.display_name
    return req.session_id, req.approved, who, req.note, review.refund.owner_id


async def _close_review(review: Review | None, approved: bool) -> None:
    if review:
        get_refund_store().finish(review.refund.id, approved)
        await app.state.service.queue_pending_refund(review.refund.session_id, review.refund.owner_id)


@app.post("/approve/stream")
async def approve_stream(req: ApprovalRequest, request: Request) -> StreamingResponse:
    """Same as /approve, streaming the agent's reply as /chat/stream does."""
    review = await run_in_threadpool(_start_review, request, req)

    async def stream():
        async for event in app.state.service.approve_stream(*_decision(req, review)):
            yield event
        await _close_review(review, req.approved)

    return _sse("approve_stream", req.session_id, stream())


@app.post("/approve", response_model=ChatResponse)
async def approve(req: ApprovalRequest, request: Request) -> ChatResponse:
    """Human-in-the-loop: a support agent approves or rejects a pending refund."""
    review = await run_in_threadpool(_start_review, request, req)
    try:
        decided = app.state.service.approve(*_decision(req, review))
        response = await _observed("approve", req.session_id, decided)
    except NoPendingApproval as exc:
        raise NOTHING_PENDING from exc
    await _close_review(review, req.approved)
    return response


@app.get(
    "/refunds/pending",
    dependencies=[Depends(accounts_only), Depends(require_role("support", "admin"))],
)
def pending_refunds() -> list[dict]:
    rows = []
    for refund in get_refund_store().list_open():
        order = get_order_repo().get(refund.order_id) or {}
        rows.append({
            "id": refund.id, "session_id": refund.session_id, "order_id": refund.order_id,
            "customer": order.get("customer", ""), "item": order.get("item", ""),
            "amount": refund.amount, "reason": refund.reason,
            "needs_supervisor": refund.needs_supervisor, "status": refund.status,
        })
    return rows


@app.get("/sessions/{session_id}/history")
def session_history(session_id: str, request: Request) -> list[dict]:
    _owned_by_caller(request, session_id)
    return get_history_store().load(session_id, limit=50)


@app.post("/conversations", status_code=201, dependencies=[Depends(accounts_only)])
def create_conversation(principal: Annotated[Principal, Depends(current_principal)]) -> dict[str, str]:
    return {"id": get_conversation_store().create(principal.user_id)}


@app.get("/conversations", dependencies=[Depends(accounts_only)])
def list_conversations(principal: Annotated[Principal, Depends(current_principal)]) -> list[dict]:
    return get_conversation_store().list_for(principal.user_id)


@app.get("/conversations/{session_id}", dependencies=[Depends(accounts_only)])
async def open_conversation(session_id: str, request: Request) -> dict:
    principal = await run_in_threadpool(_owned_by_caller, request, session_id)
    messages = await run_in_threadpool(get_history_store().load, session_id, 50)
    # accounts_only has already ruled out a missing principal
    pending = await app.state.service.pending_refund(session_id, principal.user_id)  # pyright: ignore[reportOptionalMemberAccess]
    if pending and not await run_in_threadpool(get_refund_store().open_for_session, session_id):
        pending = None  # cancelled by a demo reset
    return {"id": session_id, "messages": messages, "pending_refund": pending}
