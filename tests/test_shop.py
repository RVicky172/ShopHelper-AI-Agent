"""The shop: catalogue, cart and checkout. Offline, using the in-memory backends."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from shophelper import api, auth, cart, catalog, graph, raw_agent
from shophelper.config import get_settings
from shophelper.orders import SEED_FILE, demo_email, get_order_repo, refund_eligibility, sample_orders

ROOT = Path(__file__).parent.parent
CATALOGUE = json.loads((ROOT / "src/shophelper/data/products.json").read_text(encoding="utf-8"))
PRODUCTS = CATALOGUE["products"]
CATEGORIES = CATALOGUE["categories"]
AUDIO = [p for p in PRODUCTS if p["category"] == "audio"]


@pytest.fixture(autouse=True)
def accounts_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_enabled", True)
    caches = (auth.get_user_store, get_order_repo, catalog.get_product_repo, cart.get_cart_store)
    for cache in caches:
        cache.cache_clear()
    yield
    for cache in caches:
        cache.cache_clear()


@pytest.fixture
def guest():
    """No cookie: the catalogue has to work for someone who never signed in."""
    return TestClient(api.app)


@pytest.fixture
def sign_in(monkeypatch):
    """Returns a client signed in as a demo user, with a real session and no slow password hashing."""
    monkeypatch.setattr(get_settings(), "seed_demo_users", True)
    store = auth.get_user_store()
    owners = auth.seed_demo_users(store)
    get_order_repo().assign_owners(owners)

    def client_for(email_name: str) -> TestClient:
        user = store.get_by_email(demo_email(email_name))
        return TestClient(api.app, cookies={auth.COOKIE_NAME: auth.start_session(store, user.user_id)})

    return client_for


@pytest.fixture
def asha(sign_in):
    return sign_in("Asha")


@pytest.fixture
def ravi(sign_in):
    return sign_in("Ravi")


def product(slug):
    return next(p for p in PRODUCTS if p["slug"] == slug)


MOUSE, CASE, SPEAKER = product("wireless-mouse"), product("phone-case"), product("bluetooth-speaker")


def put(client, item, quantity):
    return client.put(f"/cart/{item['id']}", json={"quantity": quantity})


def quantities(client):
    return {line["product"]["id"]: line["quantity"] for line in client.get("/cart").json()["items"]}


# --- AC-6: the catalogue file ---

def test_the_catalogue_has_enough_categories_and_products():
    assert len(CATEGORIES) >= 8
    assert len(PRODUCTS) >= 40


def test_every_product_is_complete():
    known = {c["slug"] for c in CATEGORIES}
    for p in PRODUCTS:
        assert p["name"] and p["description"] and p["category"] in known, p
        assert p["price"] > 0 and round(p["price"], 2) == p["price"], p
        assert 1 <= p["rating"] <= 5 and p["rating_count"] > 0, p
        assert len(p["specs"]) >= 3, p
        assert p["added_at"], p


def test_ids_and_slugs_are_unique():
    """Guest carts store ids, and product pages use slugs."""
    assert len({p["id"] for p in PRODUCTS}) == len(PRODUCTS)
    assert len({p["slug"] for p in PRODUCTS}) == len(PRODUCTS)


def test_every_category_can_show_three_related_products():
    for category in CATEGORIES:
        assert sum(p["category"] == category["slug"] for p in PRODUCTS) >= 4, category


def test_every_ordered_item_is_a_product_at_the_price_paid():
    prices = {p["name"]: p["price"] for p in PRODUCTS}
    orders = json.loads(SEED_FILE.read_text(encoding="utf-8")) + sample_orders("Anyone")
    assert len(orders) == 9
    for order in orders:
        assert prices.get(order["item"]) == order["total"], order


def test_every_product_has_exactly_one_illustration():
    slugs = {p["slug"] for p in PRODUCTS}
    drawn = {f.stem for f in (ROOT / "web/public/products").glob("*.svg")}
    assert drawn == slugs


def category_tints():
    """Each category's light and dark colour, from the design tokens."""
    css = (ROOT / "web/src/index.css").read_text(encoding="utf-8")
    light, dark = css.split("@media (prefers-color-scheme: dark)")[:2]
    names = (ROOT / "web/src/shop/categories.ts").read_text(encoding="utf-8")
    tints = {}
    for category in CATEGORIES:
        name = re.search(rf"'?{category['slug']}'?: '(\w+)'", names)[1]
        tints[category["slug"]] = tuple(
            re.search(rf"--color-tint-{name}: (#\w+);", block)[1].lower() for block in (light, dark)
        )
    return tints


