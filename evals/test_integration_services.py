"""The MCP server, conversations, the review queue and the real agent."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import jwt
import psycopg
import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient

from integration_support import MOUSE, NOW, demo_user, query
from shophelper.accounts import auth
from shophelper.accounts.conversations import PostgresConversations
from shophelper.agent import memory
from shophelper.agent.service import ShopHelperService
from shophelper.core.config import get_settings
from shophelper.mcp.client import mcp_tools
from shophelper.shop.cart import PostgresCartStore
from shophelper.shop.catalog import InMemoryProductRepo
from shophelper.shop.orders import get_order_repo
from shophelper.shop.refunds import PostgresRefunds, get_refund_store

pytestmark = pytest.mark.skipif(not get_settings().database_url, reason="needs the local stack's Postgres")


# --- AC-13: straight at the running MCP server, with no agent involved ---

async def call_mcp(order_id, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else None
    connection = {"transport": "streamable_http", "url": get_settings().mcp_url, "headers": headers}
    tools = await MultiServerMCPClient({"s": connection}).get_tools()
    tool = next(t for t in tools if t.name == "get_order_status")
    return str(await tool.ainvoke({"order_id": order_id}))





async def test_mcp_returns_no_order_data_without_a_valid_identity():
    asha = demo_user("Asha").user_id
    forged = jwt.encode({"sub": str(asha), "aud": auth.INTERNAL_AUDIENCE}, "wrong-key" * 5, algorithm="HS256")
    expired = auth.issue_internal_token(asha, now=datetime.now(UTC) - timedelta(minutes=5))
    for token in (None, "garbage", forged, expired):
        result = await call_mcp("1001", token)
        assert "Wireless Mouse" not in result and "No order found" in result


async def test_mcp_serves_only_the_signed_users_orders():
    token = auth.issue_internal_token(demo_user("Asha").user_id)
    assert "Wireless Mouse" in await call_mcp("1001", token)
    theirs = await call_mcp("1002", token)
    assert "Mechanical Keyboard" not in theirs and "No order found" in theirs


async def test_mcp_tools_dont_expose_identity_to_the_model():
    client = MultiServerMCPClient({"s": {"transport": "streamable_http", "url": get_settings().mcp_url}})
    tool = next(t for t in await client.get_tools() if t.name == "get_order_status")
    assert set(tool.args) == {"order_id"}


# --- AC-24: conversation titles ---

def test_conversation_titles_come_from_masked_history(fresh_db):
    user = auth.signup(auth.get_user_store(), "a@example.com", "correct-horse", now=NOW)
    conversations = PostgresConversations()
    session = conversations.create(user.user_id)
    history = memory.PostgresHistory()
    history.append(session, "user", "My email is {EMAIL}, where is my order?")
    history.append(session, "assistant", "Here it is.")
    history.append(session, "user", "Thanks")
    listed = conversations.list_for(user.user_id)
    assert [c["title"] for c in listed] == ["My email is {EMAIL}, where is my order?"]
    assert conversations.list_for(user.user_id + 1) == []


# --- AC-16: the review queue on real Postgres ---

REFUND = {"order_id": "1001", "amount": 59.99, "reason": "damaged", "needs_supervisor": False}


def test_a_conversation_can_have_only_one_open_request(fresh_db):
    user = auth.signup(auth.get_user_store(), "a@example.com", "correct-horse", now=NOW)
    store = PostgresRefunds()
    store.open("c-1", user.user_id, REFUND)
    store.open("c-1", user.user_id, REFUND)
    assert len(store.list_open()) == 1
    assert store.list_open()[0].amount == 59.99


def test_eight_reviewers_racing_produce_one_winner(fresh_db):
    auth_store = auth.get_user_store()
    customer = auth.signup(auth_store, "c@example.com", "correct-horse", now=NOW)
    reviewer = auth.signup(auth_store, "r@example.com", "correct-horse", now=NOW)
    store = PostgresRefunds()
    store.open("c-1", customer.user_id, REFUND)
    request_id = store.list_open()[0].id
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda _: store.claim(request_id, reviewer.user_id, ""), range(8)))
    assert results.count(True) == 1


def test_a_finished_request_leaves_the_queue_and_records_who_decided(fresh_db):
    auth_store = auth.get_user_store()
    customer = auth.signup(auth_store, "c@example.com", "correct-horse", now=NOW)
    reviewer = auth.signup(auth_store, "r@example.com", "correct-horse", now=NOW)
    store = PostgresRefunds()
    store.open("c-1", customer.user_id, REFUND)
    request_id = store.list_open()[0].id
    store.claim(request_id, reviewer.user_id, "checked the photo")
    assert store.open_for_session("c-1").status == "claimed"
    store.finish(request_id, approved=True)
    assert store.list_open() == []
    decided = store.last_for_session("c-1")
    assert (decided.status, decided.reviewer_id) == ("approved", reviewer.user_id)
    assert decided.note == "checked the photo"
    assert query("SELECT decided_at FROM refund_requests")[0]["decided_at"] is not None


def test_cancelling_closes_open_requests_only(fresh_db):
    user = auth.signup(auth.get_user_store(), "a@example.com", "correct-horse", now=NOW)
    store = PostgresRefunds()
    store.open("c-1", user.user_id, REFUND)
    store.claim(store.list_open()[0].id, user.user_id, "")
    store.finish(store.last_for_session("c-1").id, approved=False)
    store.open("c-2", user.user_id, REFUND)
    store.cancel_open()
    assert store.last_for_session("c-1").status == "rejected"
    assert store.last_for_session("c-2").status == "cancelled"


# --- Feature 021, AC-22, AC-41: a bought order, all the way through the real agent ---

def remove_order(order_id):
    """This test uses the real database, because the MCP server does. It leaves nothing behind."""
    with psycopg.connect(get_settings().database_url) as conn:
        conn.execute("DELETE FROM refund_requests WHERE order_id = %s", (order_id,))
        conn.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))


async def test_a_bought_order_goes_through_the_real_agent():
    asha, ravi = auth.to_principal(demo_user("Asha")), auth.to_principal(demo_user("Ravi"))
    support = demo_user("Support")
    orders, refunds, carts = get_order_repo(), get_refund_store(), PostgresCartStore()
    carts.set_quantity(asha.user_id, MOUSE, 1)
    order_id = carts.checkout(asha.user_id, asha.display_name)["order_id"]
    run = uuid.uuid4().hex[:6]
    try:
        async with mcp_tools() as tools:
            agent = ShopHelperService(tools=tools)

            lookup = await agent.chat(f"bought-asha-{run}", f"Where is order {order_id}?", asha)
            assert "get_order_status" in lookup.tools_used
            assert "process" in lookup.answer.lower()  # positive control: the owner sees it

            stranger = await agent.chat(f"bought-ravi-{run}", f"Where is order {order_id}?", ravi)
            assert "wireless mouse" not in stranger.answer.lower()
            assert "process" not in stranger.answer.lower()

            early = f"bought-early-{run}"
            too_soon = await agent.chat(early, f"Please refund order {order_id}, I changed my mind.", asha)
            assert too_soon.status != "pending_approval"
            assert orders.get(order_id)["status"] == "processing"

            assert orders.mark_delivered(order_id)["status"] == "delivered"

            session = f"bought-refund-{run}"
            ask = f"I'd like a refund for order {order_id}, the mouse stopped working."
            asked = await agent.chat(session, ask, asha)
            assert asked.status == "pending_approval", asked.answer
            refund = refunds.open_for_session(session)
            assert refund.order_id == order_id and refund.owner_id == asha.user_id

            assert refunds.claim(refund.id, support.user_id, "")
            await agent.approve(session, True, support.display_name, "", asha.user_id)
            refunds.finish(refund.id, True)
            assert orders.get(order_id)["status"] == "refunded"
    finally:
        remove_order(order_id)


async def test_a_lifestyle_order_isnt_treated_as_off_topic():
    """AC-38. All the demo orders are electronics, so this buys something that isn't."""
    asha = auth.to_principal(demo_user("Asha"))
    carts = PostgresCartStore()
    kettlebell = next(p for p in InMemoryProductRepo().page("fitness-and-outdoors", "rating", 0, 12)["items"]
                      if p["slug"] == "cast-iron-kettlebell")
    carts.set_quantity(asha.user_id, kettlebell["id"], 1)
    order_id = carts.checkout(asha.user_id, asha.display_name)["order_id"]
    try:
        async with mcp_tools() as tools:
            agent = ShopHelperService(tools=tools)
            reply = await agent.chat(
                f"lifestyle-{uuid.uuid4().hex[:6]}",
                f"Has my kettlebell from order {order_id} shipped yet?",
                asha,
            )
        assert "get_order_status" in reply.tools_used
        assert "process" in reply.answer.lower()  # "processing" or "being processed"
    finally:
        remove_order(order_id)
