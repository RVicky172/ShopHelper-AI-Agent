"""The staff review queue for refunds. Used only when accounts are enabled.

The approval rules read what was stored when the agent paused, never the approval request, so a
reviewer can't change the amount or the owner by sending different values.
"""

from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Any, Protocol

from shophelper import db
from shophelper.auth import Principal
from shophelper.config import get_settings

OPEN_STATUSES = ("pending", "claimed")


class ReviewForbidden(Exception):
    pass


@dataclass(frozen=True)
class RefundRequest:
    id: int
    session_id: str
    order_id: str
    owner_id: int
    amount: float
    reason: str
    needs_supervisor: bool
    status: str = "pending"
    reviewer_id: int | None = None
    note: str = ""


def authorize_review(request: RefundRequest, reviewer: Principal) -> None:
    if reviewer.role not in ("support", "admin"):
        raise ReviewForbidden("Only support staff can review refunds")
    if request.owner_id == reviewer.user_id:
        raise ReviewForbidden("You can't review your own refund")
    if request.needs_supervisor and reviewer.role != "admin":
        raise ReviewForbidden("Refunds over $200 need an admin")


class RefundStore(Protocol):
    def open(self, session_id: str, owner_id: int, payload: dict[str, Any]) -> None: ...
    def open_for_session(self, session_id: str) -> RefundRequest | None: ...
    def last_for_session(self, session_id: str) -> RefundRequest | None: ...
    def list_open(self) -> list[RefundRequest]: ...
    def claim(self, request_id: int, reviewer_id: int, note: str) -> bool: ...
    def finish(self, request_id: int, approved: bool) -> None: ...
    def cancel_open(self) -> None: ...


class InMemoryRefunds:
    def __init__(self) -> None:
        self._requests: dict[int, RefundRequest] = {}

    def open(self, session_id: str, owner_id: int, payload: dict[str, Any]) -> None:
        if self.open_for_session(session_id):
            return
        request_id = len(self._requests) + 1
        self._requests[request_id] = RefundRequest(
            request_id, session_id, payload["order_id"], owner_id, float(payload["amount"]),
            payload.get("reason", ""), payload["needs_supervisor"],
        )

    def open_for_session(self, session_id: str) -> RefundRequest | None:
        return next((r for r in self.list_open() if r.session_id == session_id), None)

    def last_for_session(self, session_id: str) -> RefundRequest | None:
        mine = [r for r in self._requests.values() if r.session_id == session_id]
        return mine[-1] if mine else None

    def list_open(self) -> list[RefundRequest]:
        return [r for r in self._requests.values() if r.status in OPEN_STATUSES]

    def claim(self, request_id: int, reviewer_id: int, note: str) -> bool:
        request = self._requests[request_id]
        if request.status != "pending":
            return False
        self._requests[request_id] = replace(request, status="claimed", reviewer_id=reviewer_id, note=note)
        return True

    def finish(self, request_id: int, approved: bool) -> None:
        status = "approved" if approved else "rejected"
        self._requests[request_id] = replace(self._requests[request_id], status=status)

    def cancel_open(self) -> None:
        for request in self.list_open():
            self._requests[request.id] = replace(request, status="cancelled")


class PostgresRefunds:
    COLUMNS = (
        "id, session_id, order_id, owner_id, amount, reason, needs_supervisor, status, reviewer_id, note"
    )

    @staticmethod
    def _request(row: dict | None) -> RefundRequest | None:
        return RefundRequest(**{**row, "amount": float(row["amount"])}) if row else None

    def open(self, session_id: str, owner_id: int, payload: dict[str, Any]) -> None:
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO refund_requests "
                "(session_id, order_id, owner_id, amount, reason, needs_supervisor) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (session_id) WHERE status IN ('pending', 'claimed') DO NOTHING",
                (session_id, payload["order_id"], owner_id, payload["amount"],
                 payload.get("reason", ""), payload["needs_supervisor"]),
            )

    def open_for_session(self, session_id: str) -> RefundRequest | None:
        with db.connect() as conn:
            return self._request(conn.execute(
                f"SELECT {self.COLUMNS} FROM refund_requests "
                "WHERE session_id = %s AND status IN ('pending', 'claimed')",
                (session_id,),
            ).fetchone())

    def last_for_session(self, session_id: str) -> RefundRequest | None:
        with db.connect() as conn:
            return self._request(conn.execute(
                f"SELECT {self.COLUMNS} FROM refund_requests WHERE session_id = %s ORDER BY id DESC LIMIT 1",
                (session_id,),
            ).fetchone())

    def list_open(self) -> list[RefundRequest]:
        with db.connect() as conn:
            rows = conn.execute(
                f"SELECT {self.COLUMNS} FROM refund_requests "
                "WHERE status IN ('pending', 'claimed') ORDER BY id"
            ).fetchall()
        return [self._request(r) for r in rows]

    def claim(self, request_id: int, reviewer_id: int, note: str) -> bool:
        """One atomic UPDATE: if two reviewers race, the database lets exactly one win."""
        with db.connect() as conn:
            row = conn.execute(
                "UPDATE refund_requests SET status = 'claimed', reviewer_id = %s, note = %s "
                "WHERE id = %s AND status = 'pending' RETURNING id",
                (reviewer_id, note, request_id),
            ).fetchone()
        return row is not None

    def finish(self, request_id: int, approved: bool) -> None:
        with db.connect() as conn:
            conn.execute(
                "UPDATE refund_requests SET status = %s, decided_at = now() WHERE id = %s",
                ("approved" if approved else "rejected", request_id),
            )

    def cancel_open(self) -> None:
        with db.connect() as conn:
            conn.execute(
                "UPDATE refund_requests SET status = 'cancelled', decided_at = now() "
                "WHERE status IN ('pending', 'claimed')"
            )


@lru_cache
def get_refund_store() -> RefundStore:
    return PostgresRefunds() if get_settings().database_url else InMemoryRefunds()
