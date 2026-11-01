"""FastAPI front door for ShopHelper."""

import time

from fastapi import FastAPI, HTTPException

from shophelper import guardrails
from shophelper.config import get_settings
from shophelper.memory import get_history_store, to_converse_messages
from shophelper.raw_agent import MaxStepsExceeded, run_agent
from shophelper.schemas import ChatRequest, ChatResponse

app = FastAPI(title="ShopHelper", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    start = time.perf_counter()
    history = get_history_store()

    # Guardrail BEFORE the loop: block attacks/PII, or continue with masked text.
    guard_in = guardrails.check(req.message, "INPUT")
    if guard_in.blocked:
        return ChatResponse(session_id=req.session_id, status="blocked", answer=guard_in.text)
    message = guard_in.text

    past = history.load(req.session_id, limit=get_settings().history_turns)
    try:
        result = run_agent(message, history=to_converse_messages(past))
    except MaxStepsExceeded as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Guardrail AFTER the loop: never return PII or unsafe content.
    guard_out = guardrails.check(result.answer, "OUTPUT")
    answer = guard_out.text
    history.append(req.session_id, "user", message)  # masked text only - no raw PII stored
    history.append(req.session_id, "assistant", answer)
    return ChatResponse(
        session_id=req.session_id,
        status="blocked" if guard_out.blocked else "answered",
        answer=answer,
        tools_used=result.tools_used,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )


@app.get("/sessions/{session_id}/history")
def session_history(session_id: str) -> list[dict]:
    return get_history_store().load(session_id, limit=50)
