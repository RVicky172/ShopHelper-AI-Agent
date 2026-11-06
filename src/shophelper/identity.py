"""Who a tool call is acting for, kept out of the model's reach.

The graph sets this from its config just before running a tool. It lives in a ContextVar, so
concurrent requests can't see each other's value, and it never appears in a prompt, a message or
a tool's arguments. The model has nothing it could edit.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_acting_user: ContextVar[int | None] = ContextVar("acting_user", default=None)


def current_user() -> int | None:
    return _acting_user.get()


@contextmanager
def acting_as(user_id: int | None) -> Iterator[None]:
    token = _acting_user.set(user_id)
    try:
        yield
    finally:
        _acting_user.reset(token)
