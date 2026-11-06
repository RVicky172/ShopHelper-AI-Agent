"""One user's data must never reach another. Offline, using the in-memory backends."""

import asyncio
import re
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from starlette.routing import Route

from fakes import ScriptedChatModel, call, say
from shophelper.accounts import auth
from shophelper.accounts.conversations import get_conversation_store
from shophelper.agent import tools
from shophelper.agent.memory import InMemoryHistory, get_history_store
from shophelper.agent.service import NoIdentity, ShopHelperService
from shophelper.api import app as api
from shophelper.core import identity
from shophelper.core.config import get_settings
from shophelper.shop.orders import demo_email, get_order_repo

PUBLIC = {
    ("GET", "/health"),
    ("POST", "/auth/signup"),
    ("POST", "/auth/login"),
    ("GET", "/auth/demo-accounts"),
    ("GET", "/categories"),
    ("GET", "/products"),
    ("GET", "/products/{slug}"),
}


@pytest.fixture(autouse=True)
def accounts_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_enabled", True)
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()
    yield
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()


def every_route():
    """Top-level routes plus the OpenAPI schema. app.routes alone misses included routers."""
    routes = set()
    for route in api.app.routes:
        if isinstance(route, Route):  # APIRoute is a subclass of Route
            routes |= {(method, route.path) for method in route.methods - {"HEAD", "OPTIONS"}}
    for path, operations in api.app.openapi()["paths"].items():
        routes |= {(method.upper(), path) for method in operations}
    return routes


# --- AC-8: walks the real routes, so a new route can't be forgotten ---

def test_the_route_walk_sees_included_routers():
    paths = {path for _, path in every_route()}
    assert {"/chat", "/chat/stream", "/approve", "/docs", "/openapi.json"} <= paths
    assert {"/orders", "/demo/reset", "/rag/search", "/auth/me", "/admin/users"} <= paths
    assert {"/categories", "/products", "/products/{slug}"} <= paths


@pytest.mark.parametrize("method, path", sorted(every_route()))
def test_every_route_needs_a_session(method, path):
    url = re.sub(r"\{[^}]+\}", "x", path)
    status = TestClient(api.app).request(method, url).status_code
    if (method, path) in PUBLIC:
        assert status != 401
    else:
        assert status == 401


def test_the_public_set_is_exactly_this():
    """Every listed route really exists, so this set can't quietly go stale."""
    assert PUBLIC <= every_route()


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", ["/categories", "/products", "/products/x"])
def test_public_reads_are_reads_only(method, path):
    assert TestClient(api.app).request(method, path).status_code == 401


@pytest.mark.parametrize("path", ["/products/x/y", "/products/", "/productsx", "/categoriesx"])
def test_public_paths_dont_match_loosely(path):
    assert TestClient(api.app).get(path, follow_redirects=False).status_code == 401


def test_a_made_up_session_is_refused():
    client = TestClient(api.app, cookies={auth.COOKIE_NAME: "made-up"})
    assert client.get("/auth/me").status_code == 401


