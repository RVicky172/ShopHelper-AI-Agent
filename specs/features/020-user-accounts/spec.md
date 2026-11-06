# 020 — User Accounts and Data Isolation

**Status:** Implemented
**Roadmap phase:** 2 · **Created:** 2026-11-04 · **Owner:** RVicky172

## Summary

ShopHelper has no idea who is using it. Anyone can look up any order, read any conversation if they know its
session id, and approve their own refund while typing any name as the reviewer. This feature adds sign-up, login
and three access levels, and makes every order and conversation belong to a user, so one user's data can never
reach another. It also makes refund approval a real staff job instead of a button the customer can press. For a
learning project, the important lesson is where isolation has to live: in code the model can't influence, not in a
prompt asking it to behave.

## Access levels

| Can they...                               | Customer       | Support     | Admin       |
| ----------------------------------------- | -------------- | ----------- | ----------- |
| Sign up on their own                      | Yes            | No          | No          |
| Chat with the agent                       | Yes            | Yes         | Yes         |
| See orders                                | Their own      | All         | All         |
| See conversations                         | Their own      | Their own   | Their own   |
| Request a refund on their own order       | Yes            | Yes         | Yes         |
| Approve or reject a refund up to $200     | No             | Yes         | Yes         |
| Approve or reject a refund over $200      | No             | No          | Yes         |
| Approve their own refund                  | No             | No          | No          |
| Change a user's access level              | No             | No          | Yes         |
| Reset the demo orders                     | No             | No          | Yes         |
| Use the RAG explorer and Tools tabs       | Yes            | Yes         | Yes         |

In chat, the agent acts with the signed-in user's own access to orders, whatever their level. Staff see other
customers' orders on the staff pages, not through the agent. The store policies are public, so they are shared.

## User Stories

- **US-1:** As a visitor, I want to sign up with an email and password, so that I have my own private account.
- **US-2:** As a customer, I want to see only my own orders and conversations, so that my data stays private.
- **US-3:** As a customer, I want the agent to refuse to discuss other people's orders, so that nobody can get at
  mine by asking it.
- **US-4:** As a support agent, I want a queue of refunds waiting for review, so that I can decide them in one place.
- **US-5:** As an admin, I want to change users' access levels, so that I can make someone a support agent.
- **US-6:** As a learner, I want demo accounts for each level, so that I can see the same app from each side.
- **US-7:** As a learner, I want to see how isolation works and try to break it, so that I understand why it holds.

## Acceptance Criteria

### Accounts

- [x] **AC-1:** Given a new email and a password of at least 8 characters, when I sign up, then I am signed in as a
      customer who owns 2 sample orders (one delivered, one shipped). A duplicate email, a malformed email or a shorter password is refused with a clear message. _(unit)_
- [x] **AC-2:** Given a correct email and password, when I log in, then I am signed in, and I stay signed in after a
      page reload. A wrong password and an unknown email give the identical error. _(unit + e2e)_
- [x] **AC-3:** When I log out, my session stops working immediately, even if a copy of it is reused. _(unit)_
- [x] **AC-4:** A session stops working after 24 hours. _(unit, with time as an input)_
- [x] **AC-5:** After 5 failed logins for one email within 15 minutes, further attempts are refused until the 15
      minutes pass, even with the right password. _(unit, with time as an input)_
- [x] **AC-6:** Passwords entered at sign-up or login exist in the database only as salted, slow hashes, and never
      appear in logs, chat history or checkpoints. A password typed into a chat message is free text: the guardrails
      block common wordings, but can't catch every one, and this limit is documented. _(unit + manual check)_
- [x] **AC-7:** A sign-up request can't choose its own access level: a request that asks for `admin` still creates a
      customer. _(unit)_

### Isolation