@pytest.mark.parametrize("item", PRODUCTS, ids=lambda p: p["slug"])
def test_each_illustration_follows_the_conventions(item):
    svg = (ROOT / "web/public/products" / f"{item['slug']}.svg").read_text(encoding="utf-8")
    assert 'viewBox="0 0 400 400"' in svg
    assert f"<title>{item['name']}</title>" in svg
    assert "<text" not in svg and "<image" not in svg and "<script" not in svg
    assert "http" not in svg.replace("http://www.w3.org/2000/svg", "")  # nothing loaded from elsewhere
    assert len(svg) < 6000
    light, dark = category_tints()[item["category"]]
    head, night = svg.split("@media (prefers-color-scheme: dark)")
    assert re.search(r"--tint: (#\w+)", head)[1].lower() == light
    assert re.search(r"--tint: (#\w+)", night)[1].lower() == dark
    assert "--ink: #EEF1F8" in night and "--paper: #141A2E" in night


# --- AC-7, AC-8, AC-9, AC-13: reading the catalogue ---

def test_categories_list_their_product_counts(guest):
    body = guest.get("/categories").json()
    assert [c["slug"] for c in body] == [c["slug"] for c in CATEGORIES]
    assert sum(c["count"] for c in body) == len(PRODUCTS)
    audio = next(c for c in body if c["slug"] == "audio")
    assert (audio["name"], audio["count"]) == ("Audio", len(AUDIO))


def test_each_category_offers_its_top_rated_product_for_the_landing_page(guest):
    """AC-5: one call gives the landing page a product from every category."""
    for category in guest.get("/categories").json():
        mine = [p for p in PRODUCTS if p["category"] == category["slug"]]
        best = max(mine, key=lambda p: (p["rating"], p["rating_count"]))
        assert category["cover"] == {"slug": best["slug"], "name": best["name"]}


def test_a_list_stops_at_twelve_and_reports_the_total(guest):
    body = guest.get("/products").json()
    assert len(body["items"]) == 12
    assert body["total"] == len(PRODUCTS)


def test_paging_reaches_every_product_exactly_once(guest):
    seen = []
    for offset in range(0, len(PRODUCTS), 12):
        seen += [p["id"] for p in guest.get("/products", params={"offset": offset}).json()["items"]]
    assert sorted(seen) == sorted(p["id"] for p in PRODUCTS)


def test_paging_past_the_end_is_empty_but_keeps_the_total(guest):
    body = guest.get("/products", params={"offset": 1000}).json()
    assert body == {"items": [], "total": len(PRODUCTS)}


@pytest.mark.parametrize("params", [{"limit": 13}, {"limit": 0}, {"offset": -1}])
def test_a_list_cant_be_made_larger_than_a_page(guest, params):
    assert guest.get("/products", params=params).status_code == 422


def test_a_category_lists_only_its_products(guest):
    body = guest.get("/products", params={"category": "audio"}).json()
    assert {p["category"] for p in body["items"]} == {"audio"}
    assert body["total"] == len(AUDIO)


def test_an_unknown_category_is_not_found(guest):
    assert guest.get("/products", params={"category": "nope"}).status_code == 404


@pytest.mark.parametrize("sort, key, reverse", [
    ("price_asc", "price", False),
    ("price_desc", "price", True),
    ("rating", "rating", True),
    ("newest", "added_at", True),
])
def test_sorting(guest, sort, key, reverse):
    items = guest.get("/products", params={"sort": sort}).json()["items"]
    values = [p[key] for p in items]
    assert values == sorted(values, reverse=reverse)
    first = max if reverse else min
    assert values[0] == first(p[key] for p in PRODUCTS)


def test_a_sort_order_stays_the_same_across_pages(guest):
    """Equal ratings need a tie-break, or a product could appear on two pages and vanish from a third."""
    first = guest.get("/products", params={"sort": "rating"}).json()["items"]
    again = guest.get("/products", params={"sort": "rating"}).json()["items"]
    assert first == again
    tied = [(p["rating"], p["rating_count"], p["id"]) for p in first]
    assert tied == sorted(tied, key=lambda t: (-t[0], -t[1], t[2]))


