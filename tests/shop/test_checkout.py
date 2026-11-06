"""Checkout and delivery. Offline, using the in-memory backends."""

from datetime import UTC, datetime

import pytest

from shop_helpers import CASE, MOUSE, SPEAKER, put, quantities
from shophelper.accounts import auth
from shophelper.core.config import get_settings
from shophelper.shop.orders import demo_email, get_order_repo, refund_eligibility

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
