"""One turn of ShopHelper: guardrail -> LangGraph agent -> guardrail -> history.

Shared by the HTTP API and the eval suite so both exercise exactly the same path.
"""

import json
import re
import time
from collections.abc import AsyncIterator
from typing import Any, Literal, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.errors import GraphRecursionError
from langgraph.types import Command

from shophelper.agent import guardrails
from shophelper.agent.graph import build_graph, default_checkpointer, default_llm, local_tools
from shophelper.agent.memory import HistoryStore, get_history_store
from shophelper.agent.schemas import ChatResponse
from shophelper.agent.tools import NoIdentity
from shophelper.core.config import get_settings
from shophelper.core.identity import Principal
from shophelper.core.observability import init_tracing
from shophelper.shop.refunds import get_refund_store


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
        init_tracing()  # before the first LLM call, so LangSmith picks it up
        self.tools = tools if tools is not None else local_tools()
        self.graph = build_graph(
            self.tools,
            checkpointer or default_checkpointer(),
            llm or default_llm(),
        )
        self.history = history or get_history_store()

    def _config(self, session_id: str, user_id: int | None = None) -> RunnableConfig:
        if self.settings.accounts_enabled and user_id is None:
            raise NoIdentity  # a forgotten argument must fail loudly, never leak
        # Each agent->tools round trip is 2 graph steps; +1 for the final answer.
        return {
            "configurable": {"thread_id": session_id, "user_id": user_id},
            "recursion_limit": 2 * self.settings.max_steps + 1,
        }

    async def _prepare(
        self, session_id: str, guard_in: guardrails.GuardResult, user_id: int | None
    ) -> tuple[ChatResponse | None, Any]:
        """Acts on the input guardrail + pending-approval check. Returns an early response or
        graph input."""
        config = self._config(session_id, user_id)
        if guard_in.blocked:
            return ChatResponse(session_id=session_id, status="blocked", answer=guard_in.text), None
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

    async def chat(self, session_id: str, message: str, principal: Principal | None = None) -> ChatResponse:
        start = time.perf_counter()
        user_id = principal.user_id if principal else None
        early, prepared = await self._prepare(session_id, guardrails.check(message, "INPUT"), user_id)
        if early:
            return early
        graph_input, config, seen = prepared
        return await self._run(graph_input, config, session_id, seen, start)

    async def stream(
        self, session_id: str, message: str, principal: Principal | None = None
    ) -> AsyncIterator[tuple[str, Any]]:
        """Yields one (event, data) pair per step of the turn.

        See docs/learn/06-building-the-app/03-streaming.md.

        guardrail -> [model_step -> tool_start -> tool_end]* -> token* -> guardrail -> final

        Trade-off: tokens reach the user before the output guardrail sees the full answer.
        If it intervenes, the "final" event carries the replacement text and the client
        must swap it in. Use /chat when that is not acceptable.
        """
        start = time.perf_counter()
        user_id = principal.user_id if principal else None
        self._config(session_id, user_id)  # refuse before anything is sent
        guard_in = guardrails.check(message, "INPUT")
        yield "guardrail", _guard_event("input", guard_in, message)
        early, prepared = await self._prepare(session_id, guard_in, user_id)
        if early:
            yield "final", early
            return
        graph_input, config, seen = prepared
        async for event in self._stream_graph(graph_input, config, session_id, seen, start):
            yield event

    async def approve_stream(
        self, session_id: str, approved: bool, reviewer: str, note: str = "", owner_id: int | None = None
    ) -> AsyncIterator[tuple[str, Any]]:
        """Same events as stream(), for the agent's reply after a human decision."""
        start = time.perf_counter()
        config, seen, resume = await self._resume(session_id, approved, reviewer, note, owner_id)
        async for event in self._stream_graph(resume, config, session_id, seen, start):
            yield event

    async def _stream_graph(
        self, graph_input, config, session_id, seen, start
    ) -> AsyncIterator[tuple[str, Any]]:
        step_started = time.perf_counter()
        steps = 0
        try:
            # Two views of one run: "messages" = model tokens, "updates" = each finished node.
            async for mode, payload in self.graph.astream(
                graph_input, config, stream_mode=["messages", "updates"]
            ):
                if mode == "messages":
                    chunk, meta = cast(tuple[Any, dict[str, Any]], payload)
                    # Streaming models emit AIMessageChunks; non-streaming ones one AIMessage.
                    if meta.get("langgraph_node") == "agent" and isinstance(chunk, AIMessage):
                        if chunk.text:
                            yield "token", chunk.text
                    continue
                for node, update in cast(dict[str, Any], payload).items():
                    if node == "__interrupt__":
                        yield "interrupt", update[0].value
                        continue
                    for m in (update or {}).get("messages", []):
                        elapsed, step_started = _ms(step_started), time.perf_counter()
                        if isinstance(m, AIMessage):
                            steps += 1
                            yield "model_step", _model_step(m, steps, elapsed)
                            for c in m.tool_calls:
                                yield "tool_start", {"id": c["id"], "name": c["name"], "args": c["args"]}
                        elif isinstance(m, ToolMessage):
                            yield "tool_end", _tool_end(m, elapsed)
        except GraphRecursionError:
            yield "final", _gave_up(session_id, start)
            return
        snapshot = await self.graph.aget_state(config)
        interrupts = [i.value for i in snapshot.interrupts]
        user_id = config["configurable"]["user_id"]
        final = self._finish(session_id, snapshot.values["messages"][seen:], interrupts, start, user_id)
        if final.guardrail_action != "skipped":
            yield "guardrail", {
                "stage": "output", "action": final.guardrail_action, "reasons": final.guardrail_reasons,
            }
        yield "final", final

    async def _resume(self, session_id: str, approved: bool, reviewer: str, note: str, owner_id: int | None):
        # The graph resumes as the customer, because it's their conversation and their order.
        # The reviewer is only a name in the decision, so their access never reaches the tools.
        config = self._config(session_id, owner_id)
        snapshot = await self.graph.aget_state(config)
        if not snapshot.interrupts:
            raise NoPendingApproval(session_id)
        seen = len(snapshot.values["messages"])
        resume = {"approved": approved, "reviewer": reviewer, "note": note}
        return config, seen, Command(resume=resume)

    async def approve(
        self, session_id: str, approved: bool, reviewer: str, note: str = "", owner_id: int | None = None
    ):
        start = time.perf_counter()
        config, seen, resume = await self._resume(session_id, approved, reviewer, note, owner_id)
        return await self._run(resume, config, session_id, seen, start)

    async def pending_refund(self, session_id: str, owner_id: int) -> dict[str, Any] | None:
        snapshot = await self.graph.aget_state(self._config(session_id, owner_id))
        return snapshot.interrupts[0].value if snapshot.interrupts else None

    async def queue_pending_refund(self, session_id: str, owner_id: int) -> None:
        """A resumed turn can ask for another refund while the first is still being closed."""
        pending = await self.pending_refund(session_id, owner_id)
        if pending:
            get_refund_store().open(session_id, owner_id, pending)

    async def _run(self, graph_input, config, session_id, seen, start) -> ChatResponse:
        try:
            result = await self.graph.ainvoke(graph_input, config)
        except GraphRecursionError:
            return _gave_up(session_id, start)
        interrupts = [i.value for i in result.get("__interrupt__", [])]
        user_id = config["configurable"]["user_id"]
        return self._finish(session_id, result["messages"][seen:], interrupts, start, user_id)

    def _finish(self, session_id, new_messages, interrupts, start, user_id: Any = None) -> ChatResponse:
        response = _summarise(session_id, new_messages)
        if interrupts:
            if self.settings.accounts_enabled:
                get_refund_store().open(session_id, user_id, interrupts[0])
            response.status = "pending_approval"
            response.pending_refund = interrupts[0]
            response.answer = (
                f"I've submitted a refund request of ${interrupts[0]['amount']:.2f} for "
                f"order {interrupts[0]['order_id']}. A support agent will review it shortly."
            )
        else:
            # Guardrail AFTER the loop: never return PII or unsafe content.
            guard_out = guardrails.check(response.answer, "OUTPUT")
            response.guardrail_action = _guard_action(guard_out, response.answer)
            response.guardrail_reasons = guard_out.reasons
            response.answer = guard_out.text
            if guard_out.blocked:
                response.status = "blocked"
        self.history.append(session_id, "assistant", response.answer)
        response.latency_ms = _ms(start)
        return response


def _guard_action(
    guard: guardrails.GuardResult, original: str
) -> Literal["passed", "masked", "blocked", "skipped"]:
    if guard.blocked:
        return "blocked"
    return "masked" if guard.text != original else "passed"


def _guard_event(stage: str, guard: guardrails.GuardResult, original: str) -> dict[str, Any]:
    return {"stage": stage, "action": _guard_action(guard, original), "reasons": guard.reasons}


def _model_step(m: AIMessage, step: int, elapsed_ms: int) -> dict[str, Any]:
    usage = m.usage_metadata or {}
    return {
        "step": step,
        "tool_calls": [c["name"] for c in m.tool_calls],
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "ms": elapsed_ms,
    }


def _tool_end(m: ToolMessage, elapsed_ms: int) -> dict[str, Any]:
    return {
        "id": m.tool_call_id,
        "name": m.name or "request_refund",  # the refund node builds its ToolMessage by hand
        "status": m.status,
        "result": _tool_result(m.content),
        "ms": elapsed_ms,
    }


def _tool_result(content: Any) -> Any:
    """Tool output as data. In-process tools give a JSON string, MCP gives text blocks."""
    if isinstance(content, list):
        content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    try:
        return json.loads(content)
    except (TypeError, ValueError):
        return content


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
