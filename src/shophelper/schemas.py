"""Request/response models for the HTTP API."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$",
        description="Client-generated conversation id; reuse it to continue a conversation.",
    )
    message: str = Field(min_length=1, max_length=2000)


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


class ApprovalRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    approved: bool
    reviewer: str = Field(min_length=1, max_length=64)
    note: str = Field(default="", max_length=500)
