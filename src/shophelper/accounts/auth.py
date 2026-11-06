"""Accounts: who is using the app. Used only when Settings.accounts_enabled is true.

Authentication answers "who are you?" (this file). Authorization answers "what may you do?"
(auth_api.py and each route). Walkthrough: docs/learn/11-accounts-and-isolation.md

Functions that depend on time take `now`, so tests can move the clock instead of sleeping.
"""

import hashlib
import re
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Protocol, cast

from shophelper.core import db
from shophelper.core.config import get_settings
from shophelper.core.identity import Principal, Role
from shophelper.shop.orders import account_order_repo, demo_email, load_seed_orders

COOKIE_NAME = "shophelper_session"
SESSION_LIFETIME = timedelta(hours=24)
LOCK_WINDOW = timedelta(minutes=15)
MAX_FAILURES = 5
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128  # hashing is deliberately slow, so very long input is refused first
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Shown on the login page, so it protects nothing. Only ever seeded on the local stack.
DEMO_PASSWORD = "shophelper-demo"
INTERNAL_TOKEN_LIFETIME = timedelta(seconds=60)
INTERNAL_AUDIENCE = "shophelper-mcp"


class InvalidCredentials(Exception):
    """Wrong password and unknown email raise this same error, so neither can be told apart."""


class LockedOut(Exception):
    pass


class EmailTaken(Exception):
    pass


class InvalidSignup(Exception):
    pass


class LastAdmin(Exception):
    pass


class NoSigningKey(Exception):
    pass


class SeedingRefused(Exception):
    """Demo accounts have a published password, so they must never reach a real deployment."""


@dataclass(frozen=True)
class User:
    user_id: int
    email: str
    role: Role
    display_name: str
    password_hash: str


@dataclass(frozen=True)
class Session:
    user_id: int
    expires_at: datetime


class UserStore(Protocol):
    def create_user(self, email: str, password_hash: str, role: Role, display_name: str) -> User: ...
    def get_by_email(self, email: str) -> User | None: ...
    def get_by_id(self, user_id: int) -> User | None: ...
    def list_users(self) -> list[User]: ...
    def set_role(self, user_id: int, role: Role) -> User | None: ...
    def add_session(self, token_hash: str, user_id: int, expires_at: datetime) -> None: ...
    def get_session(self, token_hash: str) -> Session | None: ...
    def delete_session(self, token_hash: str) -> None: ...
    def record_failure(self, email: str, at: datetime) -> None: ...
    def count_failures(self, email: str, since: datetime) -> int: ...
    def clear_failures(self, email: str) -> None: ...


class InMemoryUserStore:
    def __init__(self) -> None:
        self._users: dict[int, User] = {}
        self._sessions: dict[str, Session] = {}
        self._failures: dict[str, list[datetime]] = {}

    def create_user(self, email: str, password_hash: str, role: Role, display_name: str) -> User:
        if self.get_by_email(email):
            raise EmailTaken(email)
        user = User(len(self._users) + 1, email, role, display_name, password_hash)
        self._users[user.user_id] = user
        return user

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def list_users(self) -> list[User]:
        return list(self._users.values())

    def set_role(self, user_id: int, role: Role) -> User | None:
        user = self._users.get(user_id)
        if not user:
            return None
        admins = [u for u in self._users.values() if u.role == "admin"]
        if user.role == "admin" and role != "admin" and len(admins) == 1:
            raise LastAdmin(user.email)
        self._users[user_id] = replace(user, role=role)
        return self._users[user_id]

    def add_session(self, token_hash: str, user_id: int, expires_at: datetime) -> None:
        self._sessions[token_hash] = Session(user_id, expires_at)

    def get_session(self, token_hash: str) -> Session | None:
        return self._sessions.get(token_hash)

    def delete_session(self, token_hash: str) -> None:
        self._sessions.pop(token_hash, None)

    def record_failure(self, email: str, at: datetime) -> None:
        self._failures.setdefault(email, []).append(at)

    def count_failures(self, email: str, since: datetime) -> int:
        return sum(at > since for at in self._failures.get(email, []))

    def clear_failures(self, email: str) -> None:
        self._failures.pop(email, None)


