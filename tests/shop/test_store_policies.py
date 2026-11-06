"""What the agent and the shop say about policies. Offline, using the in-memory backends."""

import re

import pytest

from shop_helpers import CATEGORIES, ROOT
from shophelper.agent import graph, raw_agent

# --- AC-38, AC-39: a general store, with terms for lifestyle products ---

def test_the_agent_isnt_told_it_only_sells_electronics():
    for prompt in (graph.SYSTEM_PROMPT, raw_agent.SYSTEM_PROMPT):
        assert "electronics store" not in prompt
        assert "home and kitchen" in prompt.lower()


def policy(name):
    return (ROOT / "knowledge/policies" / name).read_text(encoding="utf-8")


def test_returns_policy_covers_lifestyle_products():
    line = next(x for x in policy("returns.md").splitlines() if "lifestyle" in x.lower())
    assert "30 days" in line and "no restocking fee" in line


def test_the_care_line_says_what_electronics_means():
    # Chunks are retrieved alone, so a line saying only "electronics" left the model guessing:
    # it called a laptop stand and a desk mat lifestyle products.
    line = next(x for x in policy("warranty.md").splitlines() if "ShopHelper Care" in x)
    for term in ["electronics only", "laptop accessories", "laptop stands", "desk mats", "$19.99", "2 years"]:
        assert term in line


def test_warranty_policy_covers_lifestyle_products():
    line = next(x for x in policy("warranty.md").splitlines() if "lifestyle" in x.lower())
    assert "90-day" in line and "defects" in line


@pytest.mark.parametrize("name", ["returns.md", "warranty.md"])
@pytest.mark.parametrize("category", [
    "audio", "keyboards and mice", "laptop accessories", "phone accessories", "power and charging",
])
def test_each_electronics_category_is_named(name, category):
    """A phone case doesn't sound like electronics, and the agent gave it the lifestyle terms until this."""
    line = next(x for x in policy(name).splitlines() if x.startswith("- **Electronics** means"))
    assert category in line


def test_electronics_terms_havent_changed():
    assert "Opened electronics that are not defective" in policy("returns.md")
    assert "10% restocking fee" in policy("returns.md")
    assert "All electronics include a **1-year limited warranty**" in policy("warranty.md")


@pytest.mark.parametrize("name", ["returns.md", "warranty.md"])
@pytest.mark.parametrize("category", ["home and kitchen", "bags and travel", "fitness and outdoors"])
def test_each_lifestyle_category_is_named(name, category):
    assert category in policy(name).lower()


# --- AC-11: the return policy page shows what the agent reads ---

def test_the_shops_copy_of_the_return_policy_matches_the_agents():
    shown = (ROOT / "web/src/shop/returns-policy.md").read_text(encoding="utf-8")
    assert shown == policy("returns.md")


def test_every_category_has_a_colour():
    tints = (ROOT / "web/src/shop/categories.ts").read_text(encoding="utf-8")
    css = (ROOT / "web/src/index.css").read_text(encoding="utf-8")
    for category in CATEGORIES:
        name = re.search(rf"'?{category['slug']}'?: '(\w+)'", tints)
        assert name, category
        assert f"--color-tint-{name[1]}:" in css