def test_an_unknown_sort_is_refused(guest):
    assert guest.get("/products", params={"sort": "price; DROP TABLE products"}).status_code == 422


def test_a_product_page_has_everything_and_three_related(guest):
    product = next(p for p in PRODUCTS if p["slug"] == "bluetooth-speaker")
    body = guest.get("/products/bluetooth-speaker").json()
    assert {k: body[k] for k in product} == product
    related = body["related"]
    assert len(related) >= 3
    assert {p["category"] for p in related} == {"audio"}
    assert product["id"] not in {p["id"] for p in related}


def test_every_product_has_related_products(guest):
    for product in PRODUCTS:
        assert len(guest.get(f"/products/{product['slug']}").json()["related"]) >= 3, product


def test_an_unknown_product_is_not_found(guest):
    assert guest.get("/products/nope").status_code == 404


def test_a_guests_cart_page_can_read_its_products_in_one_call(guest):
    """A guest's cart stores ids only, so the cart page reads names and prices from here."""
    body = guest.get("/products", params={"ids": [18, 8, 99999]}).json()
    assert [p["id"] for p in body["items"]] == [8, 18]
    assert body["total"] == 2


def test_reading_by_id_isnt_held_to_one_page(guest):
    ids = [p["id"] for p in PRODUCTS[:20]]
    assert len(guest.get("/products", params={"ids": ids}).json()["items"]) == 20


def test_reading_by_id_has_a_limit(guest):
    assert guest.get("/products", params={"ids": list(range(101))}).status_code == 422


# --- AC-31: none of this exists on AWS ---

@pytest.mark.parametrize("path", ["/categories", "/products", "/products/bluetooth-speaker"])
def test_the_shop_doesnt_exist_with_accounts_off(guest, monkeypatch, path):
    monkeypatch.setattr(get_settings(), "auth_enabled", False)
    assert guest.get(path).status_code == 404


# --- AC-14: the cart ---

def test_a_new_cart_is_empty(asha):
    assert asha.get("/cart").json() == {"items": [], "count": 0, "total": 0}


def test_adding_shows_lines_and_totals_from_the_catalogue(asha):
    assert put(asha, MOUSE, 3).status_code == 200
    put(asha, CASE, 1)
    body = asha.get("/cart").json()
    assert body["count"] == 4
    assert body["total"] == 199.96  # 3 x 59.99 + 19.99, with no floating point dust
    line = next(x for x in body["items"] if x["product"]["id"] == MOUSE["id"])
    assert line["quantity"] == 3 and line["line_total"] == 179.97
    assert line["product"]["price"] == 59.99 and line["product"]["slug"] == "wireless-mouse"


def test_changing_a_quantity_replaces_it(asha):
    put(asha, MOUSE, 3)
    put(asha, MOUSE, 1)
    assert quantities(asha) == {MOUSE["id"]: 1}


def test_quantity_zero_removes_the_item(asha):
    put(asha, MOUSE, 3)
    put(asha, MOUSE, 0)
    assert quantities(asha) == {}


@pytest.mark.parametrize("quantity", [11, -1, 1.5, "lots"])
def test_a_quantity_outside_one_to_ten_is_refused(asha, quantity):
    put(asha, MOUSE, 2)
    assert put(asha, MOUSE, quantity).status_code == 422
    assert quantities(asha) == {MOUSE["id"]: 2}


def test_an_unknown_product_cant_go_in_a_cart(asha):
    assert asha.put("/cart/99999", json={"quantity": 1}).status_code == 404
    assert quantities(asha) == {}


# --- AC-16: merging a guest's cart ---

def merge(client, *items):
    return client.post("/cart/merge", json={"items": [{"product_id": i, "quantity": q} for i, q in items]})


def test_a_guest_cart_merges_into_an_empty_account_without_any_notice(asha):
    body = merge(asha, (MOUSE["id"], 2), (CASE["id"], 1)).json()
    assert quantities(asha) == {MOUSE["id"]: 2, CASE["id"]: 1}
    assert body["changes"] == []
    assert body["cart"]["count"] == 3


def test_items_in_both_carts_add_up_and_the_shopper_is_told(asha):
    put(asha, MOUSE, 2)
    body = merge(asha, (MOUSE["id"], 3)).json()
    assert quantities(asha) == {MOUSE["id"]: 5}
    assert body["changes"] == [
        {"kind": "combined", "product_id": MOUSE["id"], "name": "Wireless Mouse", "quantity": 5}
    ]


