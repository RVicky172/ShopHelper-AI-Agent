"""Order lookups and refunds.

Two interchangeable stores: an in-memory one seeded from data/orders.json (used for
local runs and tests) and a DynamoDB one (seeded by Terraform from the same JSON).
"""

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, cast

import boto3

from shophelper.core import db
from shophelper.core.config import get_settings

SEED_FILE = Path(__file__).parents[1] / "data" / "orders.json"
REFUND_WINDOW_DAYS = 30
FIRST_SAMPLE_ORDER = 2001
DELIVERY_DAYS = 5
DELIVERABLE = ("processing", "shipped")


def _days_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def load_seed_orders() -> dict[str, dict[str, Any]]:
    """Seed orders with relative day offsets turned into ISO dates."""
    orders = {}
    for raw in json.loads(SEED_FILE.read_text()):
        order = {k: v for k, v in raw.items() if not k.endswith("_days_ago") and k != "eta_days"}
        order["ordered_at"] = _days_ago(raw["ordered_days_ago"])
        if "delivered_days_ago" in raw:
            order["delivered_at"] = _days_ago(raw["delivered_days_ago"])
        if "eta_days" in raw:
            order["estimated_delivery"] = _days_ago(-raw["eta_days"])
        orders[order["order_id"]] = order
    return orders


def demo_email(customer: str) -> str:
    return f"{customer.lower()}@demo.shophelper.test"


def sample_orders(customer: str) -> list[dict[str, Any]]:
    """What a new sign-up starts with, so they can try everything straight away."""
    return [
        {
            "customer": customer, "item": "Wireless Earbuds", "total": 79.0, "status": "delivered",
            "ordered_at": _days_ago(7), "delivered_at": _days_ago(3),
        },
        {
            "customer": customer, "item": "Portable Charger", "total": 35.5, "status": "shipped",
            "ordered_at": _days_ago(2), "estimated_delivery": _days_ago(-3),
        },
    ]


