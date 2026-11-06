"""The shop's HTTP routes. Every route returns 404 unless accounts are enabled, so AWS has no shop.

Catalogue reads are public: see `is_public` in auth_api.py.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from shophelper.api.auth_routes import accounts_only, current_principal, require_role
from shophelper.api.schemas import CartMerge, CartQuantity
from shophelper.core.identity import Principal
from shophelper.shop.cart import cart_view, get_cart_store
from shophelper.shop.catalog import PAGE_SIZE, Sort, get_product_repo
from shophelper.shop.orders import get_order_repo

router = APIRouter(dependencies=[Depends(accounts_only)])
Shopper = Annotated[Principal, Depends(current_principal)]


@router.get("/categories")
def list_categories() -> list[dict[str, Any]]:
    return get_product_repo().categories()


@router.get("/products")
def list_products(
    category: str | None = None,
    sort: Sort = "rating",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=PAGE_SIZE)] = PAGE_SIZE,
    ids: Annotated[list[int] | None, Query(max_length=100)] = None,
) -> dict[str, Any]:
    repo = get_product_repo()
    if ids is not None:  # a guest's cart stores ids only, so its page reads the products here
        found = repo.by_ids(ids)
        return {"items": [found[i] for i in sorted(found)], "total": len(found)}
    if category is not None and category not in {c["slug"] for c in repo.categories()}:
        raise HTTPException(status_code=404, detail="No such category")
    return repo.page(category, sort, offset, limit)


@router.get("/products/{slug}")
def get_product(slug: str) -> dict[str, Any]:
    repo = get_product_repo()
    product = repo.get(slug)
    if product is None:
        raise HTTPException(status_code=404, detail="No such product")
    return {**product, "related": repo.related(product)}


# The user always comes from the session, and no route below takes a user id.

@router.get("/cart")
def get_cart(shopper: Shopper) -> dict[str, Any]:
    return cart_view(shopper.user_id)


@router.put("/cart/{product_id}")
def set_cart_item(product_id: int, body: CartQuantity, shopper: Shopper) -> dict[str, Any]:
    if not get_product_repo().by_ids([product_id]):
        raise HTTPException(status_code=404, detail="No such product")
    get_cart_store().set_quantity(shopper.user_id, product_id, body.quantity)
    return cart_view(shopper.user_id)


@router.post("/cart/merge")
def merge_cart(body: CartMerge, shopper: Shopper) -> dict[str, Any]:
    incoming = [(item.product_id, item.quantity) for item in body.items]
    products = get_product_repo().by_ids([product_id for product_id, _ in incoming])
    names = {product_id: product["name"] for product_id, product in products.items()}
    changes = get_cart_store().merge(shopper.user_id, incoming, names)
    return {"cart": cart_view(shopper.user_id), "changes": changes}


@router.post("/checkout", status_code=201)
def checkout(shopper: Shopper) -> dict[str, Any]:
    """Takes no body: the cart and the catalogue decide everything, so a sent price has nowhere to go."""
    order = get_cart_store().checkout(shopper.user_id, shopper.display_name)
    if order is None:
        raise HTTPException(status_code=409, detail="Your cart is empty")
    return order


@router.post("/orders/{order_id}/deliver", dependencies=[Depends(require_role("support", "admin"))])
def mark_delivered(order_id: str) -> dict[str, Any]:
    """Exists so a learner can buy something, deliver it and refund it, end to end."""
    repo = get_order_repo()
    if repo.get(order_id) is None:
        raise HTTPException(status_code=404, detail="No such order")
    order = repo.mark_delivered(order_id)
    if order is None:
        raise HTTPException(status_code=409, detail="Only processing or shipped orders can be delivered")
    return order
