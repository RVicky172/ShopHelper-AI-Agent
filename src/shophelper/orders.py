"""Order lookups and refunds.

Two interchangeable stores: an in-memory one seeded from data/orders.json (used for
local runs and tests) and a DynamoDB one (seeded by Terraform from the same JSON).
"""

import json
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

import boto3

from shophelper.config import get_settings

SEED_FILE = Path(__file__).parent / "data" / "orders.json"
REFUND_WINDOW_DAYS = 30


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


class OrderRepo(Protocol):
    def get(self, order_id: str) -> dict[str, Any] | None: ...
    def mark_refunded(self, order_id: str, amount: float, reason: str) -> None: ...


class InMemoryOrderRepo:
    def __init__(self) -> None:
        self._orders = load_seed_orders()

    def get(self, order_id: str) -> dict[str, Any] | None:
        order = self._orders.get(order_id)
        return dict(order) if order else None

    def mark_refunded(self, order_id: str, amount: float, reason: str) -> None:
        self._orders[order_id].update(status="refunded", refund_amount=amount, refund_reason=reason)


class DynamoOrderRepo:
    def __init__(self, table_name: str, region: str) -> None:
        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def get(self, order_id: str) -> dict[str, Any] | None:
        item = self._table.get_item(Key={"order_id": order_id}).get("Item")
        if not item:
            return None
        return {k: float(v) if isinstance(v, Decimal) else v for k, v in item.items()}

    def mark_refunded(self, order_id: str, amount: float, reason: str) -> None:
        self._table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :s, refund_amount = :a, refund_reason = :r",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "refunded", ":a": Decimal(str(amount)), ":r": reason},
        )


@lru_cache
def get_order_repo() -> OrderRepo:
    settings = get_settings()
    if settings.orders_table:
        return DynamoOrderRepo(settings.orders_table, settings.aws_region)
    return InMemoryOrderRepo()


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