class PostgresUserStore:
    """Same contract as InMemoryUserStore."""

    COLUMNS = "id, email, role, display_name, password_hash"

    @staticmethod
    def _user(row: dict | None) -> User | None:
        if not row:
            return None
        return User(row["id"], row["email"], row["role"], row["display_name"], row["password_hash"])

    def create_user(self, email: str, password_hash: str, role: Role, display_name: str) -> User:
        from psycopg.errors import UniqueViolation

        try:
            with db.connect() as conn:
                row = conn.execute(
                    "INSERT INTO users (email, password_hash, role, display_name) "
                    f"VALUES (%s, %s, %s, %s) RETURNING {self.COLUMNS}",
                    (email, password_hash, role, display_name),
                ).fetchone()
        except UniqueViolation as exc:
            raise EmailTaken(email) from exc
        return cast(User, self._user(row))  # the insert returned a row

    def get_by_email(self, email: str) -> User | None:
        with db.connect() as conn:
            sql = f"SELECT {self.COLUMNS} FROM users WHERE email = %s"
            return self._user(conn.execute(sql, (email,)).fetchone())

    def get_by_id(self, user_id: int) -> User | None:
        with db.connect() as conn:
            sql = f"SELECT {self.COLUMNS} FROM users WHERE id = %s"
            return self._user(conn.execute(sql, (user_id,)).fetchone())

    def list_users(self) -> list[User]:
        with db.connect() as conn:
            rows = conn.execute(f"SELECT {self.COLUMNS} FROM users ORDER BY id").fetchall()
        return cast(list[User], [self._user(r) for r in rows])

    def set_role(self, user_id: int, role: Role) -> User | None:
        with db.connect() as conn:  # one transaction: an exception rolls it back
            current = conn.execute("SELECT role FROM users WHERE id = %s", (user_id,)).fetchone()
            if not current:
                return None
            if current["role"] == "admin" and role != "admin":
                # FOR UPDATE stops two admins demoting each other at the same moment.
                admins = conn.execute("SELECT id FROM users WHERE role = 'admin' FOR UPDATE").fetchall()
                if len(admins) == 1:
                    raise LastAdmin(user_id)
            row = conn.execute(
                f"UPDATE users SET role = %s WHERE id = %s RETURNING {self.COLUMNS}", (role, user_id)
            ).fetchone()
        return self._user(row)

    def add_session(self, token_hash: str, user_id: int, expires_at: datetime) -> None:
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO auth_sessions (token_hash, user_id, expires_at) VALUES (%s, %s, %s)",
                (token_hash, user_id, expires_at),
            )

    def get_session(self, token_hash: str) -> Session | None:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT user_id, expires_at FROM auth_sessions WHERE token_hash = %s", (token_hash,)
            ).fetchone()
        return Session(row["user_id"], row["expires_at"]) if row else None

    def delete_session(self, token_hash: str) -> None:
        with db.connect() as conn:
            conn.execute("DELETE FROM auth_sessions WHERE token_hash = %s", (token_hash,))

    def record_failure(self, email: str, at: datetime) -> None:
        with db.connect() as conn:
            conn.execute("INSERT INTO login_attempts (email, attempted_at) VALUES (%s, %s)", (email, at))

    def count_failures(self, email: str, since: datetime) -> int:
        with db.connect() as conn:
            # count(*) always returns a row
            return conn.execute(  # pyright: ignore[reportOptionalSubscript]
                "SELECT count(*) AS n FROM login_attempts WHERE email = %s AND attempted_at > %s",
                (email, since),
            ).fetchone()["n"]

    def clear_failures(self, email: str) -> None:
        with db.connect() as conn:
            conn.execute("DELETE FROM login_attempts WHERE email = %s", (email,))


@lru_cache
def get_user_store() -> UserStore:
    return PostgresUserStore() if get_settings().database_url else InMemoryUserStore()


@lru_cache
def _hasher():
    from argon2 import PasswordHasher  # imported here so AWS runtimes never load it

    return PasswordHasher()


@lru_cache
def _decoy_hash() -> str:
    return _hasher().hash(secrets.token_hex(16))


def _password_matches(password_hash: str, password: str) -> bool:
    from argon2.exceptions import InvalidHashError, VerificationError

    try:
        return _hasher().verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def _utcnow() -> datetime:
    return datetime.now(UTC)


def normalise_email(email: str) -> str:
    return email.strip().lower()


def hash_token(token: str) -> str:
    """Tokens are long and random, so a fast hash is enough. A stolen table can't be replayed."""
    return hashlib.sha256(token.encode()).hexdigest()