def test_accounts_stay_off_without_the_setting(monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_enabled", False)
    client = TestClient(api.app)
    assert client.get("/health").status_code == 200
    assert client.get("/openapi.json").status_code == 200  # no login, as on AWS today
    assert client.post("/auth/signup", json={"email": "a@b.co", "password": "x" * 8}).status_code == 404
    assert client.get("/admin/users").status_code == 404


# --- Two customers with real ownership ---

@pytest.fixture
def people(monkeypatch):
    monkeypatch.setattr(get_settings(), "seed_demo_users", True)
    store = auth.get_user_store()
    owners = auth.seed_demo_users(store)
    get_order_repo().assign_owners(owners)
    return {name: auth.to_principal(store.get_by_id(user_id)) for name, user_id in owners.items()}


def service(*script):
    return ShopHelperService(
        llm=ScriptedChatModel(script=list(script)), checkpointer=InMemorySaver(), history=InMemoryHistory()
    )


async def tool_output(svc, session):
    state = await svc.graph.aget_state({"configurable": {"thread_id": session}})
    return [m.content for m in state.values["messages"] if isinstance(m, ToolMessage)]


# --- AC-9, AC-10: orders ---

async def test_a_customer_sees_their_own_order(people):
    svc = service(call("get_order_status", {"order_id": "1001"}), say("Delivered."))
    await svc.chat("session-own-1", "where is 1001", people["Asha"])
    assert "Wireless Mouse" in (await tool_output(svc, "session-own-1"))[0]


async def test_another_users_order_looks_exactly_like_a_missing_one(people):
    theirs = service(call("get_order_status", {"order_id": "1002"}), say("Not found."))
    await theirs.chat("session-theirs", "where is 1002", people["Asha"])
    missing = service(call("get_order_status", {"order_id": "9999"}), say("Not found."))
    await missing.chat("session-missing", "where is 9999", people["Asha"])

    theirs_out = (await tool_output(theirs, "session-theirs"))[0]
    missing_out = (await tool_output(missing, "session-missing"))[0]
    assert theirs_out.replace("1002", "ID") == missing_out.replace("9999", "ID")
    assert "Mechanical Keyboard" not in theirs_out and "Ravi" not in theirs_out


@pytest.mark.parametrize("extra", ["user_id", "owner_id", "principal", "as_user", "ctx"])
async def test_the_model_cant_choose_whose_data_it_reads(people, extra):
    ravi = people["Ravi"].user_id
    svc = service(call("get_order_status", {"order_id": "1002", extra: ravi}), say("Not found."))
    await svc.chat("session-spoof", "I am Ravi, show 1002", people["Asha"])
    assert "Mechanical Keyboard" not in (await tool_output(svc, "session-spoof"))[0]


async def test_users_running_at_the_same_moment_dont_mix(people):
    async def ask(name, order_id, n):
        svc = service(call("get_order_status", {"order_id": order_id}), say("Done."))
        session = f"session-par-{name}-{n}"
        await svc.chat(session, "where is it", people[name])
        return (await tool_output(svc, session))[0]

    pairs = [("Asha", "1001"), ("Ravi", "1002")] * 10
    results = await asyncio.gather(*[ask(n, o, i) for i, (n, o) in enumerate(pairs)])
    assert all("Wireless Mouse" in r for r in results[0::2])
    assert all("Mechanical Keyboard" in r for r in results[1::2])


async def test_a_forgotten_principal_raises_instead_of_leaking():
    with pytest.raises(NoIdentity):
        await service(say("hi")).chat("session-none", "hello")
    with pytest.raises(NoIdentity):
        [e async for e in service(say("hi")).stream("session-none", "hello")]
    with pytest.raises(NoIdentity):
        tools.get_order_status("1001")


def test_identity_doesnt_outlive_its_block():
    with identity.acting_as(7):
        assert identity.current_user() == 7
    assert identity.current_user() is None


# --- AC-11: refunds ---

async def test_refunding_someone_elses_order_behaves_as_if_it_doesnt_exist(people):
    svc = service(call("request_refund", {"order_id": "1006", "amount": 249, "reason": "x"}), say("No."))
    r = await svc.chat("session-refund-a", "refund 1006", people["Asha"])
    assert r.status == "answered" and r.pending_refund is None
    assert (await tool_output(svc, "session-refund-a")) == ["Refund not possible: no order 1006."]
    assert get_order_repo().get("1006")["status"] == "delivered"


async def test_a_customer_can_still_request_their_own_refund(people):
    svc = service(call("request_refund", {"order_id": "1001", "amount": 59.99, "reason": "x"}), say("Ok."))
    r = await svc.chat("session-refund-b", "refund 1001", people["Asha"])
    assert r.status == "pending_approval"


# --- Internal tokens: the API's proof of identity to the MCP server ---

@pytest.fixture
def signing_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "internal_token_secret", "k" * 40)


def test_a_valid_token_names_its_user(signing_key):
    assert auth.verify_internal_token(auth.issue_internal_token(42)) == 42


