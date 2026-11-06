"""The catalogue, carts and checkout on Postgres."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import psycopg
import pytest
from psycopg.types.json import Jsonb

from integration_support import CASE, MOUSE, OLD_SCHEMA, query
from shophelper.core import db
from shophelper.core.config import get_settings
from shophelper.shop.cart import PostgresCartStore
from shophelper.shop.catalog import SQL_ORDER, InMemoryProductRepo, PostgresProductRepo
from shophelper.shop.orders import PostgresOrderRepo, get_order_repo, refund_eligibility

pytestmark = pytest.mark.skipif(not get_settings().database_url, reason="needs the local stack's Postgres")


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

NAMES = {MOUSE: "Wireless Mouse", CASE: "Phone Case"}





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