def test_a_merge_keeps_items_only_the_account_had(asha):
    put(asha, SPEAKER, 1)
    merge(asha, (MOUSE["id"], 1))
    assert quantities(asha) == {SPEAKER["id"]: 1, MOUSE["id"]: 1}


def test_a_merge_stops_at_ten_and_says_so(asha):
    put(asha, MOUSE, 8)
    body = merge(asha, (MOUSE["id"], 5)).json()
    assert quantities(asha) == {MOUSE["id"]: 10}
    assert body["changes"] == [
        {"kind": "capped", "product_id": MOUSE["id"], "name": "Wireless Mouse", "quantity": 10}
    ]


def test_nothing_is_dropped_silently(asha):
    body = merge(asha, (99999, 1), (CASE["id"], 0), (MOUSE["id"], 1)).json()
    assert quantities(asha) == {MOUSE["id"]: 1}
    reported = [(c["kind"], c["product_id"]) for c in body["changes"]]
    assert reported == [("unavailable", 99999), ("unavailable", CASE["id"])]


def test_a_tampered_guest_cart_cant_beat_the_cap(asha):
    """The guest copy lives in the browser, so its numbers can be anything."""
    merge(asha, (MOUSE["id"], 10**30), (CASE["id"], 6), (CASE["id"], 6))
    assert quantities(asha) == {MOUSE["id"]: 10, CASE["id"]: 10}


def test_a_merge_cant_be_used_to_flood_a_cart(asha):
    assert merge(asha, *[(MOUSE["id"], 1)] * 101).status_code == 422


# --- AC-18: a cart belongs to one person ---

def test_one_users_cart_is_invisible_to_another(asha, ravi):
    put(asha, MOUSE, 2)
    assert quantities(ravi) == {}
    assert quantities(asha) == {MOUSE["id"]: 2}  # positive control


def test_changing_your_cart_never_touches_anothers(asha, ravi):
    put(asha, MOUSE, 2)
    put(ravi, MOUSE, 7)
    put(ravi, CASE, 1)
    put(ravi, CASE, 0)
    merge(ravi, (MOUSE["id"], 1))
    assert quantities(asha) == {MOUSE["id"]: 2}
    assert quantities(ravi) == {MOUSE["id"]: 8}


def test_the_cart_can_only_be_named_by_the_session(asha, ravi):
    """No cart route takes a user id, so there is nothing to tamper with."""
    paths = [path for path in api.app.openapi()["paths"] if path.startswith("/cart")]
    assert sorted(paths) == ["/cart", "/cart/merge", "/cart/{product_id}"]
    put(asha, MOUSE, 2)
    assert ravi.get("/cart", params={"user_id": 1, "owner_id": 1}).json()["items"] == []


@pytest.mark.parametrize("method, path", [
    ("GET", "/cart"), ("PUT", "/cart/1"), ("POST", "/cart/merge"),
])
def test_a_guest_has_no_server_cart(guest, method, path):
    assert guest.request(method, path).status_code == 401


@pytest.mark.parametrize("method, path", [
    ("GET", "/cart"), ("PUT", "/cart/1"), ("POST", "/cart/merge"),
])
def test_the_cart_doesnt_exist_with_accounts_off(guest, monkeypatch, method, path):
    monkeypatch.setattr(get_settings(), "auth_enabled", False)
    assert guest.request(method, path).status_code == 404


# --- AC-19, AC-20, AC-21: checkout ---

def buy(client, *lines):
    for item, quantity in lines:
        put(client, item, quantity)
    return client.post("/checkout")


def test_checkout_places_an_order_at_catalogue_prices(asha):
    response = buy(asha, (MOUSE, 2), (CASE, 1))
    assert response.status_code == 201
    order = response.json()
    assert order["total"] == 139.97
    assert order["status"] == "processing"
    assert order["customer"] == "Asha"
    assert order["items"] == [
        {"product_id": MOUSE["id"], "name": "Wireless Mouse", "price": 59.99, "quantity": 2},
        {"product_id": CASE["id"], "name": "Phone Case", "price": 19.99, "quantity": 1},
    ]


