"""FastAPI front door for ShopHelper."""

import time

from fastapi import FastAPI, HTTPException

from shophelper.raw_agent import MaxStepsExceeded, run_agent
from shophelper.schemas import ChatRequest, ChatResponse

app = FastAPI(title="ShopHelper", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    start = time.perf_counter()
    try:
        result = run_agent(req.message)
    except MaxStepsExceeded as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChatResponse(
        session_id=req.session_id,
        answer=result.answer,
        tools_used=result.tools_used,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )
