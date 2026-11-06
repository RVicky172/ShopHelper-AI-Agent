"""Real Postgres, in a throwaway database, so the demo data is never touched.

    scripts/evals_local.sh -k integration
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import jwt
import psycopg
import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from shophelper import auth, db, memory
from shophelper.cart import PostgresCartStore
from shophelper.catalog import SQL_ORDER, InMemoryProductRepo, PostgresProductRepo
from shophelper.config import get_settings
from shophelper.conversations import PostgresConversations
from shophelper.mcp_client import mcp_tools
from shophelper.orders import PostgresOrderRepo, demo_email, get_order_repo, refund_eligibility
from shophelper.refunds import PostgresRefunds, get_refund_store
from shophelper.service import ShopHelperService

pytestmark = pytest.mark.skipif(not get_settings().database_url, reason="needs the local stack's Postgres")

SCRATCH = "shophelper_integration_test"
NOW = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)

# The schema as it was before feature 020, with rows, to prove an in-place upgrade.
OLD_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE orders (order_id TEXT PRIMARY KEY, data JSONB NOT NULL);
CREATE TABLE chat_history (
    id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO orders VALUES ('1001', '{"order_id": "1001", "customer": "Asha", "status": "delivered"}');
INSERT INTO chat_history (session_id, role, text) VALUES ('old-session', 'user', 'hello');
"""


def scratch_url(url: str) -> str:
    return url.rsplit("/", 1)[0] + f"/{SCRATCH}"