def new_order(order_id: str, customer: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
    """An order from cart lines, in the same shape as every other order. `item` and `total` are what
    `get_order_status`, the refund checks and the staff queue already read, so none of them change."""
    more = len(lines) - 1
    return {
        "order_id": order_id,
        "customer": customer,
        "item": lines[0]["name"] + (f" + {more} more" if more else ""),
        "total": round(sum(line["price"] * line["quantity"] for line in lines), 2),
        "status": "processing",
        "ordered_at": _days_ago(0),
        "estimated_delivery": _days_ago(-DELIVERY_DAYS),
        "items": lines,
    }


class OrderRepo(Protocol):
    def get(self, order_id: str) -> dict[str, Any] | None: ...
    def get_for_owner(self, order_id: str, owner_id: int | None) -> dict[str, Any] | None: ...
    def mark_refunded(self, order_id: str, amount: float, reason: str) -> None: ...


class AccountOrderRepo(OrderRepo, Protocol):
    """Accounts exist only locally, so the AWS repo has none of this."""

    def list_all(self) -> list[dict[str, Any]]: ...
    def list_for_owner(self, owner_id: int) -> list[dict[str, Any]]: ...
    def create_sample_orders(self, owner_id: int, customer: str) -> None: ...
    def add_order(
        self, owner_id: int, customer: str, lines: list[dict[str, Any]], conn: Any = None
    ) -> dict[str, Any]: ...
    def mark_delivered(self, order_id: str) -> dict[str, Any] | None: ...
    def assign_owners(self, owners: dict[str, int]) -> None: ...
    def reset(self) -> None: ...


class InMemoryOrderRepo:
    def __init__(self) -> None:
        self._orders = load_seed_orders()

    def get(self, order_id: str) -> dict[str, Any] | None:
        order = self._orders.get(order_id)
        return dict(order) if order else None

    def get_for_owner(self, order_id: str, owner_id: int | None) -> dict[str, Any] | None:
        order = self._orders.get(order_id)
        if owner_id is None or not order or order.get("owner_id") != owner_id:
            return None
        return {k: v for k, v in order.items() if k != "owner_id"}

    def mark_refunded(self, order_id: str, amount: float, reason: str) -> None:
        self._orders[order_id].update(status="refunded", refund_amount=amount, refund_reason=reason)

    def list_for_owner(self, owner_id: int) -> list[dict[str, Any]]:
        return [dict(o) for o in self._orders.values() if o.get("owner_id") == owner_id]

    def list_all(self) -> list[dict[str, Any]]:
        return [{k: v for k, v in o.items() if k != "owner_id"} for o in self._orders.values()]

    def reset(self) -> None:
        for order_id, order in load_seed_orders().items():
            owner = self._orders.get(order_id, {}).get("owner_id")
            self._orders[order_id] = {**order, "owner_id": owner} if owner else order

    def create_sample_orders(self, owner_id: int, customer: str) -> None:
        for order in sample_orders(customer):
            order_id = str(FIRST_SAMPLE_ORDER + len(self._orders))
            self._orders[order_id] = {**order, "order_id": order_id, "owner_id": owner_id}

    def add_order(self, owner_id: int, customer: str, lines: list[dict[str, Any]]) -> dict[str, Any]:
        order = new_order(str(FIRST_SAMPLE_ORDER + len(self._orders)), customer, lines)
        self._orders[order["order_id"]] = {**order, "owner_id": owner_id}
        return order

    def mark_delivered(self, order_id: str) -> dict[str, Any] | None:
        order = self._orders[order_id]
        if order["status"] not in DELIVERABLE:
            return None
        order.pop("estimated_delivery", None)
        order.update(status="delivered", delivered_at=_days_ago(0))
        return {k: v for k, v in order.items() if k != "owner_id"}

    def assign_owners(self, owners: dict[str, int]) -> None:
        for order in self._orders.values():
            if "owner_id" not in order and order["customer"] in owners:
                order["owner_id"] = owners[order["customer"]]


class DynamoOrderRepo:
    def __init__(self, table_name: str, region: str) -> None:
        # boto3 builds its resources at runtime
        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)  # pyright: ignore[reportAttributeAccessIssue]

    def get(self, order_id: str) -> dict[str, Any] | None:
        item = self._table.get_item(Key={"order_id": order_id}).get("Item")
        if not item:
            return None
        return {k: float(v) if isinstance(v, Decimal) else v for k, v in item.items()}

    def get_for_owner(self, order_id: str, owner_id: int | None) -> dict[str, Any] | None:
        return None  # DynamoDB orders have no owners: accounts are never enabled on this backend

    def mark_refunded(self, order_id: str, amount: float, reason: str) -> None:
        self._table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :s, refund_amount = :a, refund_reason = :r",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "refunded", ":a": Decimal(str(amount)), ":r": reason},
        )


