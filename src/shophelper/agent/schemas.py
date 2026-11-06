"""What the agent returns for one turn."""

from typing import Literal

from pydantic import BaseModel


class ChatResponse(BaseModel):
    session_id: str
    status: Literal["answered", "pending_approval", "blocked"] = "answered"
    answer: str
    tools_used: list[str] = []
    citations: list[str] = []
    pending_refund: dict | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    guardrail_action: Literal["passed", "masked", "blocked", "skipped"] = "skipped"
    guardrail_reasons: list[str] = []
