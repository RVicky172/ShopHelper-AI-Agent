"""The product catalogue. Prices live here and nowhere else.

Two interchangeable stores: an in-memory one read from data/products.json (for tests), and a
Postgres one that `setup` fills from the same file, so the products can be seen in pgAdmin.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol

from shophelper.core import db
from shophelper.core.config import get_settings

SEED_FILE = Path(__file__).parents[1] / "data" / "products.json"
PAGE_SIZE = 12
RELATED_LIMIT = 4

Sort = Literal["price_asc", "price_desc", "rating", "newest"]

# The request picks a key from this list and never reaches the SQL itself. Each order ends in `id`,
# so equal values always sort the same way, and paging can't repeat or lose a product.
SQL_ORDER: dict[Sort, str] = {
    "price_asc": "price ASC, id",
    "price_desc": "price DESC, id",
    "rating": "rating DESC, rating_count DESC, id",
    "newest": "added_at DESC, id",
}
SORT_KEYS = {
    "price_asc": lambda p: (p["price"], p["id"]),
    "price_desc": lambda p: (-p["price"], p["id"]),
    "rating": lambda p: (-p["rating"], -p["rating_count"], p["id"]),
    "newest": lambda p: (-int(p["added_at"].replace("-", "")), p["id"]),
}


def load_catalogue() -> dict[str, Any]:
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))


class ProductRepo(Protocol):
    def categories(self) -> list[dict[str, Any]]: ...
    def page(self, category: str | None, sort: Sort, offset: int, limit: int) -> dict[str, Any]: ...
    def get(self, slug: str) -> dict[str, Any] | None: ...
    def by_ids(self, ids: list[int]) -> dict[int, dict[str, Any]]: ...
    def related(self, product: dict[str, Any]) -> list[dict[str, Any]]: ...
    def seed(self) -> int: ...


class InMemoryProductRepo:
    def __init__(self) -> None:
        catalogue = load_catalogue()
        self._categories = catalogue["categories"]
        self._products = catalogue["products"]

    def categories(self) -> list[dict[str, Any]]:
        result = []
        for category in self._categories:
            mine = [p for p in self._products if p["category"] == category["slug"]]
            best = min(mine, key=SORT_KEYS["rating"])
            cover = {"slug": best["slug"], "name": best["name"]}
            result.append({**category, "count": len(mine), "cover": cover})
        return result

    def page(self, category: str | None, sort: Sort, offset: int, limit: int) -> dict[str, Any]:
        chosen = [p for p in self._products if category in (None, p["category"])]
        chosen.sort(key=SORT_KEYS[sort])
        return {"items": chosen[offset:offset + limit], "total": len(chosen)}

    def get(self, slug: str) -> dict[str, Any] | None:
        return next((p for p in self._products if p["slug"] == slug), None)

    def by_ids(self, ids: list[int]) -> dict[int, dict[str, Any]]:
        return {p["id"]: p for p in self._products if p["id"] in ids}

    def related(self, product: dict[str, Any]) -> list[dict[str, Any]]:
        same = [p for p in self._products if p["category"] == product["category"]]
        others = [p for p in same if p["id"] != product["id"]]
        return sorted(others, key=SORT_KEYS["rating"])[:RELATED_LIMIT]

    def seed(self) -> int:
        return len(self._products)


def _product(row: dict[str, Any]) -> dict[str, Any]:
    """NUMERIC and DATE columns as the same plain values the JSON file holds."""
    return {
        **row, "price": float(row["price"]), "rating": float(row["rating"]),
        "added_at": row["added_at"].isoformat(),
    }


class PostgresProductRepo:
    def categories(self) -> list[dict[str, Any]]:
        with db.connect() as conn:
            rows = conn.execute(f"""
                SELECT DISTINCT ON (category) category, slug, name, count(*) OVER (PARTITION BY category) AS n
                FROM products
                ORDER BY category, {SQL_ORDER["rating"]}
            """).fetchall()
        found = {r["category"]: r for r in rows}
        return [
            {**c, "count": found[c["slug"]]["n"], "cover": {k: found[c["slug"]][k] for k in ("slug", "name")}}
            for c in load_catalogue()["categories"]
            if c["slug"] in found
        ]

    def page(self, category: str | None, sort: Sort, offset: int, limit: int) -> dict[str, Any]:
        where = "WHERE %(category)s::text IS NULL OR category = %(category)s"
        args = {"category": category, "offset": offset, "limit": limit}
        with db.connect() as conn:
            total = conn.execute(f"SELECT count(*) AS n FROM products {where}", args).fetchone()["n"]
            rows = conn.execute(
                f"""
                SELECT * FROM products {where}
                ORDER BY {SQL_ORDER[sort]} OFFSET %(offset)s LIMIT %(limit)s
                """,
                args,
            ).fetchall()
        return {"items": [_product(r) for r in rows], "total": total}

    def get(self, slug: str) -> dict[str, Any] | None:
        with db.connect() as conn:
            row = conn.execute("SELECT * FROM products WHERE slug = %s", (slug,)).fetchone()
        return _product(row) if row else None

    def by_ids(self, ids: list[int]) -> dict[int, dict[str, Any]]:
        with db.connect() as conn:
            rows = conn.execute("SELECT * FROM products WHERE id = ANY(%s)", (ids,)).fetchall()
        return {r["id"]: _product(r) for r in rows}

    def related(self, product: dict[str, Any]) -> list[dict[str, Any]]:
        with db.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM products WHERE category = %s AND id <> %s
                ORDER BY {SQL_ORDER["rating"]} LIMIT %s
                """,
                (product["category"], product["id"], RELATED_LIMIT),
            ).fetchall()
        return [_product(r) for r in rows]

    def seed(self) -> int:
        """Upserts by id, so editing the file and re-running `setup` updates rows in place."""
        products = load_catalogue()["products"]
        with db.connect() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO products
                        (id, slug, category, name, price, description, specs, rating, rating_count, added_at)
                    VALUES (%(id)s, %(slug)s, %(category)s, %(name)s, %(price)s, %(description)s, %(specs)s,
                            %(rating)s, %(rating_count)s, %(added_at)s)
                    ON CONFLICT (id) DO UPDATE SET
                        slug = EXCLUDED.slug, category = EXCLUDED.category, name = EXCLUDED.name,
                        price = EXCLUDED.price, description = EXCLUDED.description, specs = EXCLUDED.specs,
                        rating = EXCLUDED.rating, rating_count = EXCLUDED.rating_count,
                        added_at = EXCLUDED.added_at
                    """,
                    [{**p, "specs": db.Jsonb(p["specs"])} for p in products],
                )
        return len(products)


@lru_cache
def get_product_repo() -> ProductRepo:
    return PostgresProductRepo() if get_settings().database_url else InMemoryProductRepo()
