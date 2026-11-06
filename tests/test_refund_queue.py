"""Refund review: only staff decide, by rules that read stored values, never the request."""

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from fakes import ScriptedChatModel, call, say
from shophelper import api, auth
from shophelper.config import get_settings
from shophelper.conversations import get_conversation_store
from shophelper.memory import get_history_store
from shophelper.orders import demo_email, get_order_repo
from shophelper.refunds import get_refund_store
from shophelper.service import ShopHelperService


def clear_caches():
    for cache in (auth.get_user_store, get_order_repo, get_conversation_store, get_history_store,
                  get_refund_store):
        cache.cache_clear()


@pytest.fixture(autouse=True)
def accounts_on(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "seed_demo_users", True)
    clear_caches()
    get_order_repo().assign_owners(auth.seed_demo_users(auth.get_user_store()))
    previous = getattr(api.app.state, "service", None)
    yield
    api.app.state.service = previous
    clear_caches()


def script(*steps):
    api.app.state.service = ShopHelperService(
        llm=ScriptedChatModel(script=list(steps)), checkpointer=InMemorySaver(), history=get_history_store()
    )


def signed_in(name):
    client = TestClient(api.app)
    r = client.post("/auth/login", json={"email": demo_email(name), "password": auth.DEMO_PASSWORD})
    assert r.status_code == 200
    return client


def request_refund(customer, order_id, amount, *after):
    """A customer asks for a refund, and the conversation pauses."""
    script(call("request_refund", {"order_id": order_id, "amount": amount, "reason": "damaged"}),
           *(after or [say("Your refund was decided.")]))
    client = signed_in(customer)
    session = client.post("/conversations").json()["id"]
    r = client.post("/chat", json={"session_id": session, "message": "refund please"})
    assert r.json()["status"] == "pending_approval"
    return client, session


def decide(client, session, approved=True, **extra):
    return client.post("/approve", json={"session_id": session, "approved": approved, **extra})


def status_of(order_id):
    return get_order_repo().get(order_id)["status"]


def tool_messages(session):
    state = api.app.state.service.graph.get_state({"configurable": {"thread_id": session}})
    return [m.content for m in state.values["messages"] if isinstance(m, ToolMessage)]


# --- AC-15: customers can't approve ---

def test_a_customer_cant_approve_their_own_refund():
    client, session = request_refund("Asha", "1001", 59.99)
    assert decide(client, session).status_code == 403
    assert status_of("1001") == "delivered"


def test_a_customer_cant_approve_on_the_stream_route_either():
    client, session = request_refund("Asha", "1001", 59.99)
    r = client.post("/approve/stream", json={"session_id": session, "approved": True})
    assert r.status_code == 403
    assert status_of("1001") == "delivered"


def test_a_customer_cant_approve_someone_elses_refund():
    _, session = request_refund("Asha", "1001", 59.99)
    assert decide(signed_in("Ravi"), session).status_code == 403


def test_the_customer_sees_their_refund_is_waiting():
    client, session = request_refund("Asha", "1001", 59.99)
    pending = client.get(f"/conversations/{session}").json()["pending_refund"]
    assert pending["order_id"] == "1001"


# --- AC-16: the queue and its rules ---

def test_staff_see_the_queue_and_customers_dont():
    client, _ = request_refund("Asha", "1001", 59.99)
    assert client.get("/refunds/pending").status_code == 403
    for staff in ("Support", "Admin"):
        rows = signed_in(staff).get("/refunds/pending").json()
        assert len(rows) == 1
        row = rows[0]
        assert row["order_id"] == "1001" and row["amount"] == 59.99 and row["reason"] == "damaged"
        assert row["customer"] == "Asha" and row["item"] == "Wireless Mouse"


def test_support_can_approve_up_to_200():
    _, session = request_refund("Asha", "1001", 59.99)
    support = signed_in("Support")
    assert decide(support, session).json()["status"] == "answered"
    assert status_of("1001") == "refunded"
    assert support.get("/refunds/pending").json() == []


def test_support_cant_approve_over_200_but_an_admin_can():
    _, session = request_refund("Kabir", "1006", 249.0)
    assert decide(signed_in("Support"), session).status_code == 403
    assert status_of("1006") == "delivered"
    assert decide(signed_in("Admin"), session).status_code == 200
    assert status_of("1006") == "refunded"


@pytest.mark.parametrize("role", ["support", "admin"])
def test_nobody_approves_their_own_refund(role):
    store = auth.get_user_store()
    store.set_role(store.get_by_email(demo_email("Asha")).user_id, role)
    client, session = request_refund("Asha", "1001", 59.99)
    assert decide(client, session).status_code == 403
    assert status_of("1001") == "delivered"


