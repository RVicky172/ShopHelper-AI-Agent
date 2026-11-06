"""Shared by the integration tests."""

from datetime import UTC, datetime

import psycopg
import pytest
from psycopg.rows import dict_row

from shophelper.accounts import auth
from shophelper.core import db
from shophelper.core.config import get_settings
from shophelper.shop.catalog import PostgresProductRepo
from shophelper.shop.orders import demo_email, get_order_repo

SCRATCH = "shophelper_integration_test"


NOW = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


OLD_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE orders (order_id TEXT PRIMARY KEY, data JSONB NOT NULL);
CREATE TABLE chat_history (
    id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO orders VALUES ('1001', '{"order_id": "1001", "customer": "Asha", "status": "delivered"}');
INSERT INTO chat_history (session_id, role, text) VALUES ('old-session', 'user', 'hello');
"""


def scratch_url(url: str) -> str:
    return url.rsplit("/", 1)[0] + f"/{SCRATCH}"


def query(sql, *args):
    with psycopg.connect(get_settings().database_url, row_factory=dict_row) as conn:
        return conn.execute(sql, args).fetchall()


def seed(monkeypatch):
    monkeypatch.setattr(get_settings(), "seed_demo_users", True)
    return auth.seed_demo_users(auth.get_user_store())


def demo_user(name):
    return auth.PostgresUserStore().get_by_email(demo_email(name))


@pytest.fixture
def empty_db(monkeypatch):
    settings = get_settings()
    with psycopg.connect(settings.database_url, autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {SCRATCH} WITH (FORCE)")
        admin.execute(f"CREATE DATABASE {SCRATCH}")
    original = settings.database_url
    monkeypatch.setattr(settings, "database_url", scratch_url(original))
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()
    yield
    auth.get_user_store.cache_clear()
    get_order_repo.cache_clear()
    monkeypatch.undo()
    with psycopg.connect(original, autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {SCRATCH} WITH (FORCE)")


@pytest.fixture
def fresh_db(empty_db):
    db.apply_schema()


@pytest.fixture
def shoppers(fresh_db, monkeypatch):
    PostgresProductRepo().seed()
    return seed(monkeypatch)


MOUSE, CASE = 8, 18
