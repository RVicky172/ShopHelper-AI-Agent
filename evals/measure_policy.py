"""Rates that one eval case can't show. Needs `docker compose up` and LM Studio.

    uv run python evals/measure_policy.py care [--rounds 3]
    uv run python evals/measure_policy.py refunds
    uv run python evals/measure_policy.py starters

Every question is followed by an unrelated one, because LM Studio's prompt cache makes repeated
prompts repeat their result. A count here is only a first pass: read the answers it prints.
"""

import argparse
import asyncio
import json
import os
import random
import re
import uuid
from datetime import UTC, datetime, timedelta

# The same local settings as scripts/evals_local.sh, set before shophelper reads them.
for key, value in {
    "SHOPHELPER_ENV_FILE": "",
    "LLM_PROVIDER": "openai_compatible",
    "DATABASE_URL": "postgresql://shophelper:shophelper@127.0.0.1:5432/shophelper",
    "TOOLS_TRANSPORT": "mcp",
    "MCP_URL": "http://127.0.0.1:8765/mcp",
    "INTERNAL_TOKEN_SECRET": "local-development-only-not-a-real-secret-0123456789",
    "LOCAL_GUARDRAILS": "true",
    "LANGSMITH_TRACING": "false",
}.items():
    os.environ.setdefault(key, value)

import psycopg  # noqa: E402

from shophelper import auth  # noqa: E402
from shophelper.mcp_client import mcp_tools  # noqa: E402
from shophelper.orders import demo_email  # noqa: E402
from shophelper.refunds import get_refund_store  # noqa: E402
from shophelper.service import ShopHelperService  # noqa: E402

FILLER = [
    "What payment methods do you accept?",
    "How do I cancel an order?",
    "What's your privacy policy?",
    "Do you price match?",
    "Do you ship internationally?",
    "Is there a restocking fee on opened headphones?",
]

# "no": a lifestyle product, so Care isn't available. "yes": electronics, or Care itself. "price": $19.99.
D016_WORDINGS = [
    ("no", "Can I buy ShopHelper Care for my yoga mat?"),
    ("yes", "Can I buy ShopHelper Care for my headphones?"),
    ("no", "Does ShopHelper Care cover a kettle?"),
    ("price", "How much is ShopHelper Care for a laptop stand?"),
    ("no", "I'd like to extend the warranty on my suitcase with ShopHelper Care."),
    ("yes", "Is ShopHelper Care available for a phone charger?"),
    ("no", "Is my backpack eligible for ShopHelper Care?"),
    ("yes", "What is ShopHelper Care?"),
]
# Written before the fix existed and never changed to suit it (030 AC-2).
NEW_WORDINGS = [
    ("no", "Can ShopHelper Care be added to a cast iron kettlebell?"),
    ("yes", "I just bought a mechanical keyboard. Should I get ShopHelper Care?"),
    ("no", "Is there a protection plan for my French press?"),
    ("yes", "Do you sell a protection plan for noise-cancelling headphones?"),
    ("no", "Can I get extended coverage on a canvas backpack?"),
    ("yes", "How do I get extended coverage on a portable charger?"),
    ("no", "will shophelper care cover my mug?"),
    ("price", "what does shophelper care cost for a desk mat"),
]
REFUSED = re.compile(
    r"electronics only|only for electronics|only available for electronics|only applies to electronics|"
    r"only covers electronics|not available|isn't available|not eligible|isn't eligible|not offered|"
    r"can't be|cannot be|does not cover|doesn't cover|does not apply|doesn't apply|not covered|no additional",
    re.IGNORECASE,
)
TWO_YEARS = re.compile(r"2[- ]years?|two[- ]years?", re.IGNORECASE)

REFUND_WORDINGS = [
    "I'd like a refund for order {o}, it stopped working.",
    "Please refund order {o}, it arrived damaged.",
    "Can I get my money back for order {o}? It's faulty.",
    "My order {o} is faulty, please refund it.",
    "Refund order {o} please, it doesn't work.",
    "I want to return order {o} and get a refund, it's defective.",
    "It stopped working after a week. Refund order {o}.",
    "Need a refund on {o}, it's not what I ordered.",
]
# A refund that mentions a warranty often fails: a known bug, D-023, so it's kept out of this rate.
TEMP_ORDER = "9001"  # a delivered lifestyle order, removed afterwards

ELECTRONICS = {"audio", "keyboards and mice", "laptop accessories", "phone accessories", "power and charging"}
ASKS_FOR_ORDER = re.compile(r"(provide|share|give|what is|need).{0,30}order (number|id)", re.IGNORECASE)
GENERAL_STARTERS = [
    ("What are your shipping options and delivery times?", r"day"),
    ("What is your return policy?", r"30"),
    ("How long do refunds take?", r"day"),
    ("What is your cancellation policy?", r"cancel"),
    ("Where is order 1001?", r"deliver"),
]


def principal(name: str):
    return auth.to_principal(auth.get_user_store().get_by_email(demo_email(name)))


def plain(text: str) -> str:
    return text.replace("’", "'")


def care_is_right(kind: str, answer: str) -> bool:
    if kind == "no":
        return bool(REFUSED.search(answer))
    if kind == "price":
        return "19.99" in answer
    return bool(TWO_YEARS.search(answer))