def test_a_rejection_leaves_the_order_alone():
    _, session = request_refund("Asha", "1001", 59.99)
    assert decide(signed_in("Support"), session, approved=False, note="used item").status_code == 200
    assert status_of("1001") == "delivered"
    assert "REJECTED" in tool_messages(session)[0] and "used item" in tool_messages(session)[0]


def test_a_refund_can_only_be_decided_once():
    _, session = request_refund("Asha", "1001", 59.99)
    support = signed_in("Support")
    assert decide(support, session).status_code == 200
    assert decide(signed_in("Admin"), session).status_code == 409


def test_two_reviewers_cant_both_claim_a_request():
    _, session = request_refund("Asha", "1001", 59.99)
    store = get_refund_store()
    refund = store.open_for_session(session)
    assert store.claim(refund.id, 8, "") is True
    assert store.claim(refund.id, 9, "") is False


def test_deciding_with_no_refund_pending_is_a_409():
    assert decide(signed_in("Support"), "c-nothing-pending-here").status_code == 409


# --- AC-17: the reviewer is the signed-in user ---

def test_a_reviewer_name_in_the_request_is_ignored():
    _, session = request_refund("Asha", "1001", 59.99)
    support = signed_in("Support")
    decide(support, session, reviewer="mallory")
    message = tool_messages(session)[0]
    assert "by Support" in message and "mallory" not in message
    support_id = auth.get_user_store().get_by_email(demo_email("Support")).user_id
    assert get_refund_store().last_for_session(session).reviewer_id == support_id


def test_an_amount_in_the_request_changes_nothing():
    _, session = request_refund("Kabir", "1006", 249.0)
    assert decide(signed_in("Support"), session, amount=10, needs_supervisor=False).status_code == 403


# --- AC-18, and resuming as the customer ---

def test_the_customer_sees_the_outcome_without_sending_a_message():
    client, session = request_refund("Asha", "1001", 59.99)
    decide(signed_in("Support"), session)
    opened = client.get(f"/conversations/{session}").json()
    assert opened["pending_refund"] is None
    assert opened["messages"][-1] == {"role": "assistant", "text": "Your refund was decided."}


def test_the_agent_resumes_as_the_customer_not_the_reviewer():
    # After the approval the model looks up the customer's order. As Support, that would fail.
    _, session = request_refund(
        "Asha", "1001", 59.99, call("get_order_status", {"order_id": "1001"}, "c2"), say("All done."),
    )
    decide(signed_in("Support"), session)
    assert "Wireless Mouse" in tool_messages(session)[1]


def test_a_second_refund_during_the_resume_reaches_the_queue():
    store = auth.get_user_store()
    asha = store.get_by_email(demo_email("Asha")).user_id
    get_order_repo().create_sample_orders(asha, "Asha")
    second = get_order_repo().list_for_owner(asha)[1]["order_id"]
    _, session = request_refund(
        "Asha", "1001", 59.99,
        call("request_refund", {"order_id": second, "amount": 10, "reason": "also damaged"}, "c2"),
    )
    support = signed_in("Support")
    assert decide(support, session).json()["status"] == "pending_approval"
    assert [row["order_id"] for row in support.get("/refunds/pending").json()] == [second]


def test_streaming_approval_follows_the_same_rules():
    _, session = request_refund("Asha", "1001", 59.99)
    support = signed_in("Support")
    r = support.post("/approve/stream", json={"session_id": session, "approved": True})
    assert r.status_code == 200 and "event: final" in r.text
    assert status_of("1001") == "refunded"
    assert support.get("/refunds/pending").json() == []


# --- AC-23: level rules on /orders and /demo/reset ---

def test_a_customer_sees_only_their_own_orders():
    rows = signed_in("Asha").get("/orders").json()
    assert [o["order_id"] for o in rows] == ["1001"]


@pytest.mark.parametrize("staff", ["Support", "Admin"])
def test_staff_see_all_orders(staff):
    assert len(signed_in(staff).get("/orders").json()) == 7


@pytest.mark.parametrize("name, expected", [("Asha", 403), ("Support", 403), ("Admin", 200)])
def test_only_admins_can_reset(name, expected):
    assert signed_in(name).post("/demo/reset").status_code == expected


def test_reset_restores_orders_and_keeps_their_owners():
    _, session = request_refund("Asha", "1001", 59.99)
    decide(signed_in("Support"), session)
    signed_in("Admin").post("/demo/reset")
    assert status_of("1001") == "delivered"
    assert [o["order_id"] for o in signed_in("Asha").get("/orders").json()] == ["1001"]


def test_reset_cancels_open_requests():
    client, session = request_refund("Asha", "1001", 59.99)
    signed_in("Admin").post("/demo/reset")
    support = signed_in("Support")
    assert support.get("/refunds/pending").json() == []
    assert decide(support, session).status_code == 409
    assert client.get(f"/conversations/{session}").json()["pending_refund"] is None
