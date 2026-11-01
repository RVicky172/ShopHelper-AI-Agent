import pytest
from langgraph.checkpoint.memory import InMemorySaver

from fakes import ScriptedChatModel, call, say
from shophelper.memory import InMemoryHistory
from shophelper.orders import get_order_repo
from shophelper.service import NoPendingApproval, ShopHelperService


@pytest.fixture(autouse=True)
def fresh_orders():
    get_order_repo.cache_clear()
    yield
    get_order_repo.cache_clear()


def service(*script):
    return ShopHelperService(
        llm=ScriptedChatModel(script=list(script)),
        checkpointer=InMemorySaver(),
        history=InMemoryHistory(),
    )


async def test_refund_pauses_for_human_then_completes():
    svc = service(
        call("get_order_status", {"order_id": "1006"}, "c1"),
        call("request_refund", {"order_id": "1006", "amount": 249.0, "reason": "damaged"}, "c2"),
        say("Your refund has been approved."),
    )
    r = await svc.chat("session-1", "Refund order 1006, it arrived damaged")
    assert r.status == "pending_approval"
    assert r.pending_refund["amount"] == 249.0 and r.pending_refund["needs_supervisor"] is True
    assert get_order_repo().get("1006")["status"] == "delivered"  # nothing happened yet

    again = await svc.chat("session-1", "Any update?")
    assert again.status == "pending_approval"

    done = await svc.approve("session-1", approved=True, reviewer="alice")
    assert done.status == "answered" and "approved" in done.answer
    assert get_order_repo().get("1006")["status"] == "refunded"


async def test_rejected_refund_does_not_change_order():
    svc = service(
        call("request_refund", {"order_id": "1001", "amount": 59.99, "reason": "changed mind"}),
        say("Sorry, the refund was rejected."),
    )
    assert (await svc.chat("session-2", "refund 1001")).status == "pending_approval"
    await svc.approve("session-2", approved=False, reviewer="bob", note="used item")
    assert get_order_repo().get("1001")["status"] == "delivered"


async def test_ineligible_refund_never_reaches_a_human():
    svc = service(
        call("request_refund", {"order_id": "1004", "amount": 89.0, "reason": "broken"}),
        say("That order is outside the 30-day refund window."),
    )
    r = await svc.chat("session-3", "refund 1004")
    assert r.status == "answered" and r.pending_refund is None
    state = await svc.graph.aget_state({"configurable": {"thread_id": "session-3"}})
    assert "refund window" in state.values["messages"][-2].content


async def test_policy_answer_has_citations():
    svc = service(call("search_policy", {"query": "restocking fee opened electronics"}),
                  say("There is a 10% restocking fee."))
    r = await svc.chat("session-4", "Is there a restocking fee?")
    assert r.tools_used == ["search_policy"] and "returns.md" in r.citations
    assert r.input_tokens == 220


async def test_max_steps_guard_returns_graceful_answer():
    svc = service(call("get_order_status", {"order_id": "1001"}))  # loops forever
    r = await svc.chat("session-5", "loop")
    assert r.status == "answered" and "couldn't finish" in r.answer


async def test_approve_without_pending_refund():
    with pytest.raises(NoPendingApproval):
        await service(say("hi")).approve("session-6", True, "alice")


async def test_stream_yields_tokens_then_final():
    svc = service(call("get_order_status", {"order_id": "1002"}), say("Order 1002 has shipped."))
    events = [e async for e in svc.stream("session-7", "where is 1002")]
    assert events[0] == ("token", "Order 1002 has shipped.")
    kind, final = events[-1]
    assert kind == "final" and final.tools_used == ["get_order_status"]
