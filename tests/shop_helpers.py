"""Shared by the tests in tests/shop/."""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


CATALOGUE = json.loads((ROOT / "src/shophelper/data/products.json").read_text(encoding="utf-8"))


PRODUCTS = CATALOGUE["products"]


CATEGORIES = CATALOGUE["categories"]


AUDIO = [p for p in PRODUCTS if p["category"] == "audio"]


def product(slug):
    return next(p for p in PRODUCTS if p["slug"] == slug)


MOUSE, CASE, SPEAKER = product("wireless-mouse"), product("phone-case"), product("bluetooth-speaker")


def put(client, item, quantity):
    return client.put(f"/cart/{item['id']}", json={"quantity": quantity})


def quantities(client):
    return {line["product"]["id"]: line["quantity"] for line in client.get("/cart").json()["items"]}
