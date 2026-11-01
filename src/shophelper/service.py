"""One turn of ShopHelper: guardrail -> LangGraph agent -> guardrail -> history.

Shared by the HTTP API and the eval suite so both exercise exactly the same path.
"""

import re
import time
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

    async def chat(self, session_id: str, message: str) -> ChatResponse:
        start = time.perf_counter()
        guard_in = guardrails.check(message, "INPUT")
        if guard_in.blocked:
            return ChatResponse(session_id=session_id, status="blocked", answer=guard_in.text)

        config = self._config(session_id)
        snapshot = await self.graph.aget_state(config)
        if snapshot.interrupts:  # a refund is waiting for a human; don't start a new run
            return ChatResponse(
                session_id=session_id,
                status="pending_approval",
                answer="Your refund request is waiting for a support agent's approval.",
                pending_refund=snapshot.interrupts[0].value,
            )

        seen = len(snapshot.values.get("messages", [])) if snapshot.values else 0
        self.history.append(session_id, "user", guard_in.text)  # masked text only
        return await self._run(
            {"messages": [HumanMessage(guard_in.text)]}, config, session_id, seen, start
        )

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
            return ChatResponse(
                session_id=session_id,
                answer="Sorry, I couldn't finish that request. A human agent will follow up.",
                latency_ms=_ms(start),
            )

        new = result["messages"][seen:]
        response = _summarise(session_id, new)
        if result.get("__interrupt__"):
            response.status = "pending_approval"
            response.pending_refund = result["__interrupt__"][0].value
            response.answer = (
                f"I've submitted a refund request of ${response.pending_refund['amount']:.2f} for "
                f"order {response.pending_refund['order_id']}. A support agent will review it shortly."
            )
        else:
            guard_out = guardrails.check(response.answer, "OUTPUT")
            response.answer = guard_out.text
            if guard_out.blocked:
                response.status = "blocked"
        self.history.append(session_id, "assistant", response.answer)
        response.latency_ms = _ms(start)
        return response


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
