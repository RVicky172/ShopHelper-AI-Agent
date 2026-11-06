"""Step 1: the raw agent loop - no framework, just the Bedrock Converse API.

The model either answers (stopReason == "end_turn") or asks for a tool
(stopReason == "tool_use"); we run the tool, append the result and loop,
up to max_steps model calls.
"""

import json
from dataclasses import dataclass, field
from typing import Any

import boto3

from shophelper.config import get_settings
from shophelper.tools import get_order_status, search_policy

SYSTEM_PROMPT = (
    "You are ShopHelper, a concise and friendly customer-support assistant for a general online "
    "store selling electronics, home and kitchen goods, bags and travel gear, and fitness and "
    "outdoor products. Use get_order_status to look up orders and search_policy for any "
    "question about store policy, including the ShopHelper Care extended warranty - never "
    "guess order details or policy. If you cannot help, say so."
)

TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_order_status",
                "description": "Look up an order by its numeric order ID (e.g. '1001').",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"order_id": {"type": "string"}},
                        "required": ["order_id"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "search_policy",
                "description": "Search store policies: returns, refunds, shipping, warranty, "
                "cancellation, payments, privacy, price adjustments.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    }
                },
            }
        },
    ]
}


class MaxStepsExceeded(RuntimeError):
    pass


@dataclass
class AgentResult:
    answer: str
    messages: list[dict[str, Any]]
    tools_used: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


TOOLS = {"get_order_status": get_order_status, "search_policy": search_policy}


def run_agent(
    question: str,
    history: list[dict[str, Any]] | None = None,
    client: Any = None,
) -> AgentResult:
    settings = get_settings()
    client = client or boto3.client("bedrock-runtime", region_name=settings.aws_region)
    messages = list(history or []) + [{"role": "user", "content": [{"text": question}]}]
    result = AgentResult(answer="", messages=messages)

    for _ in range(settings.max_steps):
        response = client.converse(
            modelId=settings.agent_model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig=TOOL_CONFIG,
            inferenceConfig={"maxTokens": settings.max_tokens, "temperature": 0},
        )
        result.input_tokens += response["usage"]["inputTokens"]
        result.output_tokens += response["usage"]["outputTokens"]
        message = response["output"]["message"]
        messages.append(message)

        if response["stopReason"] != "tool_use":
            result.answer = "".join(b.get("text", "") for b in message["content"])
            return result

        tool_results = []
        for block in message["content"]:
            if "toolUse" not in block:
                continue
            call = block["toolUse"]
            result.tools_used.append(call["name"])
            fn = TOOLS.get(call["name"])
            output = fn(**call["input"]) if fn else {"error": f"Unknown tool {call['name']}"}
            tool_results.append(
                {"toolResult": {"toolUseId": call["toolUseId"], "content": [{"json": output}]}}
            )
        messages.append({"role": "user", "content": tool_results})

    raise MaxStepsExceeded(f"Agent did not finish within {settings.max_steps} steps")


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Where is my order 1002?"
    r = run_agent(q)
    print(r.answer)
    print(json.dumps({"tools": r.tools_used, "in": r.input_tokens, "out": r.output_tokens}))
