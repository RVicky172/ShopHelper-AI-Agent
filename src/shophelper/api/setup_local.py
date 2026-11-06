"""One-shot setup for the local stack: the `setup` service in docker-compose.yml runs this.

    1. wait for LM Studio (on the host) and check the models it needs are available
    2. create the tables and the pgvector extension
    3. create the demo accounts, if SEED_DEMO_USERS is on
    4. seed the demo orders, unless orders already exist, and give them owners
    5. load the product catalogue
    6. embed the policy documents into pgvector
"""

import sys
import time

from shophelper.accounts import auth
from shophelper.core import db
from shophelper.core.config import get_settings
from shophelper.rag import pipeline as rag
from shophelper.shop.catalog import get_product_repo
from shophelper.shop.orders import account_order_repo


def wait_for_lm_studio(timeout_s: int = 60) -> None:
    s = get_settings()
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            available = {m.id for m in rag._client().models.list().data}
            break
        except Exception as exc:
            if time.monotonic() > deadline:
                sys.exit(
                    f"Can't reach LM Studio at {s.llm_base_url} ({type(exc).__name__}). "
                    "Start its server: `lms server start`, or the Developer tab in LM Studio."
                )
            print("waiting for LM Studio...", flush=True)
            time.sleep(3)
    missing = {s.local_chat_model, s.embedding_model} - available
    if missing:
        sys.exit(f"LM Studio doesn't have: {sorted(missing)}. It has: {sorted(available)}")
    print(f"LM Studio OK: chat={s.local_chat_model} embeddings={s.embedding_model}", flush=True)


def main() -> None:
    wait_for_lm_studio()
    db.apply_schema()
    print("schema OK", flush=True)

    owners = {}
    if get_settings().seed_demo_users:
        owners = auth.seed_demo_users(auth.get_user_store())
        print(f"demo accounts OK: {len(owners)} customers, plus support and admin", flush=True)

    repo = account_order_repo()
    if repo.list_all():
        print("orders already seeded", flush=True)
    else:
        repo.reset()
        print("orders seeded", flush=True)
    repo.assign_owners(owners)

    print(f"catalogue OK: {get_product_repo().seed()} products", flush=True)

    print(f"ingest: {rag.ingest()}", flush=True)


if __name__ == "__main__":
    main()
