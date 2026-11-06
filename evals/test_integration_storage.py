"""Upgrades, tables and the Postgres backends."""

from datetime import timedelta

import psycopg
import pytest

from integration_support import NOW, OLD_SCHEMA, query, seed
from shophelper.accounts import auth
from shophelper.core import db
from shophelper.core.config import get_settings
from shophelper.shop.orders import get_order_repo

pytestmark = pytest.mark.skipif(not get_settings().database_url, reason="needs the local stack's Postgres")


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
