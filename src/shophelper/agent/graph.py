"""Step 6: the agent as a LangGraph state machine with a human-approval refund node.

    START -> agent --(no tool calls)--------------------------> END
               |  --(read-only tool calls)--> tools ----------> agent
               |  --(request_refund)--> refund_approval ------> agent
                                         (interrupt() pauses the graph until a
                                          human approves/rejects via /approve)

State is checkpointed per thread (= session_id) in DynamoDB, so a paused refund
survives across requests, processes and even different compute (Lambda vs ECS).
"""

import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any, TypedDict, cast

from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool, tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from shophelper.agent.tools import get_order_status, search_policy
from shophelper.core import identity
from shophelper.core.config import get_settings
from shophelper.shop.orders import get_order_repo, refund_eligibility

SYSTEM_PROMPT = """You are ShopHelper, a concise, friendly customer-support assistant for a \
general online store selling electronics, home and kitchen goods, bags and travel gear, and \
fitness and outdoor products.

Rules:
- Whenever a message names an order number, call get_order_status before replying, even if \
the order came up earlier: its status may have changed. Never guess order details.
- You know nothing about this store's policies or services until you search. Call \
search_policy before answering ANY question about them, including yes/no questions and \
questions about what a customer can buy, such as warranties or ShopHelper Care. Answer only \
from the passages it returns. If the passages don't answer the question, say you don't know.
- To refund, first look up the order, then call request_refund on its own (no other tool in \
the same turn). Don't ask the customer to confirm first: a human reviews every request. Use \
the order total unless the customer names a smaller amount. Refunds always need human \
approval; never claim a refund is done until the tool result says it was approved.
- Never say you will do something: if an action is needed, call the tool now, in this reply.
- Never ask for card numbers, CVV, passwords or OTPs.
- {EMAIL} and {PHONE} mark contact details hidden for privacy. Ignore them and answer the rest \
of the message.
- Politely decline requests unrelated to the store, its orders or its policies.
"""


# A model can write "I'll process your refund" and stop without calling the tool, leaving the
# customer waiting for a review that doesn't exist. A prompt rule only reduced this, so code checks.
REFUND_PROMISE = re.compile(
    r"\b(i'll|i will|i've|i have|i can(?!'t|not)|let me|proceeding)\b[^.!?\n]{0,80}\brefund", re.IGNORECASE
)
REFUND_NUDGE = (
    "You offered or promised a refund but did not call request_refund, so nothing was submitted. "
    "Call request_refund now, or tell the customer plainly why you can't. Don't ask them to confirm."
)
NO_REFUND_SUBMITTED = (
    "I haven't submitted a refund request yet. Please ask again, with your order number and the reason."
)


# Asked about "ShopHelper Care", the model reads a product it doesn't know, skips search_policy and
# answers anyway. Two prompt rewrites reached 12 of 24, so for these topics code searches first.
POLICY_TOPIC = re.compile(
    r"\b(shophelper care|warrant(y|ies)|extended coverage|protection plan)\b", re.IGNORECASE
)
NO_POLICY_ANSWER = (
    "I couldn't check our policy just now, so I don't want to guess. Please ask again, or contact support."
)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


@tool
def request_refund(order_id: str, amount: float, reason: str) -> str:
    """Request a refund for a delivered order. A human support agent must approve it."""
    raise RuntimeError("Handled by the refund_approval node, never executed directly")


def local_tools() -> list[BaseTool]:
    """Read-only tools, in-process. (Step 7 swaps these for the MCP server's tools.)"""
    return [StructuredTool.from_function(get_order_status), StructuredTool.from_function(search_policy)]


def default_llm() -> BaseChatModel:
    s = get_settings()
    if s.llm_provider == "openai_compatible":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=s.local_chat_model, base_url=s.llm_base_url, api_key=s.llm_api_key,
            # max_tokens is a pydantic alias the stubs don't show
            temperature=0, max_tokens=s.max_tokens, stream_usage=True,  # pyright: ignore[reportCallIssue]
        )
    return ChatBedrockConverse(
        model=s.agent_model_id, region_name=s.aws_region, temperature=0, max_tokens=s.max_tokens
    )


def default_checkpointer() -> BaseCheckpointSaver:
    s = get_settings()
    if s.checkpoint_table:
        from langgraph_checkpoint_aws import DynamoDBSaver

        return DynamoDBSaver(
            table_name=s.checkpoint_table,
            region_name=s.aws_region,
            ttl_seconds=s.checkpoint_ttl_days * 86400,
        )
    return InMemorySaver()


