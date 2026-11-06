"""Who owns each conversation. Used only when accounts are enabled.

Ids come from the server. If clients could choose them, a taken id would fail while a free one
worked, which would reveal that a stranger's conversation exists.
"""

import uuid
from functools import lru_cache
from typing import Any, Protocol

from shophelper.core import db
from shophelper.core.config import get_settings


def new_conversation_id() -> str:
    return f"c-{uuid.uuid4()}"


class ConversationStore(Protocol):
    def create(self, owner_id: int) -> str: ...
    def owner_of(self, session_id: str) -> int | None: ...
    def list_for(self, owner_id: int) -> list[dict[str, Any]]: ...


class InMemoryConversations:
    def __init__(self) -> None:
        self._owners: dict[str, int] = {}

    def create(self, owner_id: int) -> str:
        session_id = new_conversation_id()
        self._owners[session_id] = owner_id
        return session_id

    def owner_of(self, session_id: str) -> int | None:
        return self._owners.get(session_id)

    def list_for(self, owner_id: int) -> list[dict[str, Any]]:
        mine = [s for s, owner in self._owners.items() if owner == owner_id]
        return [{"id": s, "title": "", "updated_at": ""} for s in reversed(mine)]


class PostgresConversations:
    def create(self, owner_id: int) -> str:
        session_id = new_conversation_id()
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO conversations (session_id, owner_id) VALUES (%s, %s)", (session_id, owner_id)
            )
        return session_id

    def owner_of(self, session_id: str) -> int | None:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT owner_id FROM conversations WHERE session_id = %s", (session_id,)
            ).fetchone()
        return row["owner_id"] if row else None

    def list_for(self, owner_id: int) -> list[dict[str, Any]]:
        with db.connect() as conn:
            return conn.execute(
                "SELECT session_id AS id, title, updated_at::text AS updated_at FROM conversations "
                "WHERE owner_id = %s ORDER BY updated_at DESC, session_id",
                (owner_id,),
            ).fetchall()


@lru_cache
def get_conversation_store() -> ConversationStore:
    return PostgresConversations() if get_settings().database_url else InMemoryConversations()
