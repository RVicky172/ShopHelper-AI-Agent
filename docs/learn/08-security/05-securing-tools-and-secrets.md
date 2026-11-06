---
title: Securing tools and secrets
checked: 2026-11-06
---

## What you'll learn

- How to design tools a model can't misuse
- How to give each part the least access it needs
- Where secrets belong, and where they don't
- What to check in your dependencies

## The simple explanation

A tool gives a model real power, so design each one as if it'll be called by an attacker. Sometimes it will be.

Think of a hotel key card. A cleaner's card opens the rooms on one floor, during working hours. It doesn't open the safe. If it's stolen, the damage is limited. That's **least privilege**: give each thing only what its job needs.

For tools, that means:

| Rule | Instead of | Do this |
| --- | --- | --- |
| Narrow purpose | `run_sql(query)` | `get_order_status(order_id)` |
| Validate input | Trust the argument | Check its shape in code |
| Keep identity out | `user_id` as an argument | Identity from the session |
| Read by default | One tool for everything | Separate read and write |
| Limit output | The whole row | Only what's needed |
| Log it | Silent | A record of each call |

A **secret** is anything that grants access: a key, a password, a signing token. The rules are short. Keep them out of code. Keep them out of prompts. Keep them out of logs. Give them the shortest life you can.

The model should never see a secret. Anything in its context can come back out, as the [system prompt](02-prompt-injection.md) did.

## An example

Compare two ways to give an agent order data.

**The dangerous way:** a tool called `run_sql` with a query argument. It's flexible, and quick to build. But now injected text can write `SELECT * FROM users`, and the model holds a database connection.

**This project's way:**

```python file=src/shophelper/mcp/server.py
def get_order_status(order_id: str, ctx: Context) -> dict[str, Any]:
```

The model supplies one thing: an order id. The code cleans it, adds the verified user, and runs a fixed query. Whatever the model writes, the query's shape can't change.

Now apply the same thinking to credentials. The MCP server needs to know who's calling. It could accept a shared password forever. Instead, a signed token proves it, and expires quickly:

```python file=src/shophelper/accounts/auth.py
INTERNAL_TOKEN_LIFETIME = timedelta(seconds=60)
```

If that token leaks, it's useful for a minute, and only for one user.

## How ShopHelper does it

**Secrets locally.** The real ones never enter git:

```text file=.gitignore
.env
```

The one secret in `docker-compose.yml` looks alarming, and it's safe. It's fake, and it says so:

```yaml file=docker-compose.yml
INTERNAL_TOKEN_SECRET: local-development-only-not-a-real-secret-0123456789
```

**Secrets on AWS.** The LangSmith key sits in Parameter Store, as an encrypted value, and the app reads it at runtime. Deployment uses a short-lived role, so there's no long-lived AWS key in GitHub:

```yaml file=.github/workflows/ci.yml
role-to-assume: ${{ vars.AWS_ROLE_ARN }}
```

**Least privilege on AWS.** The app's role lists exact actions on exact resources, in [app_iam.tf](../../../infra/app_iam.tf). It can apply one guardrail, and read one knowledge base:

```hcl file=infra/app_iam.tf
actions   = ["bedrock:ApplyGuardrail"]
resources = [aws_bedrock_guardrail.main.guardrail_arn]
```

**Dependencies.** A tool is code you run, and so is a library. `uv.lock` pins exact versions, and `requirements.txt` has hashes, so a tampered package fails to install.

**The demo password** is on the sign-in page, so it protects nothing. That's fine for fake demo users, and it's why seeding them must never be turned on for a real deployment.

**What's missing:**

- No secret scanner runs on commits, so a key pasted by mistake wouldn't be stopped.
- There's no audit table for tool calls. Logs show them, but logs aren't an audit trail.
- No automated check for vulnerable packages.
- No key rotation process, since nothing here needs one yet.

## In the market

Checked on 2026-11-06.

| Need | Options |
| --- | --- |
| Storing secrets | AWS Secrets Manager or Parameter Store, HashiCorp Vault |
| Finding leaked secrets | [Gitleaks](https://github.com/gitleaks/gitleaks), GitHub secret scanning |
| Vulnerable packages | [Dependabot](https://docs.github.com/en/code-security/dependabot), `pip-audit` |
| Who did what | AWS CloudTrail, your own audit table |

**MCP needs extra care.** A third-party MCP server's tool descriptions go into your model's context, so a bad server can inject instructions. It's a supply chain risk, listed as ASI04 on [OWASP's agentic list](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/). Treat an MCP server like any dependency: read it, pin it, and give it the least access you can.

**Coding agents too.** The same rules apply to AI tools working on your code. They can read `.env` files, and [the OWASP cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html) suggests blocking secret-bearing files from tools, and keeping real secrets and customer data out of test fixtures.

If a secret does leak: **rotate it first.** Deleting it from git isn't enough, because it stays in the history, and may already have been copied.

## Try it

1. Read `search_policy` and `get_order_status` in `src/shophelper/mcp/server.py`. What can the model control in each?
2. Run `git log --all --oneline -- .env`. Nothing should come back.
3. Search the repo for anything that looks like a real secret. What do you find, and is it safe?
4. Design one new tool for this shop, such as changing a delivery address. Apply the six rules at the top. Should it be on the MCP server?

## Interview questions

### How do you design a safe tool for an agent?

**Strong answer:** I assume an attacker will call it. So it does one narrow thing, takes few arguments, and validates them in code. Identity comes from the session, never from an argument. Reads and writes are separate, and anything that changes state goes through rules and approval. I'd never give a model `run_sql`. My order tool takes an order id, and the code runs a fixed query with the owner filter.

**Follow-up:** What about tools that must take free text?

### Where do secrets belong in an AI application?

**Strong answer:** In a secret manager or the environment, read at runtime, and never in code, prompts or logs. The model should never see one, because anything in its context can leak. I prefer short-lived credentials: my deployment uses a role, and my service token lasts 60 seconds. If one leaks, I rotate it first, since removing it from git doesn't undo the exposure. My project doesn't have a secret scanner yet, and I'd add one.

**Follow-up:** How would you give an agent access to a third-party API?

### What are the risks of connecting a third-party MCP server?

**Strong answer:** Its tool descriptions go into my model's context, so it can inject instructions. Its tools might do more than they say, and it may see my data. I'd treat it as a dependency: review it, pin the version, limit what it can reach, and require approval for anything that changes state. I built my own server read-only for this reason, because any client can reach it.

**Follow-up:** How do you check a server hasn't changed?

## Check yourself

### Why is `run_sql` a bad tool?

- [ ] SQL is too slow — speed isn't the problem.
- [x] Injected text could run any query — right: narrow tools limit the damage.
- [ ] Models can't write SQL — they can, which is the problem.

### A key is pushed to git by mistake. What's first?

- [x] Rotate the key — right: it may already be copied.
- [ ] Delete the commit — it may already be copied.
- [ ] Wait to see if it's used — that's too late.

### Why does the service token last 60 seconds?

- [ ] Tokens can't last longer — they can.
- [ ] To save memory — that's not why.
- [x] A leak is only useful briefly — right: it never needs revoking.