def to_principal(user: User) -> Principal:
    return Principal(user.user_id, user.email, user.role, user.display_name)


def signup(
    store: UserStore, email: str, password: str, display_name: str = "", now: datetime | None = None
) -> Principal:
    """Everyone who signs up is a customer. No input can choose another level."""
    email = normalise_email(email)
    if len(email) > 254 or not EMAIL_PATTERN.match(email):
        raise InvalidSignup("Enter a valid email address.")
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise InvalidSignup(
            f"Use a password of {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters."
        )
    name = display_name.strip() or email.split("@")[0]
    user = store.create_user(email, _hasher().hash(password), "customer", name)
    account_order_repo().create_sample_orders(user.user_id, name)
    return to_principal(user)


def start_session(store: UserStore, user_id: int, now: datetime | None = None) -> str:
    token = secrets.token_urlsafe(32)
    store.add_session(hash_token(token), user_id, (now or _utcnow()) + SESSION_LIFETIME)
    return token


def login(
    store: UserStore, email: str, password: str, now: datetime | None = None
) -> tuple[Principal, str]:
    now = now or _utcnow()
    email = normalise_email(email)
    if store.count_failures(email, since=now - LOCK_WINDOW) >= MAX_FAILURES:
        raise LockedOut(email)

    user = store.get_by_email(email)
    # An unknown email still costs one hash check, so response time doesn't reveal who has an account.
    matches = _password_matches(user.password_hash if user else _decoy_hash(), password)
    if not (user and matches):
        store.record_failure(email, now)
        raise InvalidCredentials

    store.clear_failures(email)
    return to_principal(user), start_session(store, user.user_id, now)


def resolve_session(store: UserStore, token: str, now: datetime | None = None) -> Principal | None:
    """The user's level is read fresh each time, so a change applies on their next request."""
    token_hash = hash_token(token)
    session = store.get_session(token_hash)
    if not session:
        return None
    if (now or _utcnow()) >= session.expires_at:
        store.delete_session(token_hash)
        return None
    user = store.get_by_id(session.user_id)
    return to_principal(user) if user else None


def logout(store: UserStore, token: str) -> None:
    store.delete_session(hash_token(token))


def issue_internal_token(user_id: int, now: datetime | None = None) -> str:
    """Proof, from the API to the MCP server, of who a tool call is for.

    A JWT suits this job and not browser sessions: it lives for 60 seconds, so it never needs
    revoking, and the MCP server can check it with no database lookup.
    """
    import jwt

    secret = get_settings().internal_token_secret
    if not secret:
        raise NoSigningKey
    now = now or _utcnow()
    claims = {
        "sub": str(user_id), "aud": INTERNAL_AUDIENCE, "iat": now,
        "exp": now + INTERNAL_TOKEN_LIFETIME,
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def verify_internal_token(token: str) -> int | None:
    import jwt

    secret = get_settings().internal_token_secret
    if not secret or not token:
        return None
    try:
        # Naming the algorithm matters: otherwise a token could declare itself unsigned.
        claims = jwt.decode(token, secret, algorithms=["HS256"], audience=INTERNAL_AUDIENCE)
        return int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None


def demo_accounts() -> list[dict[str, str]]:
    customers = sorted({order["customer"] for order in load_seed_orders().values()})
    accounts = [
        {"email": demo_email(name), "role": "customer", "display_name": name, "password": DEMO_PASSWORD}
        for name in customers
    ]
    for role, name in (("support", "Support"), ("admin", "Admin")):
        accounts.append(
            {"email": demo_email(name), "role": role, "display_name": name, "password": DEMO_PASSWORD}
        )
    return accounts


def seed_demo_users(store: UserStore) -> dict[str, int]:
    """Creates any missing demo account and returns {display name: user id}. Existing accounts are
    left alone, so a level changed during testing survives a restart."""
    if not get_settings().seed_demo_users:
        raise SeedingRefused
    owners = {}
    for account in demo_accounts():
        user = store.get_by_email(account["email"]) or store.create_user(
            account["email"],
            _hasher().hash(DEMO_PASSWORD),
            cast(Role, account["role"]),
            account["display_name"],
        )
        if account["role"] == "customer":
            owners[account["display_name"]] = user.user_id
    return owners
