"""Step 6: the agent as a LangGraph state machine with a human-approval refund node.

    START -> agent --(no tool calls)--------------------------> END
               |  --(read-only tool calls)--> tools ----------> agent
               |  --(request_refund)--> refund_approval ------> agent
                                         (interrupt() pauses the graph until a
                                          human approves/rejects via /approve)

State is checkpointed per thread (= session_id) in DynamoDB, so a paused refund
survives across requests, processes and even different compute (Lambda vs ECS).
"""

from typing import Annotated, Any, TypedDict

from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, StructuredTool, tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from shophelper.config import get_settings
from shophelper.orders import get_order_repo, refund_eligibility
from shophelper.tools import get_order_status, search_policy

SYSTEM_PROMPT = """You are ShopHelper, a concise, friendly customer-support assistant for an \
online electronics store.

Rules:
- Use get_order_status to look up orders. Never guess order details.
- Use search_policy for ANY question about store policy, and answer only from the passages \
it returns. If the passages don't answer the question, say you don't know.
- To refund, first look up the order, then call request_refund on its own (no other tool in \
the same turn). Refunds always need human approval; never claim a refund is done until the \
tool result says it was approved.
- Never ask for card numbers, CVV, passwords or OTPs.
- Politely decline requests unrelated to the store, its orders or its policies.
"""


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


def build_graph(tools: list[BaseTool], checkpointer: BaseCheckpointSaver, llm: BaseChatModel):
    model = llm.bind_tools([*tools, request_refund])
    tools_by_name = {t.name: t for t in tools}

    async def run_tool(call: dict[str, Any]) -> ToolMessage:
        t = tools_by_name.get(call["name"])
        if t is None:
            return ToolMessage(f"Unknown tool {call['name']}", tool_call_id=call["id"], status="error")
        try:
            return await t.ainvoke(call)  # a ToolCall in -> a ToolMessage out
        except Exception as exc:  # surface tool failures to the model instead of crashing
            return ToolMessage(f"Tool error: {exc}", tool_call_id=call["id"], status="error")

    async def agent(state: State) -> dict:
        response = await model.ainvoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
        return {"messages": [response]}

    async def tools_node(state: State) -> dict:
        return {"messages": [await run_tool(c) for c in state["messages"][-1].tool_calls]}

    async def refund_approval(state: State) -> dict:
        # NB: on resume LangGraph re-runs this node from the top; interrupt() then
        # returns the human's decision instead of pausing. Side effects go after it.
        out = []
        for call in state["messages"][-1].tool_calls:
            if call["name"] != "request_refund":
                out.append(await run_tool(call))
                continue
            out.append(ToolMessage(_decide_refund(call["args"]), tool_call_id=call["id"]))
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


def _decide_refund(args: dict[str, Any]) -> str:
    repo = get_order_repo()
    order_id = str(args.get("order_id", "")).strip().lstrip("#")
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
