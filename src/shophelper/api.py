"""FastAPI front door for ShopHelper."""

from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI, HTTPException

from shophelper.config import get_settings
from shophelper.mcp_client import mcp_tools
from shophelper.memory import get_history_store
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


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    return await app.state.service.chat(req.session_id, req.message)


@app.post("/approve", response_model=ChatResponse)
async def approve(req: ApprovalRequest) -> ChatResponse:
    """Human-in-the-loop: a support agent approves or rejects a pending refund."""
    try:
        return await app.state.service.approve(req.session_id, req.approved, req.reviewer, req.note)
    except NoPendingApproval as exc:
        raise HTTPException(status_code=409, detail="No refund is pending for this session") from exc


@app.get("/sessions/{session_id}/history")
def session_history(session_id: str) -> list[dict]:
    return get_history_store().load(session_id, limit=50)
