---
title: Authentication
checked: 2026-11-06
---

## What you'll learn

- How to store a password safely
- How an app remembers you: sessions and JWTs
- What the cookie flags do
- How a login form leaks information, and how to stop it

## The simple explanation

**Authentication** asks "who are you?". **Authorization** asks "what may you do?". This lesson is the first one, and [the next](07-authorization-and-isolation.md) is the second.

| | Authentication | Authorization |
| --- | --- | --- |
| Asks | Who are you? | What may you do? |
| Answered by | Password and session | Your level, and who owns the data |
| Fails with | 401 | 403 |

Think of a hotel. Showing your passport at the desk is authentication. It happens once. Then you get a key card, which is your **session**, so you don't need the passport at every door. The card opening only your room is authorization.

**Never store a password.** If the database is stolen, every account goes with it. Store a **hash**, a one-way fingerprint. To check a login, hash what was typed, and compare.

Ordinary hashes like SHA-256 are the wrong tool, because they're built to be fast, which lets an attacker try billions of guesses. **Argon2** is slow on purpose, and uses a lot of memory, so each guess is expensive. Each password also gets a random **salt**, so two people with the same password have different hashes.

## An example

Here's what's stored for a password, and you can read the settings in it:

```text
$argon2id$v=19$m=65536,t=3,p=4$...
```

That's 64 MB of memory and 3 passes for every single guess. [OWASP's minimum](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) is 19 MiB, 2 passes and 1 lane, so this library's defaults are well above it.

Now look at how a login form can leak. An attacker wants to know if `someone@example.com` has an account:

| Leak | Fix used here |
| --- | --- |
| Different errors for a wrong password and an unknown email | One message for both |
| Unknown emails answer faster, because nothing is hashed | A decoy hash runs anyway |
| Only real accounts get locked | Failed attempts count for any email |

The second one is easy to miss. Argon2 is slow, so skipping it for an unknown email creates a timing difference anyone can measure. So the code always hashes:

```python file=src/shophelper/accounts/auth.py
matches = _password_matches(user.password_hash if user else _decoy_hash(), password)
```

## How ShopHelper does it

**Staying signed in.** There are two common ways:

| | Session in the database | JWT (a signed token) |
| --- | --- | --- |
| The browser holds | A random id | The data itself, signed |
| Each request | Looks up the database | Checks a signature |
| Log out at once | **Yes**: delete the row | No: it's valid until it expires |
| Change a level at once | **Yes** | No: the old level stays in the token |

The spec requires logout to work immediately, so browser sessions use the database. Only a hash of the token is stored, so a stolen table can't be replayed. The level is read fresh on every request.

JWTs aren't wrong, they just suit a different job. This project uses them between the agent and the MCP server, where a token lasts 60 seconds and never needs revoking.

**The cookie:**

```python file=src/shophelper/api/auth_routes.py
httponly=True,  # page scripts can't read it
samesite="strict",  # the browser won't send it on requests started by other sites
```

- **`HttpOnly`:** a script injected into the page can't steal the session. It can still act as the user while the page is open, so it isn't a complete defence.
- **`SameSite=Strict`:** the browser won't send it on requests other sites start.
- **`Secure`:** this sends the cookie over HTTPS only. **It isn't set here**, because the local stack runs on plain HTTP. A real deployment must set it.

`SameSite` ignores ports, so an app on `localhost:3000` counts as the same site. That's why the gate also checks the `Origin` header on anything that changes data.

**Protected by default.** Adding a check to each route is risky, because the one you forget is open. Here, one gate wraps every request, and a short list is public:

```python file=src/shophelper/api/auth_routes.py
PUBLIC_PATHS = {"/health", "/auth/signup", "/auth/login", "/auth/demo-accounts"}
```

A new route is protected without anyone remembering to do it. A test walks every route and checks for a 401. That test once silently skipped half the routes, and a second test exposed it. When a test checks "all of X", also check that X really was all of them.

**Lockout.** Five failures in 15 minutes locks that email:

```python file=src/shophelper/accounts/auth.py
if store.count_failures(email, since=now - LOCK_WINDOW) >= MAX_FAILURES:
```

This slows guessing, but someone could lock a victim out on purpose. Real systems add limits per IP address, which this project doesn't have.

**Very long passwords** are refused before hashing, because slow hashing of huge input is an easy way to overload a server.

## In the market

Checked on 2026-11-06.

**In a real product, use an identity provider.** Accounts are hand-built here so you can read every step, not because it's the right production choice. Providers handle what this project doesn't have: email verification, password reset, two-factor login and passkeys.

| Provider | Kind | Fit |
| --- | --- | --- |
| [Keycloak](https://www.keycloak.org/) | Open source, you run it | You need self-hosting and full control |
| [Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html) | Managed | You're already on AWS |
| [Auth0](https://auth0.com/docs) | Managed | Enterprise login across many customers |

We've left out prices and free limits, because the ones we found came from blogs and vendors, and changed in 2026.

[OWASP's session guide](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) is the checklist to learn from. It asks for `Secure`, `HttpOnly` and `SameSite`, at least 64 bits of randomness in a session id, and 128 bits if you make your own.

## Try it

1. **See the cookie is hidden.** While signed in, open the browser console, and type `document.cookie`. The session cookie isn't there. Find it under **Application**, then **Cookies**, marked `HttpOnly`.
2. **Look at what's stored.** In pgAdmin:

```sql
SELECT email, role, left(password_hash, 30) AS hash_start FROM users;
SELECT left(token_hash, 12) AS token_hash, user_id, expires_at FROM auth_sessions;
```

Neither table holds anything a thief could use directly.

3. **Compare the errors.** On the sign-in page, try a real email with a wrong password, then a made-up email. The message is the same.

## Interview questions

### How do you store passwords?

**Strong answer:** As a slow, salted hash, using a library. I use Argon2id, which costs time and memory for each guess, so a stolen table is expensive to attack. SHA-256 is too fast for this. The salt stops two identical passwords matching. I'd never write this myself, and I'd refuse very long passwords before hashing, so it can't be used to overload the server.

**Follow-up:** How would you raise the settings for existing users?

### Sessions or JWTs?

**Strong answer:** It depends on revocation. Database sessions can be ended at once, and a change in access applies on the next request, at the cost of a lookup. JWTs need no lookup, but stay valid until they expire. In my project browsers use database sessions, because logout must be immediate, and I store only a hash of the token. Between services I use a JWT that lasts 60 seconds, so revocation doesn't matter.

**Follow-up:** Where should a browser keep a JWT?

### How can a login form leak who has an account?

**Strong answer:** Three ways I closed: different error messages, a faster response for unknown emails because nothing is hashed, and lockouts that only happen to real accounts. So there's one message, a decoy hash runs for unknown emails, and failures count for any email. Sign-up and password reset can leak too, so those need the same care. Mine has no reset flow, and that's a known gap.

**Follow-up:** Does your sign-up form leak this?

## Check yourself

### Why is SHA-256 a poor choice for passwords?

- [x] It's too fast, so guessing is cheap — right: password hashes are slow on purpose.
- [ ] It can be reversed — hashes are one-way.
- [ ] It's too slow — the opposite is true.

### Why run a hash for an email that doesn't exist?

- [ ] To create the account — nothing's created.
- [x] So timing doesn't reveal who has an account — right: both paths take as long.
- [ ] To slow down the server — that's not the goal.

### Why does this app keep browser sessions in the database?

- [ ] JWTs aren't secure — they have different trade-offs.
- [ ] Cookies can't hold a JWT — they can.
- [x] Logout has to work immediately — right: delete the row, and it's over.
