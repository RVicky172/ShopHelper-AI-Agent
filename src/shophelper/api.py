"""FastAPI front door for ShopHelper."""

import json
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from shophelper.config import get_settings
from shophelper.mcp_client import mcp_tools
from shophelper.memory import get_history_store
from shophelper.observability import log_event
from shophelper.schemas import ApprovalRequest, ChatRequest, ChatResponse
from shophelper.service import NoPendingApproval, ShopHelperService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Built once per process (per Lambda execution environment / ECS task).
    async with AsyncExitStack() as stack:
        if not hasattr(app.state, "service"):
            tools = None  # in-process tools
            if get_settings().tools_transport == "mcp":
                tools = await stack.enter_async_context(mcp_tools())
            app.state.service = ShopHelperService(tools=tools)
        yield


app = FastAPI(title="ShopHelper", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
async def chat(req: ChatRequest) -> ChatResponse:
    return await _observed("chat", req.session_id, app.state.service.chat(req.session_id, req.message))


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Server-sent events: `token` events while the model writes, then one `final` event.
    Streams through the ALB (ECS); API Gateway + Lambda buffers it into one response."""

    async def events():
        try:
            async for kind, data in app.state.service.stream(req.session_id, req.message):
                if kind == "final":
                    _log_turn("chat_stream", data)
                payload = data.model_dump() if kind == "final" else data
                yield f"event: {kind}\ndata: {json.dumps(payload)}\n\n"
        except Exception as exc:
            log_event("chat_error", endpoint="chat_stream", session_id=req.session_id, error=repr(exc)[:500])
            yield f"event: error\ndata: {json.dumps('Something went wrong')}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/approve", response_model=ChatResponse)
async def approve(req: ApprovalRequest) -> ChatResponse:
    """Human-in-the-loop: a support agent approves or rejects a pending refund."""
    try:
        return await _observed(
            "approve", req.session_id,
            app.state.service.approve(req.session_id, req.approved, req.reviewer, req.note),
        )
    except NoPendingApproval as exc:
        raise HTTPException(status_code=409, detail="No refund is pending for this session") from exc


@app.get("/sessions/{session_id}/history")
def session_history(session_id: str) -> list[dict]:
    return get_history_store().load(session_id, limit=50)