@pytest.mark.parametrize("sent", [
    {"total": 0.01},
    {"price": 0.01, "items": [{"product_id": 8, "price": 0.01, "quantity": 1}]},
    {"order": {"total": 0.01, "status": "delivered", "owner_id": 1}},
])
def test_a_price_sent_with_the_request_changes_nothing(asha, sent):
    put(asha, MOUSE, 1)
    order = asha.post("/checkout", json=sent).json()
    assert order["total"] == 59.99
    assert order["status"] == "processing"
    assert order["items"][0]["price"] == 59.99


def test_a_quantity_in_the_request_changes_nothing(asha):
    put(asha, MOUSE, 1)
    assert asha.post("/checkout", json={"items": [{"product_id": 8, "quantity": 9}]}).json()["total"] == 59.99


def test_an_order_keeps_the_shape_the_agent_and_refunds_expect(asha):
    order = buy(asha, (MOUSE, 1), (CASE, 1), (SPEAKER, 1)).json()
    assert order["item"] == "Bluetooth Speaker + 2 more"  # lines are in product id order
    assert order["order_id"].isdigit()
    assert order["ordered_at"] and order["estimated_delivery"]
    stored = get_order_repo().get(order["order_id"])
    assert refund_eligibility(stored, 1.0)[0] is False  # not delivered yet


def test_one_product_is_named_alone_even_with_several_of_it(asha):
    assert buy(asha, (SPEAKER, 3)).json()["item"] == "Bluetooth Speaker"


def test_a_placed_order_empties_the_cart(asha):
    buy(asha, (MOUSE, 2))
    assert quantities(asha) == {}


def test_an_empty_cart_cant_be_checked_out(asha):
    before = len(asha.get("/orders").json())
    assert asha.post("/checkout").status_code == 409
    assert len(asha.get("/orders").json()) == before


def test_a_double_click_places_one_order(asha):
    before = len(asha.get("/orders").json())
    assert buy(asha, (MOUSE, 1)).status_code == 201
    assert asha.post("/checkout").status_code == 409
    assert len(asha.get("/orders").json()) == before + 1


def test_each_order_gets_its_own_number(asha):
    assert buy(asha, (MOUSE, 1)).json()["order_id"] != buy(asha, (MOUSE, 1)).json()["order_id"]


def test_checkout_needs_a_session(guest):
    assert guest.post("/checkout").status_code == 401