@pytest.fixture
def empty_db(monkeypatch):
    settings = get_settings()
    with psycopg.connect(settings.database_url, autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {SCRATCH} WITH (FORCE)")
        admin.execute(f"CREATE DATABASE {SCRATCH}")
    original = settings.database_url
    monkeypatch.setattr(settings, "database_url", scratch_url(original))
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()
    yield
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()
    monkeypatch.undo()
    with psycopg.connect(original, autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {SCRATCH} WITH (FORCE)")


@pytest.fixture
def fresh_db(empty_db):
    db.apply_schema()


def query(sql, *args):
    with psycopg.connect(get_settings().database_url, row_factory=dict_row) as conn:
        return conn.execute(sql, args).fetchall()


def seed(monkeypatch):
    monkeypatch.setattr(get_settings(), "seed_demo_users", True)
    return auth.seed_demo_users(auth.get_user_store())


# --- AC-20: upgrade in place ---

def test_an_old_database_upgrades_and_keeps_its_rows(empty_db, monkeypatch):
    with psycopg.connect(get_settings().database_url) as conn:
        conn.execute(OLD_SCHEMA)

    db.apply_schema()
    db.apply_schema()  # safe to run on every start

    assert query("SELECT owner_id FROM orders") == [{"owner_id": None}]
    assert len(query("SELECT * FROM chat_history")) == 1

    get_order_repo().assign_owners(seed(monkeypatch))
    assert query("SELECT owner_id FROM orders")[0]["owner_id"] is not None


def test_old_conversations_get_no_owner(empty_db):
    with psycopg.connect(get_settings().database_url) as conn:
        conn.execute(OLD_SCHEMA)
    db.apply_schema()
    assert query("SELECT * FROM conversations WHERE session_id = 'old-session'") == []


# --- AC-19: tables and seeded accounts ---

def test_all_tables_exist(fresh_db):
    tables = {r["tablename"] for r in query("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")}
    expected = {"users", "auth_sessions", "login_attempts", "conversations", "refund_requests", "products",
                "cart_items"}
    assert expected <= tables


def test_seeding_creates_every_level_and_owns_the_demo_orders(fresh_db, monkeypatch):
    owners = seed(monkeypatch)
    repo = get_order_repo()
    repo.reset()
    repo.assign_owners(owners)
    roles = [r["role"] for r in query("SELECT role FROM users")]
    assert roles.count("customer") == 7 and roles.count("support") == 1 and roles.count("admin") == 1
    assert query("SELECT count(*) AS n FROM orders WHERE owner_id IS NULL") == [{"n": 0}]
    assert len({r["owner_id"] for r in query("SELECT owner_id FROM orders")}) == 7


def test_seeding_twice_changes_nothing(fresh_db, monkeypatch):
    first = seed(monkeypatch)
    store = auth.get_user_store()
    asha = store.get_by_id(first["Asha"])
    store.set_role(asha.user_id, "support")
    assert seed(monkeypatch) == first
    assert store.get_by_id(asha.user_id).role == "support"


def test_seeding_is_refused_without_the_setting(fresh_db):
    with pytest.raises(auth.SeedingRefused):
        auth.seed_demo_users(auth.get_user_store())
    assert query("SELECT * FROM users") == []


def test_reset_keeps_owners_and_sample_orders(fresh_db, monkeypatch):
    owners = seed(monkeypatch)
    repo = get_order_repo()
    repo.reset()
    repo.assign_owners(owners)
    user = auth.signup(auth.get_user_store(), "new@example.com", "correct-horse", now=NOW)
    repo.mark_refunded("1001", 59.99, "test")

    repo.reset()

    assert repo.get("1001")["status"] == "delivered"
    assert query("SELECT owner_id FROM orders WHERE order_id = '1001'") == [{"owner_id": owners["Asha"]}]
    assert len(repo.list_for_owner(user.user_id)) == 2


# --- The Postgres backend honours the same contract as the in-memory one ---

def test_signup_login_and_session_on_postgres(fresh_db):
    store = auth.get_user_store()
    user = auth.signup(store, "Asha@Example.com", "correct-horse", now=NOW)
    assert user.role == "customer"
    with pytest.raises(auth.EmailTaken):
        auth.signup(store, "asha@example.com", "correct-horse", now=NOW)

    principal, token = auth.login(store, "asha@example.com", "correct-horse", now=NOW)
    assert principal == user
    assert auth.resolve_session(store, token, now=NOW) == user
    assert auth.resolve_session(store, token, now=NOW + timedelta(hours=24)) is None
    assert query("SELECT * FROM auth_sessions") == []  # expired rows are removed


def test_new_users_get_numbered_sample_orders(fresh_db):
    user = auth.signup(auth.get_user_store(), "a@example.com", "correct-horse", now=NOW)
    orders = get_order_repo().list_for_owner(user.user_id)
    assert sorted(o["order_id"] for o in orders) == ["2001", "2002"]
    assert sorted(o["status"] for o in orders) == ["delivered", "shipped"]


def test_logout_removes_the_row(fresh_db):
    store = auth.get_user_store()
    auth.signup(store, "a@example.com", "correct-horse", now=NOW)
    _, token = auth.login(store, "a@example.com", "correct-horse", now=NOW)
    auth.logout(store, token)
    assert auth.resolve_session(store, token, now=NOW) is None


def test_lockout_on_postgres(fresh_db):
    store = auth.get_user_store()
    auth.signup(store, "a@example.com", "correct-horse", now=NOW)
    for _ in range(5):
        with pytest.raises(auth.InvalidCredentials):
            auth.login(store, "a@example.com", "wrong-password", now=NOW)
    with pytest.raises(auth.LockedOut):
        auth.login(store, "a@example.com", "correct-horse", now=NOW + timedelta(minutes=14))
    assert auth.login(store, "a@example.com", "correct-horse", now=NOW + timedelta(minutes=15))
    assert query("SELECT * FROM login_attempts") == []  # success clears the count


def test_the_last_admin_is_protected_on_postgres(fresh_db):
    store = auth.get_user_store()
    first = auth.signup(store, "a@example.com", "correct-horse", now=NOW)
    second = auth.signup(store, "b@example.com", "correct-horse", now=NOW)
    store.set_role(first.user_id, "admin")
    with pytest.raises(auth.LastAdmin):
        store.set_role(first.user_id, "customer")
    store.set_role(second.user_id, "admin")
    assert store.set_role(first.user_id, "customer").role == "customer"


def test_only_argon2_hashes_and_token_hashes_are_stored(fresh_db):
    store = auth.get_user_store()
    auth.signup(store, "a@example.com", "correct-horse", now=NOW)
    _, token = auth.login(store, "a@example.com", "correct-horse", now=NOW)
    row = query("SELECT password_hash FROM users")[0]
    assert row["password_hash"].startswith("$argon2id$") and "correct-horse" not in row["password_hash"]
    assert query("SELECT token_hash FROM auth_sessions") == [{"token_hash": auth.hash_token(token)}]


# --- AC-13: straight at the running MCP server, with no agent involved ---

async def call_mcp(order_id, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else None
    connection = {"transport": "streamable_http", "url": get_settings().mcp_url, "headers": headers}
    tools = await MultiServerMCPClient({"s": connection}).get_tools()
    tool = next(t for t in tools if t.name == "get_order_status")
    return str(await tool.ainvoke({"order_id": order_id}))


def demo_user(name):
    return auth.PostgresUserStore().get_by_email(demo_email(name))


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


# --- Feature 021, AC-6: the catalogue on Postgres ---

def test_seeding_the_catalogue_twice_changes_nothing(fresh_db):
    repo = PostgresProductRepo()
    assert repo.seed() == 42
    first = query("SELECT * FROM products ORDER BY id")
    assert repo.seed() == 42
    assert query("SELECT * FROM products ORDER BY id") == first


def test_the_catalogue_file_wins_over_an_edited_row(fresh_db):
    repo = PostgresProductRepo()
    repo.seed()
    with psycopg.connect(get_settings().database_url) as conn:
        conn.execute("UPDATE products SET price = 1 WHERE slug = 'phone-case'")
    repo.seed()
    assert query("SELECT price FROM products WHERE slug = 'phone-case'")[0]["price"] == Decimal("19.99")


def test_a_database_from_before_the_shop_gains_the_catalogue(empty_db):
    with psycopg.connect(get_settings().database_url) as conn:
        conn.execute(OLD_SCHEMA)
    db.apply_schema()
    assert PostgresProductRepo().seed() == 42
    assert len(query("SELECT * FROM orders")) == 1


def test_every_demo_order_item_is_a_product_on_postgres(fresh_db):
    PostgresProductRepo().seed()
    get_order_repo().reset()
    missing = query("""
        SELECT data->>'item' AS item FROM orders
        WHERE NOT EXISTS (SELECT 1 FROM products p WHERE p.name = orders.data->>'item')
    """)
    assert missing == []
    assert len(query("SELECT * FROM orders")) == 7


@pytest.mark.parametrize("sort", sorted(SQL_ORDER))
@pytest.mark.parametrize("category", [None, "audio", "bags-and-travel"])
def test_postgres_returns_exactly_what_the_offline_tests_prove(fresh_db, sort, category):
    postgres, memory_repo = PostgresProductRepo(), InMemoryProductRepo()
    postgres.seed()
    for offset in (0, 12, 24, 36, 48):
        assert postgres.page(category, sort, offset, 12) == memory_repo.page(category, sort, offset, 12)


def test_postgres_categories_products_and_related_match_too(fresh_db):
    postgres, memory_repo = PostgresProductRepo(), InMemoryProductRepo()
    postgres.seed()
    assert postgres.categories() == memory_repo.categories()
    for offset in (0, 12, 24, 36):
        for product in memory_repo.page(None, "newest", offset, 12)["items"]:
            assert postgres.get(product["slug"]) == product
            assert postgres.related(product) == memory_repo.related(product)
    assert postgres.get("nope") is None


# --- Feature 021, AC-16 to AC-18: carts on Postgres ---

MOUSE, CASE = 8, 18
NAMES = {MOUSE: "Wireless Mouse", CASE: "Phone Case"}


@pytest.fixture
def shoppers(fresh_db, monkeypatch):
    PostgresProductRepo().seed()
    return seed(monkeypatch)


def test_a_cart_is_stored_so_any_browser_sees_it(shoppers):
    PostgresCartStore().set_quantity(shoppers["Asha"], MOUSE, 2)
    assert PostgresCartStore().quantities(shoppers["Asha"]) == {MOUSE: 2}  # a new store, so nothing cached


def test_changing_and_removing_on_postgres(shoppers):
    store, asha = PostgresCartStore(), shoppers["Asha"]
    store.set_quantity(asha, MOUSE, 2)
    store.set_quantity(asha, MOUSE, 5)
    store.set_quantity(asha, CASE, 1)
    store.set_quantity(asha, CASE, 0)
    assert store.quantities(asha) == {MOUSE: 5}


def test_one_users_writes_never_reach_another_on_postgres(shoppers):
    store, asha, ravi = PostgresCartStore(), shoppers["Asha"], shoppers["Ravi"]
    store.set_quantity(asha, MOUSE, 2)
    assert store.quantities(ravi) == {}
    store.set_quantity(ravi, MOUSE, 7)
    store.set_quantity(ravi, MOUSE, 0)
    store.merge(ravi, [(CASE, 1)], NAMES)
    assert store.quantities(asha) == {MOUSE: 2}  # positive control, and untouched
    assert store.quantities(ravi) == {CASE: 1}


def test_merging_on_postgres_follows_the_same_rules(shoppers):
    store, asha = PostgresCartStore(), shoppers["Asha"]
    store.set_quantity(asha, MOUSE, 8)
    changes = store.merge(asha, [(MOUSE, 5), (CASE, 1), (10**30, 1)], NAMES)
    assert store.quantities(asha) == {MOUSE: 10, CASE: 1}
    assert [(c["kind"], c["product_id"]) for c in changes] == [("unavailable", 10**30), ("capped", MOUSE)]


def test_a_huge_product_id_is_just_an_unknown_product(shoppers):
    assert PostgresProductRepo().by_ids([10**30, MOUSE]).keys() == {MOUSE}


def test_merges_racing_each_other_lose_nothing(shoppers):
    store, asha = PostgresCartStore(), shoppers["Asha"]
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda _: store.merge(asha, [(MOUSE, 1)], NAMES), range(8)))
    assert store.quantities(asha) == {MOUSE: 8}


def test_the_database_itself_refuses_a_quantity_over_ten(shoppers):
    with pytest.raises(psycopg.errors.CheckViolation):
        PostgresCartStore().set_quantity(shoppers["Asha"], MOUSE, 11)


# --- Feature 021, AC-19 to AC-21, AC-41: checkout and delivery on Postgres ---

def fill(shoppers, name="Asha"):
    store = PostgresCartStore()
    store.set_quantity(shoppers[name], MOUSE, 2)
    store.set_quantity(shoppers[name], CASE, 1)
    return store


def test_checkout_on_postgres_prices_from_the_table_and_owns_the_order(shoppers):
    order = fill(shoppers).checkout(shoppers["Asha"], "Asha")
    assert order["total"] == 139.97 and order["item"] == "Wireless Mouse + 1 more"
    assert query("SELECT * FROM cart_items") == []
    repo = get_order_repo()
    assert repo.get_for_owner(order["order_id"], shoppers["Asha"]) == order
    assert repo.get_for_owner(order["order_id"], shoppers["Ravi"]) is None


def test_a_price_changed_in_the_table_is_the_price_paid(shoppers):
    store = fill(shoppers)
    with psycopg.connect(get_settings().database_url) as conn:
        conn.execute("UPDATE products SET price = 1.50 WHERE id = %s", (MOUSE,))
    assert store.checkout(shoppers["Asha"], "Asha")["total"] == 22.99


def test_a_failed_order_keeps_the_cart(shoppers, monkeypatch):
    """One transaction: if the order can't be written, nothing is lost."""
    store = fill(shoppers)

    def broken(*args):
        raise RuntimeError("database write failed")

    monkeypatch.setattr(PostgresOrderRepo, "add_order", broken)
    with pytest.raises(RuntimeError):
        store.checkout(shoppers["Asha"], "Asha")
    assert store.quantities(shoppers["Asha"]) == {MOUSE: 2, CASE: 1}
    assert query("SELECT * FROM orders") == []


def test_eight_checkouts_racing_place_one_order(shoppers):
    store = fill(shoppers)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda _: store.checkout(shoppers["Asha"], "Asha"), range(8)))
    assert len([r for r in results if r]) == 1
    assert len(query("SELECT * FROM orders")) == 1


