---
title: Project setup and folder structure
checked: 2026-11-06
---

## What you'll learn

- Why to group code by feature, not by type
- How one-way imports keep a project manageable
- How a test can stop the structure decaying
- Which tools a modern Python and React project uses

## The simple explanation

A small project works in any layout. The trouble starts around the 30th file, when nobody remembers where anything goes.

There are two common ways to organise code:

| Style | Folders | A change to refunds touches |
| --- | --- | --- |
| **By type** | `models/`, `services/`, `routes/` | Three folders |
| **By feature** | `shop/`, `accounts/`, `agent/` | Mostly one |

Think of a supermarket. It doesn't keep every tin in one aisle and every box in another. Things that are used together sit together, and you can find them by what they're for.

The second idea is **direction**. Think of a building. Upper floors rest on lower ones, and never the other way round, so you can redecorate the top floor without touching the foundations. In code, that means imports point one way. Low-level code knows nothing about what's built on it.

A rule only lasts if something enforces it. Written guidelines fade, so the rule belongs in a test that fails.

## An example

Say the shop gets a new rule: refunds over $500 need two reviewers. Where does the code go?

The route that receives the request is in `api/`. But ask what the code is *about*, not what kind of code it is. It's a shop rule, so it goes in `shop/refunds.py`, next to the existing rule. The route just calls it.

That one habit pays off three ways:

- The rule can be tested with no web server.
- The agent and the staff page can both use it.
- A new teammate looks for refund rules in one obvious place.

This project learned that the hard way. It started as 27 Python files in one folder, and feature 031 regrouped them, with no change in behaviour. The new layout came with a test, so it can't slide back.

## How ShopHelper does it

```text
src/shophelper/
  core/        Settings, database access, logging, identity
  shop/        Catalogue, cart, orders, refunds
  accounts/    Users, sessions, conversations
  rag/         Chunking, embedding, search
  agent/       The agent loop, tools, memory, guardrails
  mcp/         The MCP server and client
  api/         HTTP routes and request models
web/src/
  features/    auth, cart, chat, how-it-works, learn, shop, staff
  shared/      API client and page layout
tests/         Mirrors src/shophelper/
evals/         Tests against the real model
```

The rule is a table in a test. Each folder lists what it may import:

```python file=tests/test_architecture.py
ALLOWED = {
"core": set(),
"shop": {"core"},
"accounts": {"core", "shop"},
"rag": {"core"},
"agent": {"core", "shop", "accounts", "rag"},
"mcp": {"core", "shop", "accounts", "agent"},
"api": {"core", "shop", "accounts", "rag", "agent", "mcp"},
}
```

The test reads every file's imports, including ones inside functions. So if `core` ever imports `agent`, the build fails. The same file checks that paths named in the docs still exist.

**The tooling:**

| Job | Tool | Why |
| --- | --- | --- |
| Python packages | uv | One lock file, and it's fast |
| Lint and format, Python | ruff | One tool instead of several |
| Types, Python | pyright | Catches mistakes before running |
| Lint and format, web | Biome | One tool, and fast |
| Before each commit | pre-commit | Runs lint on what you changed |
| The gate | `scripts/check.sh` | One command runs all of it |

`scripts/check.sh` is the important one. A new person needs one command, CI runs the same checks, and nobody has to remember a list.

**Settings** live in one place, read from the environment, and every new setting keeps AWS as the default. **`CONTRIBUTING.md`** says where new code goes, because a good structure that nobody can find doesn't help.

**Docker Compose** starts the database, API, MCP server, web server and pgAdmin with one command. So "it works on my machine" means the same machine for everyone.

## In the market

Checked on 2026-11-06.

| Need | Used here | Common alternatives |
| --- | --- | --- |
| Python packages | [uv](https://docs.astral.sh/uv/) | Poetry, pip with `requirements.txt` |
| Python lint | [ruff](https://docs.astral.sh/ruff/) | Flake8 with Black |
| Web lint | [Biome](https://biomejs.dev/) | ESLint with Prettier |
| Git hooks | [pre-commit](https://pre-commit.com/) | Husky |

**One service or many?** ShopHelper is mostly one application with clear folders, often called a **modular monolith**. The MCP server is the one separate service. Splitting into many services makes sense when teams need to ship separately or parts need to scale separately. Before that, it adds network calls and deployment work. Good folders give you most of the benefit, and they make a later split easier.

## Try it

1. Run `scripts/check.sh`, and read the order of the steps.
2. **Break the rule.** Add this line at the top of `src/shophelper/core/identity.py`:

```python
from shophelper.agent import schemas
```

3. Run `uv run pytest tests/test_architecture.py`. The test fails, and names the import.
4. Remove the line, and run it again.

## Interview questions

### How would you organise an AI application's codebase?

**Strong answer:** By feature, with imports pointing one way. In my project, `core` is at the bottom, then `shop`, `accounts` and `rag`, then `agent`, then `mcp` and `api`. Routes stay thin, and rules sit with their feature, so they're testable with no web server. A test reads every import and fails on a wrong direction, so the structure can't quietly decay. Tests mirror the source, and evals are separate because they need a real model.

**Follow-up:** Where does a prompt live?

### How do you keep a growing codebase manageable?

**Strong answer:** Make the rules automatic. One command runs lint, types and tests, and CI runs the same one. Architecture rules are a test, not a wiki page. There's a short contributing guide saying where new code goes. And I make changes small, with specs for features, so reviewers can follow. I restructured my own project once it passed about 27 files in one folder, with no behaviour change, and added the test in the same piece of work.

**Follow-up:** How do you restructure safely?

### Microservices or a monolith for a new AI product?

**Strong answer:** I'd start with a modular monolith. Most early teams don't need separate deployments, and each split adds network failures and operations. I'd separate something when it has a real reason: different scaling, a different team, or a security boundary. In my project the MCP server is separate because it's a real protocol boundary, and it holds the code that touches order data.

**Follow-up:** What would make you split the agent from the API?

## Check yourself

### Where does a new rule about refund limits go?

- [ ] In the API route — routes should stay thin.
- [x] In `shop/`, with the other refund rules — right: ask what it's about, not what kind of code it is.
- [ ] In `core/` — that's for shared basics.

### Why should imports point one way?

- [x] A change low down can't be broken by something above it — right: the foundations don't depend on the upper floors.
- [ ] Python requires it — Python allows it, which is the problem.
- [ ] It makes imports faster — speed isn't the reason.

### What keeps the folder rules from fading?

- [ ] A note in the README — notes get ignored.
- [ ] Careful reviewers — people miss things.
- [x] A test that fails — right: the build enforces it.
