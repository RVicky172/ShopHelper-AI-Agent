"""The catalogue. Offline, using the in-memory backends."""

import json
import re

import pytest

from shop_helpers import (
    AUDIO,
    CATEGORIES,
    PRODUCTS,
    ROOT,
)
from shophelper.core.config import get_settings
from shophelper.shop.orders import SEED_FILE, sample_orders

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
