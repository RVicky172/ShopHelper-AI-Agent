"""Signed-in carts. A guest's cart lives in their browser and joins this one at sign-in.

A cart holds product ids and quantities, never prices, so a price can't be tampered with here.
Two interchangeable stores, in memory and Postgres. The merge rules are one function that both use.
"""

from functools import lru_cache
from typing import Any, Protocol

from shophelper import db
from shophelper.catalog import get_product_repo
from shophelper.config import get_settings
from shophelper.orders import PostgresOrderRepo, get_order_repo

MAX_QUANTITY = 10


def merge_items(
    existing: dict[int, int], incoming: list[tuple[int, int]], names: dict[int, str]
) -> tuple[dict[int, int], list[dict[str, Any]]]:
    """Adds a guest's items to an account's cart. Returns the new cart, and everything the shopper
    should be told about. `names` holds the products that exist, by id."""
    changes = []
    wanted: dict[int, int] = {}
    for product_id, quantity in incoming:
        if product_id in names and quantity >= 1:
            wanted[product_id] = wanted.get(product_id, 0) + quantity
        else:
            changes.append({"kind": "unavailable", "product_id": product_id, "name": names.get(product_id)})

    merged = dict(existing)
    for product_id, quantity in wanted.items():
        total = existing.get(product_id, 0) + quantity
        merged[product_id] = min(total, MAX_QUANTITY)
        kind = "capped" if total > MAX_QUANTITY else "combined" if product_id in existing else None
        if kind:
            changes.append({
                "kind": kind, "product_id": product_id, "name": names[product_id],
                "quantity": merged[product_id],
            })
    return merged, changes


class CartStore(Protocol):
    def quantities(self, user_id: int) -> dict[int, int]: ...
    def set_quantity(self, user_id: int, product_id: int, quantity: int) -> None: ...
    def merge(
        self, user_id: int, incoming: list[tuple[int, int]], names: dict[int, str]
    ) -> list[dict[str, Any]]: ...
    def checkout(self, user_id: int, customer: str) -> dict[str, Any] | None: ...


class InMemoryCartStore:
    def __init__(self) -> None:
        self._carts: dict[int, dict[int, int]] = {}

    def quantities(self, user_id: int) -> dict[int, int]:
        return dict(self._carts.get(user_id, {}))

    def set_quantity(self, user_id: int, product_id: int, quantity: int) -> None:
        cart = self._carts.setdefault(user_id, {})
        if quantity:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)

    def merge(
        self, user_id: int, incoming: list[tuple[int, int]], names: dict[int, str]
    ) -> list[dict[str, Any]]:
        self._carts[user_id], changes = merge_items(self.quantities(user_id), incoming, names)
        return changes

    def checkout(self, user_id: int, customer: str) -> dict[str, Any] | None:
        cart = self._carts.pop(user_id, {})
        if not cart:
            return None
        products = get_product_repo().by_ids(list(cart))
        lines = [
            {"product_id": i, "name": products[i]["name"], "price": products[i]["price"], "quantity": count}
            for i, count in sorted(cart.items())
        ]
        return get_order_repo().add_order(user_id, customer, lines)


class PostgresCartStore:
    """Isolation lives in the `user_id` of every statement here. No route takes a user id."""

    def quantities(self, user_id: int) -> dict[int, int]:
        with db.connect() as conn:
            rows = conn.execute("SELECT product_id, quantity FROM cart_items WHERE user_id = %s", (user_id,))
            return {r["product_id"]: r["quantity"] for r in rows}

    def set_quantity(self, user_id: int, product_id: int, quantity: int) -> None:
        with db.connect() as conn:
            if quantity:
                conn.execute(
                    "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s) "
                    "ON CONFLICT (user_id, product_id) DO UPDATE SET quantity = EXCLUDED.quantity",
                    (user_id, product_id, quantity),
                )
            else:
                conn.execute(
                    "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s", (user_id, product_id)
                )

    def merge(
        self, user_id: int, incoming: list[tuple[int, int]], names: dict[int, str]
    ) -> list[dict[str, Any]]:
        with db.connect() as conn:
            # Two tabs merging at once wait here, so the second one sees the first one's result.
            conn.execute("SELECT id FROM users WHERE id = %s FOR UPDATE", (user_id,))
            rows = conn.execute("SELECT product_id, quantity FROM cart_items WHERE user_id = %s", (user_id,))
            merged, changes = merge_items({r["product_id"]: r["quantity"] for r in rows}, incoming, names)
            for product_id, quantity in merged.items():
                conn.execute(
                    "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s) "
                    "ON CONFLICT (user_id, product_id) DO UPDATE SET quantity = EXCLUDED.quantity",
                    (user_id, product_id, quantity),
                )
        return changes

    def checkout(self, user_id: int, customer: str) -> dict[str, Any] | None:
        """One transaction. DELETE ... RETURNING claims the cart: of two requests at the same moment,
        only one gets the rows, and the other finds an empty cart. Prices come from `products`."""
        with db.connect() as conn:
            rows = conn.execute(
                """
                WITH taken AS (
                    DELETE FROM cart_items WHERE user_id = %s RETURNING product_id, quantity
                )
                SELECT p.id AS product_id, p.name, p.price, taken.quantity
                FROM taken JOIN products p ON p.id = taken.product_id
                ORDER BY p.id
                """,
                (user_id,),
            ).fetchall()
            if not rows:
                return None
            lines = [{**row, "price": float(row["price"])} for row in rows]
            return PostgresOrderRepo().add_order(user_id, customer, lines, conn)


@lru_cache
def get_cart_store() -> CartStore:
    return PostgresCartStore() if get_settings().database_url else InMemoryCartStore()


def cart_view(user_id: int) -> dict[str, Any]:
    """The cart as the shopper sees it, always priced from the catalogue."""
    quantities = get_cart_store().quantities(user_id)
    products = get_product_repo().by_ids(list(quantities))
    lines = [
        {
            "product": {k: products[i][k] for k in ("id", "slug", "name", "price", "category")},
            "quantity": quantity,
            "line_total": round(products[i]["price"] * quantity, 2),
        }
        for i, quantity in sorted(quantities.items())
    ]
    return {
        "items": lines,
        "count": sum(line["quantity"] for line in lines),
        "total": round(sum(line["line_total"] for line in lines), 2),
    }
