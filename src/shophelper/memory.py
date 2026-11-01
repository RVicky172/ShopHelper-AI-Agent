"""Step 3: conversation history in DynamoDB (TTL-expired), with an in-memory fallback."""

import time
from collections import defaultdict
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, Protocol

import boto3
from boto3.dynamodb.conditions import Key

from shophelper.config import get_settings


class HistoryStore(Protocol):
    def load(self, session_id: str, limit: int) -> list[dict[str, Any]]: ...
    def append(self, session_id: str, role: str, text: str, **meta: Any) -> None: ...


class InMemoryHistory:
    def __init__(self) -> None:
        self._items: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def load(self, session_id: str, limit: int) -> list[dict[str, Any]]:
        return self._items[session_id][-limit:]

    def append(self, session_id: str, role: str, text: str, **meta: Any) -> None:
        self._items[session_id].append({"role": role, "text": text, **meta})


class DynamoHistory:
    def __init__(self, table_name: str, region: str, ttl_days: int) -> None:
        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)
        self._ttl_seconds = ttl_days * 86400

    def load(self, session_id: str, limit: int) -> list[dict[str, Any]]:
        resp = self._table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=False,  # newest first, then reverse
            Limit=limit,
        )
        items = list(reversed(resp["Items"]))
        return [{k: v for k, v in i.items() if k not in ("session_id", "expires_at")} for i in items]

    def append(self, session_id: str, role: str, text: str, **meta: Any) -> None:
        self._table.put_item(
            Item={
                "session_id": session_id,
                # ISO timestamp sorts chronologically; role suffix avoids same-microsecond clashes
                "ts": f"{datetime.now(UTC).isoformat()}#{role}",
                "role": role,
                "text": text,
                "expires_at": int(time.time()) + self._ttl_seconds,
                **meta,
            }
        )


@lru_cache
def get_history_store() -> HistoryStore:
    s = get_settings()
    if s.history_table:
        return DynamoHistory(s.history_table, s.aws_region, s.history_ttl_days)
    return InMemoryHistory()


def to_converse_messages(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """History rows -> Converse messages. Converse needs the first message to be 'user'."""
    messages = [{"role": t["role"], "content": [{"text": t["text"]}]} for t in turns]
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages
