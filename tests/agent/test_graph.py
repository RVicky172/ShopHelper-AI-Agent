import pytest
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import InMemorySaver

from fakes import ScriptedChatModel, call, say
from shophelper.agent.graph import NO_POLICY_ANSWER
from shophelper.agent.memory import InMemoryHistory
from shophelper.agent.service import NoPendingApproval, ShopHelperService
from shophelper.shop.orders import get_order_repo


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
    assert ("token", "Order 1002 has shipped.") in events
    kind, final = events[-1]
    assert kind == "final" and final.tools_used == ["get_order_status"]


# --- The model must not promise a refund it never requested ---

PROMISE = "I'll proceed with the refund request for $59.99. A human support agent will review it shortly."


async def test_a_refund_promise_without_a_request_is_retried():
    svc = service(
        call("get_order_status", {"order_id": "1001"}, "c1"),
        say(PROMISE),
        call("request_refund", {"order_id": "1001", "amount": 59.99, "reason": "broken"}, "c2"),
    )
    r = await svc.chat("session-promise-1", "I'd like a refund for order 1001")
    assert r.status == "pending_approval"


async def test_a_repeated_false_promise_never_reaches_the_customer():
    svc = service(call("get_order_status", {"order_id": "1001"}, "c1"), say(PROMISE), say(PROMISE))
    r = await svc.chat("session-promise-2", "I'd like a refund for order 1001")
    assert r.status == "answered"
    assert "review" not in r.answer and "haven't submitted" in r.answer


async def test_asking_to_confirm_a_refund_is_also_retried():
    svc = service(
        say("I can help you request a refund. Would you like me to go ahead?"),
        call("request_refund", {"order_id": "1001", "amount": 59.99, "reason": "broken"}, "c2"),
    )
    assert (await svc.chat("session-promise-3", "Refund 1001")).status == "pending_approval"


@pytest.mark.parametrize("answer", [
    "Refunds are reviewed by a human and take 5-7 business days.",
    "Our return window is 30 days, and refunds go to the original payment method.",
    "I can't refund that order, because it hasn't been delivered.",
    "I cannot process a refund for an order that was cancelled.",
    "Your order has shipped and should arrive on Friday.",
])
async def test_normal_answers_are_left_alone(answer):
    svc = service(say(answer), say("SHOULD NOT BE USED"))
    assert (await svc.chat("session-promise-4", "Tell me about refunds")).answer == answer


async def test_a_real_request_can_be_described_afterwards():
    svc = service(
        call("request_refund", {"order_id": "1001", "amount": 59.99, "reason": "broken"}, "c1"),
        say("I've processed your refund."),
        say("SHOULD NOT BE USED"),
    )
    await svc.chat("session-promise-5", "refund 1001")
    done = await svc.approve("session-promise-5", True, "alice")
    assert done.answer == "I've processed your refund."



# --- Care and warranty questions always search the policy (030) ---


def counted(*script):
    model = ScriptedChatModel(script=list(script))
    return model, ShopHelperService(llm=model, checkpointer=InMemorySaver(), history=InMemoryHistory())


@pytest.mark.parametrize("question", [
    "What is ShopHelper Care?",
    "what does shophelper care cost for a desk mat",
    "SHOPHELPER CARE for my mouse?",
    "How long is the warranty?",
    "Do your warranties cover water damage?",
    "Can I get extended coverage on a charger?",
    "Is there a protection plan for my headphones?",
])
async def test_a_protected_question_searches_before_the_model_answers(question):
    model, svc = counted(say("From the policy."))
    r = await svc.chat("session-care-1", question)
    assert r.tools_used == ["search_policy"] and r.answer == "From the policy."
    assert model.calls == 1  # the search costs no model call


@pytest.mark.parametrize("question", [
    "Take care!",
    "How do I contact customer care?",
    "Do you sell skincare?",
    "How do I care for my kettle?",
    "Please handle my order with care.",
    "I care about delivery times.",
    "Who takes care of returns?",
    "What's your coverage area for delivery?",
    "Is there a plan to add more colours?",
    "Can you protect my card details?",
])
async def test_a_near_miss_is_left_to_the_model(question):
    model, svc = counted(say("Happy to help."))
    r = await svc.chat("session-care-2", question)
    assert r.tools_used == [] and model.calls == 1


async def test_a_repeated_question_searches_again():
    _, svc = counted(say("From the policy."))
    first = await svc.chat("session-care-3", "What is ShopHelper Care?")
    second = await svc.chat("session-care-3", "What is ShopHelper Care?")
    assert first.tools_used == ["search_policy"] and second.tools_used == ["search_policy"]


async def test_no_answer_is_written_before_the_search():
    _, svc = counted(say("From the policy."))
    events = [kind for kind, _ in [e async for e in svc.stream("session-care-4", "What is ShopHelper Care?")]]
    assert events.index("tool_end") < events.index("token")


def failing_search(query: str) -> dict:
    """Search store policies."""
    raise RuntimeError("the search is down")


async def test_a_failed_search_gives_an_honest_reply_without_the_model():
    model = ScriptedChatModel(script=[say("SHOULD NOT BE USED")])
    svc = ShopHelperService(
        tools=[StructuredTool.from_function(failing_search, name="search_policy")],
        llm=model, checkpointer=InMemorySaver(), history=InMemoryHistory(),
    )
    r = await svc.chat("session-care-5", "What is ShopHelper Care?")
    assert r.answer == NO_POLICY_ANSWER and model.calls == 0


async def test_a_failed_search_on_another_topic_is_left_to_the_model():
    model = ScriptedChatModel(
        script=[call("search_policy", {"query": "fee"}), say("Sorry, I can't check that.")]
    )
    svc = ShopHelperService(
        tools=[StructuredTool.from_function(failing_search, name="search_policy")],
        llm=model, checkpointer=InMemorySaver(), history=InMemoryHistory(),
    )
    r = await svc.chat("session-care-6", "Is there a restocking fee?")
    assert r.answer == "Sorry, I can't check that."


async def test_a_refund_that_mentions_a_warranty_still_reaches_a_human():
    svc = service(
        call("get_order_status", {"order_id": "1006"}, "c1"),
        call("request_refund", {"order_id": "1006", "amount": 249.0, "reason": "faulty"}, "c2"),
        say("Your refund has been approved."),
    )
    r = await svc.chat("session-care-7", "It's under warranty, please refund order 1006")
    assert r.status == "pending_approval" and r.tools_used[0] == "search_policy"
    done = await svc.approve("session-care-7", approved=True, reviewer="alice")
    assert done.answer == "Your refund has been approved." and "search_policy" not in done.tools_used
