"""Golden-set evals: the full production path (guardrails + LangGraph + Bedrock + KB + DynamoDB).

    RUN_EVALS=1 uv run pytest evals -v
"""

import uuid
from contextlib import nullcontext
from pathlib import Path

import pytest
import yaml
from langchain_core.messages import ToolMessage

from judge import judge_faithfulness
from shophelper import auth
from shophelper.config import get_settings
from shophelper.mcp_client import mcp_tools
from shophelper.orders import demo_email, get_order_repo
from shophelper.service import ShopHelperService

CASES = yaml.safe_load(Path(__file__).with_name("golden_cases.yaml").read_text())
MIN_FAITHFULNESS = 4


def _tools_context():
    return mcp_tools() if get_settings().tools_transport == "mcp" else nullcontext(None)


def _principal(case: dict):
    """Each case runs as the customer named in `as:`. With accounts off (AWS) nobody is signed in."""
    if not get_settings().accounts_enabled:
        return None
    store = auth.get_user_store()
    return auth.to_principal(store.get_by_email(demo_email(case["as"])))


def _failures(case: dict, resp, answer: str) -> list[str]:
    exp, errors = case["expect"], []
    for tool in exp.get("tools", []):
        if tool not in resp.tools_used:
            errors.append(f"tool {tool} not called (called {resp.tools_used})")
    if "status" in exp and resp.status != exp["status"]:
        errors.append(f"status {resp.status} != {exp['status']}")
    if "status_in" in exp and resp.status not in exp["status_in"]:
        errors.append(f"status {resp.status} not in {exp['status_in']}")
    if "contains_any" in exp and not any(s.lower() in answer for s in exp["contains_any"]):
        errors.append(f"answer lacks any of {exp['contains_any']}")
    for bad in exp.get("not_contains", []):
        if bad.lower() in answer:
            errors.append(f"answer contains forbidden '{bad}'")
    for order_id, status in exp.get("orders_after", {}).items():
        actual = get_order_repo().get(order_id)["status"]
        if actual != status:
            errors.append(f"order {order_id} is {actual}, expected {status}")
    return errors


@pytest.mark.evals
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
async def test_golden(case, record):
    if case["id"].startswith("xuser_") and not get_settings().accounts_enabled:
        pytest.skip("cross-user cases need accounts, which are local only")
    session_id = f"eval-{case['id'].replace('_', '-')}-{uuid.uuid4().hex[:6]}"
    async with _tools_context() as tools:
        svc = ShopHelperService(tools=tools)
        resp = await svc.chat(session_id, case["message"], _principal(case))
        state = await svc.graph.aget_state({"configurable": {"thread_id": session_id}})

    answer = resp.answer.lower().replace("’", "'")  # models also write curly apostrophes
    errors = _failures(case, resp, answer)

    verdict = None
    if case["expect"].get("judge") and resp.status == "answered":
        passages = [
            str(m.content) for m in (state.values or {}).get("messages", [])
            if isinstance(m, ToolMessage) and m.name == "search_policy"
        ]
        verdict = judge_faithfulness(case["message"], passages, resp.answer)
        if verdict.get("score", 0) < MIN_FAITHFULNESS:
            errors.append(f"faithfulness {verdict.get('score')}: {verdict.get('reason')}")

    record({
        "id": case["id"], "attack": case.get("attack", False), "passed": not errors,
        "errors": errors, "status": resp.status, "tools": resp.tools_used,
        "answer": resp.answer, "judge": verdict, "latency_ms": resp.latency_ms,
        "input_tokens": resp.input_tokens, "output_tokens": resp.output_tokens,
    })
    assert not errors, errors