class PostgresOrderRepo:
    """Same contract as DynamoOrderRepo. `data` is JSONB, so an order stays a free-form document."""

    def get(self, order_id: str) -> dict[str, Any] | None:
        with db.connect() as conn:
            row = conn.execute("SELECT data FROM orders WHERE order_id = %s", (order_id,)).fetchone()
        return row["data"] if row else None

    def get_for_owner(self, order_id: str, owner_id: int | None) -> dict[str, Any] | None:
        """Isolation lives in this WHERE clause. Someone else's order and a missing one take the
        same path, so nothing downstream can tell them apart."""
        with db.connect() as conn:
            row = conn.execute(
                "SELECT data FROM orders WHERE order_id = %s AND owner_id = %s", (order_id, owner_id)
            ).fetchone()
        return row["data"] if row else None

    def list_all(self) -> list[dict[str, Any]]:
        with db.connect() as conn:
            return [r["data"] for r in conn.execute("SELECT data FROM orders ORDER BY order_id")]

    def mark_refunded(self, order_id: str, amount: float, reason: str) -> None:
        patch = {"status": "refunded", "refund_amount": amount, "refund_reason": reason}
        with db.connect() as conn:
            conn.execute(
                "UPDATE orders SET data = data || %s WHERE order_id = %s", (db.Jsonb(patch), order_id)
            )

    def list_for_owner(self, owner_id: int) -> list[dict[str, Any]]:
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT data FROM orders WHERE owner_id = %s ORDER BY order_id", (owner_id,)
            )
            return [r["data"] for r in rows]

    def create_sample_orders(self, owner_id: int, customer: str) -> None:
        with db.connect() as conn:
            for order in sample_orders(customer):
                # count(*) always returns a row
                order_id = str(conn.execute("SELECT nextval('order_numbers') AS n").fetchone()["n"])  # pyright: ignore[reportOptionalSubscript]
                conn.execute(
                    "INSERT INTO orders (order_id, data, owner_id) VALUES (%s, %s, %s)",
                    (order_id, db.Jsonb({**order, "order_id": order_id}), owner_id),
                )

    def add_order(
        self, owner_id: int, customer: str, lines: list[dict[str, Any]], conn: Any
    ) -> dict[str, Any]:
        """Runs on the caller's connection, so the order and the emptied cart commit together."""
        order_id = str(conn.execute("SELECT nextval('order_numbers') AS n").fetchone()["n"])
        order = new_order(order_id, customer, lines)
        conn.execute(
            "INSERT INTO orders (order_id, data, owner_id) VALUES (%s, %s, %s)",
            (order_id, db.Jsonb(order), owner_id),
        )
        return order

    def mark_delivered(self, order_id: str) -> dict[str, Any] | None:
        """The status check is in the WHERE clause, so it can't race a refund."""
        patch = {"status": "delivered", "delivered_at": _days_ago(0)}
        with db.connect() as conn:
            row = conn.execute(
                "UPDATE orders SET data = (data - 'estimated_delivery') || %s "
                "WHERE order_id = %s AND data->>'status' = ANY(%s) RETURNING data",
                (db.Jsonb(patch), order_id, list(DELIVERABLE)),
            ).fetchone()
        return row["data"] if row else None

    def assign_owners(self, owners: dict[str, int]) -> None:
        with db.connect() as conn:
            for customer, owner_id in owners.items():
                conn.execute(
                    "UPDATE orders SET owner_id = %s WHERE data->>'customer' = %s AND owner_id IS NULL",
                    (owner_id, customer),
                )

    def reset(self) -> None:
        """Put the seed orders back, with fresh dates. Owners and sign-ups' own orders are kept."""
        with db.connect() as conn:
            for order_id, order in load_seed_orders().items():
                conn.execute(
                    "INSERT INTO orders (order_id, data) VALUES (%s, %s) "
                    "ON CONFLICT (order_id) DO UPDATE SET data = EXCLUDED.data",
                    (order_id, db.Jsonb(order)),
                )


@lru_cache
def get_order_repo() -> OrderRepo:
    settings = get_settings()
    if settings.database_url:
        return PostgresOrderRepo()
    if settings.orders_table:
        return DynamoOrderRepo(settings.orders_table, settings.aws_region)
    return InMemoryOrderRepo()


def account_order_repo() -> AccountOrderRepo:
    """For code that only runs with accounts on, where the repo is never the AWS one."""
    return cast(AccountOrderRepo, get_order_repo())


def refund_eligibility(order: dict[str, Any], amount: float) -> tuple[bool, str]:
    """Deterministic policy check run *before* a human is asked to approve."""
    if order["status"] == "refunded":
        return False, "This order has already been refunded."
    if order["status"] != "delivered":
        return False, f"Only delivered orders can be refunded (status is '{order['status']}')."
    delivered = date.fromisoformat(order["delivered_at"])
    age = (datetime.now(UTC).date() - delivered).days
    if age > REFUND_WINDOW_DAYS:
        return False, f"Delivered {age} days ago; the refund window is {REFUND_WINDOW_DAYS} days."
    if amount <= 0 or amount > order["total"]:
        return False, f"Refund amount must be between 0 and the order total ({order['total']})."
    return True, "Eligible for refund."
