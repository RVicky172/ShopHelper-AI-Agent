"""One turn of ShopHelper: guardrail -> LangGraph agent -> guardrail -> history.

Shared by the HTTP API and the eval suite so both exercise exactly the same path.
"""

import re
import time
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.errors import GraphRecursionError
from langgraph.types import Command

from shophelper import guardrails
from shophelper.config import get_settings
from shophelper.graph import build_graph, default_checkpointer, default_llm, local_tools
from shophelper.memory import HistoryStore, get_history_store
from shophelper.schemas import ChatResponse


class NoPendingApproval(Exception):
    pass


class ShopHelperService:
    def __init__(
        self,
        tools: list[BaseTool] | None = None,
        llm: BaseChatModel | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        history: HistoryStore | None = None,
    ) -> None:
        self.settings = get_settings()
        self.graph = build_graph(
            tools if tools is not None else local_tools(),
            checkpointer or default_checkpointer(),
            llm or default_llm(),
        )
        self.history = history or get_history_store()

    def _config(self, session_id: str) -> dict[str, Any]:
        # Each agent->tools round trip is 2 graph steps; +1 for the final answer.
        return {
            "configurable": {"thread_id": session_id},
            "recursion_limit": 2 * self.settings.max_steps + 1,
        }

    async def _prepare(self, session_id: str, message: str):
        """Input guardrail + pending-approval check. Returns an early response or graph input."""
        guard_in = guardrails.check(message, "INPUT")
        if guard_in.blocked:
            return ChatResponse(session_id=session_id, status="blocked", answer=guard_in.text), None
        config = self._config(session_id)
        snapshot = await self.graph.aget_state(config)
        if snapshot.interrupts:  # a refund is waiting for a human; don't start a new run
            return ChatResponse(
                session_id=session_id,
                status="pending_approval",
                answer="Your refund request is waiting for a support agent's approval.",
                pending_refund=snapshot.interrupts[0].value,
            ), None
        seen = len(snapshot.values.get("messages", [])) if snapshot.values else 0
        self.history.append(session_id, "user", guard_in.text)  # masked text only
        return None, ({"messages": [HumanMessage(guard_in.text)]}, config, seen)

    async def chat(self, session_id: str, message: str) -> ChatResponse:
        start = time.perf_counter()
        early, prepared = await self._prepare(session_id, message)
        if early:
            return early
        graph_input, config, seen = prepared
        return await self._run(graph_input, config, session_id, seen, start)

    async def stream(self, session_id: str, message: str) -> AsyncIterator[tuple[str, Any]]:
        """Yields ("token", text) while the agent writes, then ("final", ChatResponse).

        Trade-off: tokens reach the user before the output guardrail sees the full answer.
        If it intervenes, the "final" event carries the replacement text and the client
        must swap it in. Use /chat when that is not acceptable.
        """
        start = time.perf_counter()
        early, prepared = await self._prepare(session_id, message)
        if early:
            yield "final", early
            return
        graph_input, config, seen = prepared
        try:
            async for chunk, meta in self.graph.astream(graph_input, config, stream_mode="messages"):
                # Streaming models emit AIMessageChunks; non-streaming ones one AIMessage.
                if meta.get("langgraph_node") == "agent" and isinstance(chunk, AIMessage):
                    if chunk.text:
                        yield "token", chunk.text
        except GraphRecursionError:
            yield "final", _gave_up(session_id, start)
            return
        snapshot = await self.graph.aget_state(config)
        interrupts = [i.value for i in snapshot.interrupts]
        yield "final", self._finish(session_id, snapshot.values["messages"][seen:], interrupts, start)

    async def approve(self, session_id: str, approved: bool, reviewer: str, note: str = ""):
        start = time.perf_counter()
        config = self._config(session_id)
        snapshot = await self.graph.aget_state(config)
        if not snapshot.interrupts:
            raise NoPendingApproval(session_id)
        seen = len(snapshot.values["messages"])
        resume = {"approved": approved, "reviewer": reviewer, "note": note}
        return await self._run(Command(resume=resume), config, session_id, seen, start)

    async def _run(self, graph_input, config, session_id, seen, start) -> ChatResponse:
        try:
            result = await self.graph.ainvoke(graph_input, config)
        except GraphRecursionError:
            return _gave_up(session_id, start)
        interrupts = [i.value for i in result.get("__interrupt__", [])]
        return self._finish(session_id, result["messages"][seen:], interrupts, start)

    def _finish(self, session_id, new_messages, interrupts, start) -> ChatResponse:
        response = _summarise(session_id, new_messages)
        if interrupts:
            response.status = "pending_approval"
            response.pending_refund = interrupts[0]
            response.answer = (
                f"I've submitted a refund request of ${interrupts[0]['amount']:.2f} for "
                f"order {interrupts[0]['order_id']}. A support agent will review it shortly."
            )
        else:
            # Guardrail AFTER the loop: never return PII or unsafe content.
            guard_out = guardrails.check(response.answer, "OUTPUT")
            response.answer = guard_out.text
            if guard_out.blocked:
                response.status = "blocked"
        self.history.append(session_id, "assistant", response.answer)
        response.latency_ms = _ms(start)
        return response


def _gave_up(session_id: str, start: float) -> ChatResponse:
    """Max-steps guard tripped (GraphRecursionError)."""
    return ChatResponse(
        session_id=session_id,
        answer="Sorry, I couldn't finish that request. A human agent will follow up.",
        latency_ms=_ms(start),
    )


def _summarise(session_id: str, messages: list) -> ChatResponse:
    tools_used, citations, tokens_in, tokens_out, answer = [], [], 0, 0, ""
    for m in messages:
        if isinstance(m, AIMessage):
            tools_used += [c["name"] for c in m.tool_calls]
            usage = m.usage_metadata or {}
            tokens_in += usage.get("input_tokens", 0)
            tokens_out += usage.get("output_tokens", 0)
            if m.text:
                answer = m.text
        elif isinstance(m, ToolMessage) and m.name == "search_policy":
            # Works for both in-process (JSON) and MCP (text block) tool output.
            for src in re.findall(r'"source":\s*"([^"]+)"', str(m.content)):
                if src not in citations:
                    citations.append(src)
    return ChatResponse(
        session_id=session_id,
        answer=answer,
        tools_used=tools_used,
        citations=citations,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
    )


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)