@asynccontextmanager
async def postgres_checkpointer() -> AsyncIterator[BaseCheckpointSaver]:
    """Checkpoints in Postgres, for the local stack. A pool, because the graph is async."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool

    kwargs = {"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row}
    url = cast(str, get_settings().database_url)  # only called when it's set
    async with AsyncConnectionPool(url, kwargs=kwargs, open=False) as pool:
        saver = AsyncPostgresSaver(cast(Any, pool))
        await saver.setup()  # creates the checkpoint* tables
        yield saver


def build_graph(tools: list[BaseTool], checkpointer: BaseCheckpointSaver, llm: BaseChatModel):
    model = llm.bind_tools([*tools, request_refund])
    tools_by_name = {t.name: t for t in tools}

    async def run_tool(call: Any, config: RunnableConfig) -> ToolMessage:
        t = tools_by_name.get(call["name"])
        if t is None:
            return ToolMessage(f"Unknown tool {call['name']}", tool_call_id=call["id"], status="error")
        try:
            # Identity comes from the graph's config, which only our code writes. The model's
            # output is `call`, and nothing in it is used to decide whose data is read.
            with identity.acting_as(_user_id(config)):
                return await t.ainvoke(call)  # a ToolCall in -> a ToolMessage out
        except Exception as exc:  # surface tool failures to the model instead of crashing
            return ToolMessage(f"Tool error: {exc}", tool_call_id=call["id"], status="error")

    async def agent(state: State) -> dict:
        if _needs_policy_search(state["messages"]):
            return {"messages": [_search_first(state["messages"])]}
        if _policy_search_failed(state["messages"]):
            return {"messages": [AIMessage(NO_POLICY_ANSWER)]}  # no passages, so nothing to answer from
        context = [SystemMessage(SYSTEM_PROMPT), *state["messages"]]
        response = await model.ainvoke(context)
        if _promises_unrequested_refund(response, state["messages"]):
            response = await model.ainvoke([*context, response, HumanMessage(REFUND_NUDGE)])
            if _promises_unrequested_refund(response, state["messages"]):
                response = AIMessage(NO_REFUND_SUBMITTED)  # honest beats a promise nobody will keep
        return {"messages": [response]}

    async def tools_node(state: State, config: RunnableConfig) -> dict:
        return {"messages": [await run_tool(c, config) for c in _last_calls(state)]}

    async def refund_approval(state: State, config: RunnableConfig) -> dict:
        # NB: on resume LangGraph re-runs this node from the top; interrupt() then
        # returns the human's decision instead of pausing. Side effects go after it.
        out = []
        for call in _last_calls(state):
            if call["name"] != "request_refund":
                out.append(await run_tool(call, config))
                continue
            refund = _decide_refund(call["args"], _user_id(config))
            out.append(ToolMessage(refund, tool_call_id=call["id"]))
        return {"messages": out}

    def route(state: State) -> str:
        calls = getattr(state["messages"][-1], "tool_calls", None)
        if not calls:
            return END
        return "refund_approval" if any(c["name"] == "request_refund" for c in calls) else "tools"

    g = StateGraph(State)
    g.add_node("agent", agent)
    g.add_node("tools", tools_node)
    g.add_node("refund_approval", refund_approval)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", route, ["tools", "refund_approval", END])
    g.add_edge("tools", "agent")
    g.add_edge("refund_approval", "agent")
    return g.compile(checkpointer=checkpointer)


def _last_calls(state: State) -> list[Any]:
    """Only reached after `route` saw tool calls on the last message."""
    return cast(AIMessage, state["messages"][-1]).tool_calls


def _current_turn(messages: list[AnyMessage]) -> tuple[str, list[AnyMessage]]:
    """The customer's latest message, and everything that has happened since."""
    last_human = max((i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=-1)
    return (messages[last_human].text if last_human >= 0 else ""), messages[last_human + 1:]


def _search_call_ids(turn: list[AnyMessage]) -> set[str]:
    calls = [c for m in turn if isinstance(m, AIMessage) for c in m.tool_calls]
    return {cast(str, c["id"]) for c in calls if c["name"] == "search_policy"}


def _needs_policy_search(messages: list[AnyMessage]) -> bool:
    """True for a protected question that this turn hasn't searched for yet."""
    question, turn = _current_turn(messages)
    return bool(POLICY_TOPIC.search(question)) and not _search_call_ids(turn)


def _search_first(messages: list[AnyMessage]) -> AIMessage:
    """A tool call written by code, not the model. The graph runs it like any other."""
    question, _ = _current_turn(messages)
    call = {"name": "search_policy", "args": {"query": question}, "id": f"code-{uuid.uuid4().hex}"}
    return AIMessage("", tool_calls=[call])


def _policy_search_failed(messages: list[AnyMessage]) -> bool:
    """True for a protected question whose every search this turn returned an error."""
    question, turn = _current_turn(messages)
    if not POLICY_TOPIC.search(question):
        return False
    ids = _search_call_ids(turn)
    results = [m for m in turn if isinstance(m, ToolMessage) and m.tool_call_id in ids]
    return bool(results) and all(m.status == "error" for m in results)


def _promises_unrequested_refund(response: AIMessage, messages: list[AnyMessage]) -> bool:
    """True if the model talks as if it's handling a refund, but this turn never requested one."""
    if response.tool_calls or not REFUND_PROMISE.search(response.text.replace("\u2019", "'")):
        return False
    _, turn = _current_turn(messages)
    return not any(
        c["name"] == "request_refund" for m in turn if isinstance(m, AIMessage) for c in m.tool_calls
    )


def _user_id(config: RunnableConfig) -> int | None:
    return config.get("configurable", {}).get("user_id")


def _decide_refund(args: dict[str, Any], user_id: int | None) -> str:
    repo = get_order_repo()
    order_id = str(args.get("order_id", "")).strip().lstrip("#")
    if get_settings().accounts_enabled:
        order = repo.get_for_owner(order_id, user_id)
    else:
        order = repo.get(order_id)
    if not order:
        return f"Refund not possible: no order {order_id}."
    amount = float(args.get("amount") or order["total"])
    ok, why = refund_eligibility(order, amount)
    if not ok:  # deterministic policy check - don't waste a human's time
        return f"Refund not possible: {why}"

    decision = interrupt({
        "order_id": order_id,
        "item": order["item"],
        "order_total": order["total"],
        "amount": amount,
        "reason": args.get("reason", ""),
        "needs_supervisor": amount > 200,
    })
    reviewer = decision.get("reviewer", "support")
    if not decision.get("approved"):
        return f"Refund REJECTED by human reviewer {reviewer}. Note: {decision.get('note') or 'none'}"
    repo.mark_refunded(order_id, amount, args.get("reason", ""))
    return (
        f"Refund of ${amount:.2f} for order {order_id} APPROVED by {reviewer}. It goes back to the "
        "original payment method within 5-7 business days."
    )