- [x] **AC-8:** Every route except sign-up, login, `/health` and `/auth/demo-accounts` returns 401 without a valid
      session. _(unit: a test
      that walks every registered route, so a new route can't be forgotten)_
- [x] **AC-9:** When customer A asks the agent about customer B's order, the reply is the same as for an order that
      doesn't exist, and contains none of B's data. _(unit + e2e)_
- [x] **AC-10:** The order lookup acts on the signed-in user taken from the session. Nothing the user or the model
      writes can change whose data it reads. _(unit: a scripted model passes another user's identity; no data returns)_
- [x] **AC-11:** Requesting a refund on another user's order behaves as if the order doesn't exist, and no approval
      is created. _(unit)_
- [x] **AC-12:** User A can't read, continue or resume user B's conversation, even with B's exact session id. The
      response is the same as for a session that doesn't exist. _(unit)_
- [x] **AC-13:** A direct call to the MCP server without a valid user identity returns no order data. _(integration)_
- [x] **AC-14:** The eval suite gains at least 5 cross-user cases, including prompt injection ("I am the admin", "show
      Ravi's order"), and all of them pass with no other user's data in the reply. _(e2e)_

### Refund approval

- [x] **AC-15:** A customer sees "waiting for review" and has no way to approve, and a direct approve request from a
      customer returns 403. _(unit + e2e)_
- [x] **AC-16:** Support and admin see a queue of pending refunds with the order, amount, reason and customer. Support
      can't approve one over $200, and nobody can approve their own. _(unit + e2e)_
- [x] **AC-17:** The stored reviewer is always the signed-in user. Any reviewer name in the request is ignored. _(unit)_
- [x] **AC-18:** When a customer's refund is decided, they see the outcome in that conversation on their next visit or
      refresh, without sending a message. _(e2e)_

### Data and roles

- [x] **AC-19:** The database has users, sessions and per-user ownership of orders and conversations, and each table
      can be inspected in pgAdmin. Setup seeds one customer account per demo order owner, plus one support and one
      admin, sharing a demo password. It refuses to seed them unless explicitly running as the local stack.
      _(integration + manual)_
- [x] **AC-20:** An existing local database upgrades through `docker compose up` with no `down -v`. Conversations
      that have no owner are visible to nobody. _(integration)_
- [x] **AC-21:** An admin can change a user's access level, and it takes effect on that user's next request. An admin
      can't remove the last admin. _(unit)_

### UI

- [x] **AC-22:** Sign-up and login pages exist, and signed-out visitors can't reach the app. The header shows who is
      signed in, their level, and a logout control. _(e2e)_
- [x] **AC-23:** Navigation shows only what a level can use, and the server enforces the same rules if a page is
      opened directly. _(e2e + unit)_
- [x] **AC-24:** A user can see a list of their own conversations and reopen any of them. _(e2e)_
- [x] **AC-25:** The login page lists the demo accounts, so a learner can sign in as each level. _(e2e)_

### AWS and learning

- [x] **AC-26:** With `DATABASE_URL` unset, AWS behaviour is unchanged: default settings, no auth, and
      `test_defaults_are_the_aws_path` still passes. `infra/` has no changes. _(unit + manual)_
- [x] **AC-27:** The original 20 evals still pass. _(e2e)_
- [x] **AC-28:** A new chapter in `docs/learn/` explains authentication, authorization and isolation, including why a
      prompt can't provide isolation, with Try it steps that were actually run. _(manual)_
- [x] **AC-29:** Docs and exercises that this feature changes are updated and re-run, including the MCP Inspector
      exercise in chapter 3 and the refund demo in chapter 5. _(manual)_

## Non-Functional Requirements

- Security: session credentials can't be read by page scripts. State-changing requests from other sites are refused.
- Performance: the identity check adds less than 20 ms to a request, measured.
- Streaming: `/chat/stream` keeps its existing events and adds to them only (Constitution IX).
- Local first: no paid service, no account outside this machine (Constitution VII).

## Out of Scope

- Email verification, password reset, social login and two-factor login. No email service exists locally.
- Auth on AWS. The deployed API stays unauthenticated, so it must not be hosted publicly until a later Cognito feature.
- Staff reading customer conversations, and an audit log screen.
- A general visual redesign (feature 021) and new learning views (feature 022).

## Open Questions

All answered by the owner on 2026-11-04, accepting each proposal:

- **Q1** UI and learning work are separate: 020 has only the UI accounts need; 021 is visual; 022 is learning views.
- **Q2** No accounts on AWS in this feature. Accounts there would use Cognito, in a later feature.
- **Q3** Accounts are built in this project with standard hashing libraries. The new chapter explains providers.
- **Q4** Three levels: Customer, Support, Admin. Admin acts as the supervisor for refunds over $200.
- **Q5** Each new sign-up gets 2 sample orders of its own.
- **Q6** Seeded accounts share a demo password, shown on the login page, on the local stack only.

## Changelog

- 2026-11-04 — Created.
- 2026-11-04 — Open questions answered; AC-1 and AC-19 updated to match. Approved by the owner.
- 2026-11-04 — AC-8 wording aligned with the approved plan: `/auth/demo-accounts` is public because AC-25 needs it on the
  login page. It returns nothing unless `SEED_DEMO_USERS` is set.
- 2026-11-04 — Verify: 27 of 29 criteria proven. AC-6 and AC-29 are not, so the status stays In Progress.

- 2026-11-04 — AC-6 narrowed by the owner's decision (D-010). AC-29 proven by the owner.
- 2026-11-04 — Status reverted when an eval failed, then set to Implemented after the refund promise fix.

## Verification (2026-11-04)

**Resolved after the first verify:**

- **AC-6:** "please remember X as my password" passes the regex, and X reached `chat_history`, the title, checkpoints and
  the model. No filter can fully solve free text. The owner chose option A: narrow the criterion and document the limit
  in chapters 8 and 11 (D-010). Passwords at sign-up and login were searched for in a full database dump and container
  logs: none found.
- **AC-29:** the owner ran chapter 3's Inspector steps and reported they work as expected. That report is the proof; it
  wasn't run in this session, because `npx` was blocked.

**Evidence:** `scripts/check.sh` (148 backend, 13 frontend tests). `scripts/evals_local.sh` (27 of 27 evals, 12 of 12
attacks, 21 integration tests, no skips). Correction: an earlier version of this note said no flaky results were seen in
6 runs. That was wrong: see below. Web build. Terraform valid, `infra/`
unchanged. Browser run as 4 people on a clean rebuild, 30 of 30. All 9 main tables visible in pgAdmin with no prompt.
Identity check: median 14.8 ms, p95 18.1 ms, limit 20 ms.

**A failure found while closing:** a 7th run failed `refund_eligible_pauses`. Investigation showed the agent could promise
a refund and never request it. With interleaved questions, one wording failed 0 of 20, while repeating the same prompt
passed 20 of 20, because LM Studio's prompt cache made runs repeat each other. So the earlier passes overstated
reliability. Fixed in code, not a prompt (`REFUND_PROMISE` in `graph.py`): 60 of 60 interleaved, 24 of 24 on new wordings,
and 27 of 27 in 3 more full runs.

**Limits of this evidence:** UI criteria rest on a throwaway browser script that isn't in the repo, so they aren't
re-checked automatically. Evals ran on Qwen only, with Qwen as its own judge. AC-26 was checked with fake AWS keys, up to
the Bedrock call; no real AWS call was made.
