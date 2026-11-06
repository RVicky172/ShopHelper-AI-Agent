"""The cart. Offline, using the in-memory backends."""

import pytest

from shop_helpers import CASE, MOUSE, SPEAKER, put, quantities
from shophelper.api import app as api
from shophelper.core.config import get_settings

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
