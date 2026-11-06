"""Postgres access for the local stack. Only used when DATABASE_URL is set.

psycopg is imported inside functions so the AWS runtimes never load it.
"""

from pathlib import Path
from typing import Any

from shophelper.core.config import get_settings

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def Jsonb(value: Any) -> Any:  # noqa: N802 - mirrors psycopg's name
    from psycopg.types.json import Jsonb as _Jsonb

    return _Jsonb(value)


def connect():
    """A short-lived connection. Use `with connect() as conn:` - it commits on success."""
    import psycopg
    from pgvector.psycopg import register_vector
    from psycopg.rows import dict_row

    conn = psycopg.connect(get_settings().database_url, row_factory=dict_row, connect_timeout=5)
    try:
        register_vector(conn)  # lets psycopg send and receive VECTOR columns
    except psycopg.ProgrammingError:
        pass  # the extension doesn't exist until apply_schema() has run
    return conn


def apply_schema() -> None:
    with connect() as conn:
        conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