async def measure_care(rounds: int) -> None:
    who = principal("Asha")
    async with mcp_tools() as tools:
        svc = ShopHelperService(tools=tools)
        for label, wordings in (("D-016", D016_WORDINGS), ("new", NEW_WORDINGS)):
            searched = right = total = 0
            for r in range(rounds):
                for i, (kind, question) in enumerate(wordings):
                    resp = await svc.chat(uuid.uuid4().hex, question, who)
                    answer = plain(resp.answer)
                    did_search = "search_policy" in resp.tools_used
                    is_right = care_is_right(kind, answer)
                    total += 1
                    searched += did_search
                    right += is_right
                    print(f"[{label} r{r + 1}] search={did_search} check={is_right} kind={kind}")
                    print(f"  Q: {question}\n  A: {answer}\n")
                    await svc.chat(uuid.uuid4().hex, FILLER[(i + r) % len(FILLER)], who)
            print(f"RESULT {label}: searched {searched}, keyword check {right}, of {total}\n", flush=True)


async def measure_refunds() -> None:
    url = os.environ["DATABASE_URL"]
    today = datetime.now(UTC).date()
    with psycopg.connect(url, autocommit=True) as conn:
        owner = conn.execute("select owner_id from orders where order_id = '1001'").fetchone()[0]
        data = {
            "item": "French Press", "total": 34.0, "status": "delivered", "customer": "Asha",
            "order_id": TEMP_ORDER,
            "ordered_at": str(today - timedelta(days=8)), "delivered_at": str(today - timedelta(days=4)),
        }
        conn.execute(
            "insert into orders (order_id, data, owner_id) values (%s, %s, %s)",
            (TEMP_ORDER, json.dumps(data), owner),
        )
    orders = [("Asha", "1001"), ("Kabir", "1006"), ("Asha", TEMP_ORDER)]
    refunds = get_refund_store()
    submitted = mentions_warranty = 0
    failures = []
    try:
        async with mcp_tools() as tools:
            svc = ShopHelperService(tools=tools)
            for n in range(60):
                name, order = orders[n % len(orders)]
                question = REFUND_WORDINGS[n % len(REFUND_WORDINGS)].format(o=order)
                who = principal(name)
                session = f"measure-{uuid.uuid4().hex}"
                resp = await svc.chat(session, question, who)
                request = refunds.open_for_session(session)  # the database decides, not the reply
                mentions_warranty += "warranty" in question
                if request and str(request.order_id) == order:
                    submitted += 1
                else:
                    failures.append((question, resp.status, resp.tools_used, plain(resp.answer)))
                refunds.cancel_open()
                await svc.chat(uuid.uuid4().hex, FILLER[n % len(FILLER)], who)
                if (n + 1) % 15 == 0:
                    print(n + 1, "attempts,", submitted, "submitted", flush=True)
    finally:
        refunds.cancel_open()
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute("delete from refund_requests where order_id = %s", (TEMP_ORDER,))
            conn.execute("delete from orders where order_id = %s", (TEMP_ORDER,))
    print(f"RESULT {submitted} of 60 submitted, {mentions_warranty} attempts mentioned a warranty")
    for failure in failures:
        print(failure)


async def measure_starters() -> None:
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute("select name, category from products order by id").fetchall()
    per_category: dict[str, list[str]] = {}
    for name, slug in rows:
        names = per_category.setdefault(slug.replace("-", " "), [])
        if len(names) < 2:
            names.append(name)
    cases = []
    for category, names in per_category.items():
        electronics = category in ELECTRONICS
        for name in names:
            cases.append((
                f"What's the warranty on the {name} ({category})?",
                r"1-year|1 year|one year|one-year" if electronics else r"\b90\b",
                r"\b90\b" if electronics else r"1-year|1 year|one year",
            ))
            cases.append((f"How do returns work for the {name} ({category})?", r"30", None))
    cases += [(question, want, None) for question, want in GENERAL_STARTERS] * 5
    random.Random(21).shuffle(cases)  # a different question after each one, as with FILLER
    who = principal("Asha")
    passed = 0
    flagged = []
    async with mcp_tools() as tools:
        svc = ShopHelperService(tools=tools)
        for question, want, forbidden in cases:
            resp = await svc.chat(uuid.uuid4().hex, question, who)
            answer = plain(resp.answer)
            good = (
                bool(resp.tools_used)
                and re.search(want, answer, re.IGNORECASE)
                and not (forbidden and re.search(forbidden, answer, re.IGNORECASE))
                and not ASKS_FOR_ORDER.search(answer)
            )
            if good:
                passed += 1
            else:
                flagged.append((question, resp.tools_used, answer))
    print(f"RESULT {passed} of {len(cases)} by the strict check; read any below in full")
    for item in flagged:
        print(item)


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure rates that one eval case can't show.")
    parser.add_argument("what", choices=["care", "refunds", "starters"])
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    if args.what == "care":
        asyncio.run(measure_care(args.rounds))
    elif args.what == "refunds":
        asyncio.run(measure_refunds())
    else:
        asyncio.run(measure_starters())


if __name__ == "__main__":
    main()