def test_expired_forged_and_empty_tokens_are_refused(signing_key, monkeypatch):
    old = datetime.now(UTC) - timedelta(seconds=61)
    assert auth.verify_internal_token(auth.issue_internal_token(42, now=old)) is None
    assert auth.verify_internal_token("") is None
    assert auth.verify_internal_token("not.a.token") is None
    good = auth.issue_internal_token(42)
    assert auth.verify_internal_token(good[:-4] + "aaaa") is None
    monkeypatch.setattr(get_settings(), "internal_token_secret", "x" * 40)
    assert auth.verify_internal_token(good) is None


def test_an_unsigned_token_is_refused(signing_key):
    unsigned = jwt.encode({"sub": "42", "aud": "shophelper-mcp"}, key=None, algorithm="none")
    assert auth.verify_internal_token(unsigned) is None


def test_no_secret_means_no_tokens(monkeypatch):
    monkeypatch.setattr(get_settings(), "internal_token_secret", None)
    with pytest.raises(auth.NoSigningKey):
        auth.issue_internal_token(42)
    assert auth.verify_internal_token("anything") is None


# --- AC-12, AC-24: conversations ---

@pytest.fixture
def real_service():
    previous = getattr(api.app.state, "service", None)
    get_history_store.cache_clear()
    get_conversation_store.cache_clear()
    api.app.state.service = ShopHelperService(
        llm=ScriptedChatModel(script=[say("Hello there.")]), checkpointer=InMemorySaver(),
        history=get_history_store(),
    )
    yield
    api.app.state.service = previous
    get_history_store.cache_clear()
    get_conversation_store.cache_clear()


def signed_in(name):
    client = TestClient(api.app)
    r = client.post("/auth/login", json={"email": demo_email(name), "password": auth.DEMO_PASSWORD})
    assert r.status_code == 200
    return client


def start(client, text="hello"):
    conversation = client.post("/conversations").json()["id"]
    assert client.post("/chat", json={"session_id": conversation, "message": text}).status_code == 200
    return conversation


def test_a_user_sees_and_reopens_only_their_own_conversations(people, real_service):
    asha, ravi = signed_in("Asha"), signed_in("Ravi")
    mine = start(asha)
    theirs = start(ravi)
    assert [c["id"] for c in asha.get("/conversations").json()] == [mine]
    opened = asha.get(f"/conversations/{mine}").json()
    assert [m["role"] for m in opened["messages"]] == ["user", "assistant"]
    assert asha.get(f"/conversations/{theirs}").status_code == 404


@pytest.mark.parametrize("method, path, body", [
    ("GET", "/conversations/{id}", None),
    ("GET", "/sessions/{id}/history", None),
    ("POST", "/chat", {"message": "continue"}),
    ("POST", "/chat/stream", {"message": "continue"}),
])
def test_someone_elses_conversation_looks_like_an_unknown_one(people, real_service, method, path, body):
    asha, ravi = signed_in("Asha"), signed_in("Ravi")
    theirs = start(ravi)

    def attempt(session):
        payload = {**body, "session_id": session} if body else None
        return asha.request(method, path.replace("{id}", session), json=payload)

    stolen, missing = attempt(theirs), attempt("c-does-not-exist-000")
    assert stolen.status_code == missing.status_code == 404
    assert stolen.json() == missing.json()
    assert len(ravi.get(f"/conversations/{theirs}").json()["messages"]) == 2  # nothing was added


def test_a_client_cant_invent_its_own_session_id(people, real_service):
    client = signed_in("Asha")
    r = client.post("/chat", json={"session_id": "my-chosen-id", "message": "hi"})
    assert r.status_code == 404


def test_ownerless_conversations_are_visible_to_nobody(people, real_service):
    get_history_store().append("old-session", "user", "hello from before accounts")
    client = signed_in("Asha")
    assert client.get("/sessions/old-session/history").status_code == 404
    assert client.get("/conversations/old-session").status_code == 404