def test_checkout_on_postgres_leaves_other_carts_alone(shoppers):
    store = fill(shoppers)
    store.set_quantity(shoppers["Ravi"], CASE, 3)
    store.checkout(shoppers["Asha"], "Asha")
    assert store.quantities(shoppers["Ravi"]) == {CASE: 3}


def test_delivering_a_bought_order_on_postgres_makes_it_refundable(shoppers):
    order = fill(shoppers).checkout(shoppers["Asha"], "Asha")
    delivered = get_order_repo().mark_delivered(order["order_id"])
    assert delivered["status"] == "delivered" and "estimated_delivery" not in delivered
    assert refund_eligibility(get_order_repo().get(order["order_id"]), 139.97)[0] is True


@pytest.mark.parametrize("status", ["delivered", "cancelled", "refunded"])
def test_postgres_refuses_to_deliver_a_finished_order(shoppers, status):
    order = fill(shoppers).checkout(shoppers["Asha"], "Asha")
    with psycopg.connect(get_settings().database_url) as conn:
        conn.execute("UPDATE orders SET data = data || %s", (Jsonb({"status": status}),))
    assert get_order_repo().mark_delivered(order["order_id"]) is None
    assert get_order_repo().get(order["order_id"])["status"] == status


def test_a_demo_reset_keeps_bought_orders_on_postgres(shoppers):
    order = fill(shoppers).checkout(shoppers["Asha"], "Asha")
    get_order_repo().reset()
    assert get_order_repo().get_for_owner(order["order_id"], shoppers["Asha"]) == order


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
