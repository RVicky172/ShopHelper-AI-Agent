"""Accounts: sign-up, login, sessions and access levels. Offline, using the in-memory backends."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from shophelper import api, auth
from shophelper.config import get_settings
from shophelper.orders import get_order_repo

NOW = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
GOOD = {"email": "asha@example.com", "password": "correct-horse"}


@pytest.fixture(autouse=True)
def accounts_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_enabled", True)
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()
    yield
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()


@pytest.fixture
def client():
    return TestClient(api.app)


@pytest.fixture
def store():
    return auth.get_user_store()


def signup(client, **over):
    return client.post("/auth/signup", json={**GOOD, **over})


# --- AC-1: sign-up ---

def test_signup_creates_a_signed_in_customer(client):
    r = signup(client)
    assert r.status_code == 201
    assert r.json()["email"] == "asha@example.com" and r.json()["role"] == "customer"
    assert client.get("/auth/me").json()["email"] == "asha@example.com"


def test_new_customers_get_two_sample_orders(client):
    user_id = signup(client).json()["id"]
    orders = get_order_repo().list_for_owner(user_id)
    assert sorted(o["status"] for o in orders) == ["delivered", "shipped"]


@pytest.mark.parametrize("over", [{"password": "short12"}, {"email": "not-an-email"}, {"email": "a@b"}])
def test_signup_refuses_bad_input_with_a_message(client, over):
    r = signup(client, **over)
    assert r.status_code == 400 and r.json()["detail"]
    assert client.get("/auth/me").status_code == 401


def test_signup_refuses_a_duplicate_email_in_any_case(client):
    signup(client)
    fresh = TestClient(api.app)
    r = signup(fresh, email="ASHA@Example.com")
    assert r.status_code == 409 and r.json()["detail"]


# --- AC-7: a request can't choose its own level ---

def test_signup_ignores_a_requested_role(client):
    assert signup(client, role="admin").json()["role"] == "customer"


# --- AC-2: login ---

def test_login_works_and_is_case_insensitive(client):
    signup(client)
    fresh = TestClient(api.app)
    assert fresh.post("/auth/login", json={**GOOD, "email": "Asha@Example.com"}).status_code == 200
    assert fresh.get("/auth/me").status_code == 200


def test_wrong_password_and_unknown_email_look_identical(client):
    signup(client)
    fresh = TestClient(api.app)
    wrong = fresh.post("/auth/login", json={**GOOD, "password": "wrong-password"})
    unknown = fresh.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_the_session_cookie_cant_be_read_by_page_scripts(client):
    cookie = signup(client).headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie


# --- AC-3: logout ---

def test_logout_ends_the_session_even_for_a_saved_copy(client):
    signup(client)
    saved = client.cookies.get(auth.COOKIE_NAME)
    assert client.post("/auth/logout").status_code == 204
    copy = TestClient(api.app, cookies={auth.COOKIE_NAME: saved})
    assert copy.get("/auth/me").status_code == 401


# --- AC-4: expiry ---

def test_session_works_until_24_hours_then_stops(store):
    auth.signup(store, GOOD["email"], GOOD["password"], now=NOW)
    _, token = auth.login(store, GOOD["email"], GOOD["password"], now=NOW)
    almost = NOW + timedelta(hours=24) - timedelta(seconds=1)
    assert auth.resolve_session(store, token, now=almost) is not None
    assert auth.resolve_session(store, token, now=NOW + timedelta(hours=24)) is None


# --- AC-5: lockout ---

def fail_login(store, now, email=GOOD["email"]):
    with pytest.raises(auth.InvalidCredentials):
        auth.login(store, email, "wrong-password", now=now)


def test_five_failures_lock_even_the_right_password(store):
    auth.signup(store, GOOD["email"], GOOD["password"], now=NOW)
    for _ in range(5):
        fail_login(store, NOW)
    with pytest.raises(auth.LockedOut):
        auth.login(store, GOOD["email"], GOOD["password"], now=NOW + timedelta(minutes=14))


def test_the_lock_ends_after_15_minutes(store):
    auth.signup(store, GOOD["email"], GOOD["password"], now=NOW)
    for _ in range(5):
        fail_login(store, NOW)
    principal, _ = auth.login(store, GOOD["email"], GOOD["password"], now=NOW + timedelta(minutes=15))
    assert principal.email == GOOD["email"]


def test_old_failures_dont_count(store):
    auth.signup(store, GOOD["email"], GOOD["password"], now=NOW)
    for i in range(4):
        fail_login(store, NOW + timedelta(minutes=i))
    fail_login(store, NOW + timedelta(minutes=20))
    assert auth.login(store, GOOD["email"], GOOD["password"], now=NOW + timedelta(minutes=21))


def test_unknown_emails_lock_too_so_lockout_reveals_nothing(store):
    for _ in range(5):
        fail_login(store, NOW, email="nobody@example.com")
    with pytest.raises(auth.LockedOut):
        auth.login(store, "nobody@example.com", "wrong-password", now=NOW)


def test_lockout_is_a_429_over_http(client):
    signup(client)
    fresh = TestClient(api.app)
    for _ in range(5):
        fresh.post("/auth/login", json={**GOOD, "password": "wrong-password"})
    assert fresh.post("/auth/login", json=GOOD).status_code == 429


# --- AC-6: only hashes are stored ---

def test_only_a_salted_slow_hash_is_stored(store):
    auth.signup(store, GOOD["email"], GOOD["password"], now=NOW)
    auth.signup(store, "ravi@example.com", GOOD["password"], now=NOW)
    first = store.get_by_email(GOOD["email"]).password_hash
    second = store.get_by_email("ravi@example.com").password_hash
    assert first.startswith("$argon2id$") and GOOD["password"] not in first
    assert first != second  # same password, different salt


def test_session_tokens_are_stored_only_as_hashes(store):
    auth.signup(store, GOOD["email"], GOOD["password"], now=NOW)
    _, token = auth.login(store, GOOD["email"], GOOD["password"], now=NOW)
    assert store.get_session(token) is None
    assert store.get_session(auth.hash_token(token)) is not None


def test_a_rejected_password_isnt_echoed_back(client):
    r = client.post("/auth/login", json={"email": 5, "password": "secret-value-123"})
    assert "secret-value-123" not in r.text


# --- Cross-site requests (non-functional requirement) ---

def test_state_changing_requests_from_other_sites_are_refused(client):
    r = client.post("/auth/login", json=GOOD, headers={"origin": "https://evil.example"})
    assert r.status_code == 403


def test_requests_from_our_own_site_are_allowed(client):
    signup(client)
    r = client.post("/auth/logout", headers={"origin": get_settings().web_origin})
    assert r.status_code == 204


# --- AC-21: access levels ---

def make_user(store, email, role):
    user = auth.signup(store, email, GOOD["password"], now=NOW)
    return store.set_role(user.user_id, role) if role != "customer" else user


def as_user(email):
    c = TestClient(api.app)
    c.post("/auth/login", json={"email": email, "password": GOOD["password"]})
    return c


def test_only_admins_can_list_users(store):
    make_user(store, "admin@example.com", "admin")
    make_user(store, "support@example.com", "support")
    make_user(store, "cust@example.com", "customer")
    assert as_user("cust@example.com").get("/admin/users").status_code == 403
    assert as_user("support@example.com").get("/admin/users").status_code == 403
    users = as_user("admin@example.com").get("/admin/users")
    assert users.status_code == 200 and len(users.json()) == 3
    assert all("password" not in key for row in users.json() for key in row)


def test_a_level_change_applies_on_the_next_request(store):
    make_user(store, "admin@example.com", "admin")
    target = make_user(store, "cust@example.com", "customer")
    customer = as_user("cust@example.com")
    assert customer.get("/auth/me").json()["role"] == "customer"
    r = as_user("admin@example.com").patch(f"/admin/users/{target.user_id}", json={"role": "support"})
    assert r.status_code == 200
    assert customer.get("/auth/me").json()["role"] == "support"


def test_a_non_admin_cant_change_levels(store):
    make_user(store, "support@example.com", "support")
    target = make_user(store, "cust@example.com", "customer")
    r = as_user("support@example.com").patch(f"/admin/users/{target.user_id}", json={"role": "admin"})
    assert r.status_code == 403


def test_the_last_admin_cant_be_removed(store):
    admin = make_user(store, "admin@example.com", "admin")
    r = as_user("admin@example.com").patch(f"/admin/users/{admin.user_id}", json={"role": "customer"})
    assert r.status_code == 409
    assert store.get_by_id(admin.user_id).role == "admin"


def test_an_admin_can_step_down_if_another_remains(store):
    first = make_user(store, "admin@example.com", "admin")
    make_user(store, "other@example.com", "admin")
    r = as_user("admin@example.com").patch(f"/admin/users/{first.user_id}", json={"role": "customer"})
    assert r.status_code == 200


def test_an_unknown_level_is_refused(store):
    admin = make_user(store, "admin@example.com", "admin")
    r = as_user("admin@example.com").patch(f"/admin/users/{admin.user_id}", json={"role": "root"})
    assert r.status_code == 422


# --- AC-19, AC-25: demo accounts ---

def test_demo_accounts_are_hidden_unless_seeding_is_on(client):
    assert client.get("/auth/demo-accounts").json() == []


def test_seeding_is_refused_without_the_setting(store):
    with pytest.raises(auth.SeedingRefused):
        auth.seed_demo_users(store)
    assert store.list_users() == []


def test_seeded_accounts_can_log_in_and_are_listed(store, client, monkeypatch):
    monkeypatch.setattr(get_settings(), "seed_demo_users", True)
    owners = auth.seed_demo_users(store)
    assert set(owners) == {"Asha", "Ravi", "Meera", "Arjun", "Priya", "Kabir", "Neha"}
    listed = client.get("/auth/demo-accounts").json()
    assert sorted({row["role"] for row in listed}) == ["admin", "customer", "support"]
    assert len(listed) == 9
    for row in listed:
        r = TestClient(api.app).post("/auth/login", json={"email": row["email"], "password": row["password"]})
        assert r.status_code == 200 and r.json()["role"] == row["role"]


def test_demo_orders_can_be_given_owners(store, monkeypatch):
    monkeypatch.setattr(get_settings(), "seed_demo_users", True)
    owners = auth.seed_demo_users(store)
    get_order_repo().assign_owners(owners)
    assert [o["order_id"] for o in get_order_repo().list_for_owner(owners["Asha"])] == ["1001"]
