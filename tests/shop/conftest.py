import pytest
from fastapi.testclient import TestClient

from shophelper.accounts import auth
from shophelper.api import app as api
from shophelper.core.config import get_settings
from shophelper.shop import cart, catalog
from shophelper.shop.orders import demo_email, get_order_repo


@pytest.fixture(autouse=True)
def accounts_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_enabled", True)
    caches = (auth.get_user_store, get_order_repo, catalog.get_product_repo, cart.get_cart_store)
    for cache in caches:
        cache.cache_clear()
    yield
    for cache in caches:
        cache.cache_clear()


@pytest.fixture
def guest():
    """No cookie: the catalogue has to work for someone who never signed in."""
    return TestClient(api.app)


@pytest.fixture
def sign_in(monkeypatch):
    """Returns a client signed in as a demo user, with a real session and no slow password hashing."""
    monkeypatch.setattr(get_settings(), "seed_demo_users", True)
    store = auth.get_user_store()
    owners = auth.seed_demo_users(store)
    get_order_repo().assign_owners(owners)

    def client_for(email_name: str) -> TestClient:
        user = store.get_by_email(demo_email(email_name))
        return TestClient(api.app, cookies={auth.COOKIE_NAME: auth.start_session(store, user.user_id)})

    return client_for


@pytest.fixture
def asha(sign_in):
    return sign_in("Asha")


@pytest.fixture
def ravi(sign_in):
    return sign_in("Ravi")