def test_checkout_doesnt_exist_with_accounts_off(guest, monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_enabled", False)
    assert guest.post("/checkout").status_code == 404


def test_an_order_belongs_to_the_buyer_alone(asha, ravi):
    order_id = buy(asha, (MOUSE, 1)).json()["order_id"]
    assert order_id in [o["order_id"] for o in asha.get("/orders").json()]  # positive control
    assert order_id not in [o["order_id"] for o in ravi.get("/orders").json()]


def test_only_the_buyers_identity_reaches_the_order(asha, ravi):
    order_id = buy(asha, (MOUSE, 1)).json()["order_id"]
    asha_id = auth.get_user_store().get_by_email(demo_email("Asha")).user_id
    ravi_id = auth.get_user_store().get_by_email(demo_email("Ravi")).user_id
    assert get_order_repo().get_for_owner(order_id, asha_id)["item"] == "Wireless Mouse"
    assert get_order_repo().get_for_owner(order_id, ravi_id) is None


def test_checkout_leaves_other_carts_alone(asha, ravi):
    put(ravi, CASE, 2)
    buy(asha, (MOUSE, 1))
    assert quantities(ravi) == {CASE["id"]: 2}


def test_the_response_doesnt_expose_the_owner_id(asha):
    assert "owner_id" not in buy(asha, (MOUSE, 1)).json()


def test_a_demo_reset_keeps_bought_orders(asha):
    order_id = buy(asha, (MOUSE, 1)).json()["order_id"]
    get_order_repo().reset()
    assert order_id in [o["order_id"] for o in asha.get("/orders").json()]


# --- AC-41: mark delivered ---

@pytest.fixture
def support(sign_in, monkeypatch):
    return sign_in("support")


@pytest.fixture
def admin(sign_in, monkeypatch):
    return sign_in("admin")


def deliver(client, order_id):
    return client.post(f"/orders/{order_id}/deliver")


def test_staff_can_mark_a_bought_order_delivered(asha, support):
    order_id = buy(asha, (MOUSE, 1)).json()["order_id"]
    response = deliver(support, order_id)
    assert response.status_code == 200
    assert response.json()["status"] == "delivered"
    assert response.json()["delivered_at"] == datetime.now(UTC).date().isoformat()
    assert "estimated_delivery" not in response.json()


def test_a_delivered_order_can_be_refunded(asha, support):
    order_id = buy(asha, (MOUSE, 1)).json()["order_id"]
    deliver(support, order_id)
    assert refund_eligibility(get_order_repo().get(order_id), 59.99)[0] is True


def test_admins_can_too_and_shipped_orders_count(admin):
    assert deliver(admin, "1002").json()["status"] == "delivered"  # shipped


def test_customers_cant_even_on_their_own_order(asha):
    order_id = buy(asha, (MOUSE, 1)).json()["order_id"]
    assert deliver(asha, order_id).status_code == 403
    assert get_order_repo().get(order_id)["status"] == "processing"


def test_customers_learn_nothing_from_order_numbers(asha):
    assert deliver(asha, "99999").status_code == 403  # same answer as a real order


@pytest.mark.parametrize("order_id, status", [
    ("1001", "delivered"), ("1005", "cancelled"), ("1007", "refunded"),
])
def test_only_processing_or_shipped_orders_can_be_marked(support, order_id, status):
    before = get_order_repo().get(order_id)
    assert before["status"] == status
    assert deliver(support, order_id).status_code == 409
    assert get_order_repo().get(order_id) == before


def test_an_unknown_order_is_not_found(support):
    assert deliver(support, "99999").status_code == 404


def test_marking_delivered_needs_a_session(guest):
    assert deliver(guest, "1002").status_code == 401


def test_marking_delivered_doesnt_exist_with_accounts_off(guest, monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_enabled", False)
    assert deliver(guest, "1002").status_code == 404


# --- AC-38, AC-39: a general store, with terms for lifestyle products ---

def test_the_agent_isnt_told_it_only_sells_electronics():
    for prompt in (graph.SYSTEM_PROMPT, raw_agent.SYSTEM_PROMPT):
        assert "electronics store" not in prompt
        assert "home and kitchen" in prompt.lower()


def policy(name):
    return (ROOT / "knowledge/policies" / name).read_text(encoding="utf-8")


def test_returns_policy_covers_lifestyle_products():
    line = next(x for x in policy("returns.md").splitlines() if "lifestyle" in x.lower())
    assert "30 days" in line and "no restocking fee" in line


def test_warranty_policy_covers_lifestyle_products():
    line = next(x for x in policy("warranty.md").splitlines() if "lifestyle" in x.lower())
    assert "90-day" in line and "defects" in line


@pytest.mark.parametrize("name", ["returns.md", "warranty.md"])
@pytest.mark.parametrize("category", [
    "audio", "keyboards and mice", "laptop accessories", "phone accessories", "power and charging",
])
def test_each_electronics_category_is_named(name, category):
    """A phone case doesn't sound like electronics, and the agent gave it the lifestyle terms until this."""
    line = next(x for x in policy(name).splitlines() if x.startswith("- **Electronics** means"))
    assert category in line


def test_electronics_terms_havent_changed():
    assert "Opened electronics that are not defective" in policy("returns.md")
    assert "10% restocking fee" in policy("returns.md")
    assert "All electronics include a **1-year limited warranty**" in policy("warranty.md")


@pytest.mark.parametrize("name", ["returns.md", "warranty.md"])
@pytest.mark.parametrize("category", ["home and kitchen", "bags and travel", "fitness and outdoors"])
def test_each_lifestyle_category_is_named(name, category):
    assert category in policy(name).lower()


# --- AC-11: the return policy page shows what the agent reads ---

def test_the_shops_copy_of_the_return_policy_matches_the_agents():
    shown = (ROOT / "web/src/shop/returns-policy.md").read_text(encoding="utf-8")
    assert shown == policy("returns.md")


def test_every_category_has_a_colour():
    tints = (ROOT / "web/src/shop/categories.ts").read_text(encoding="utf-8")
    css = (ROOT / "web/src/index.css").read_text(encoding="utf-8")
    for category in CATEGORIES:
        name = re.search(rf"'?{category['slug']}'?: '(\w+)'", tints)
        assert name, category
        assert f"--color-tint-{name[1]}:" in css
