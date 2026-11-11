# Learnings & Gotchas

Non-obvious facts discovered while building. Keep entries short; group by topic (`## <Topic>`). Add one when
something cost more than ~10 minutes or the fix was non-obvious. Delete entries that become wrong.

## Windows and Docker

- Host code must use `127.0.0.1`, not `localhost`, for Postgres. `localhost` tries IPv6 first and stalls.
- A file mounted from Windows can't be `0600`, so libpq ignores it. pgAdmin's entrypoint copies `pgpass` first.
- File events don't cross a Windows bind mount: `WATCHFILES_FORCE_POLLING` and Vite's `usePolling` are required.
- `uv run uvicorn` on the host reads the stale AWS names in `.env`.

## Local model behaviour (Qwen3 30B)

- It may write "I'll process the refund" and stop without calling the tool. The prompt rule "call the tool now"
  fixed it. It also asked for confirmation until told not to.
- `{EMAIL}` at the start of a message made it ask for the order number. Explaining the placeholders fixed it.
- It sometimes writes text before a tool call. The reducer clears that text on a `model_step` with tool calls.

## RAG

- With nomic, unrelated text still scores around 0.5, so scores are only meaningful relative to each other.
- Vector search always returns something. Relevance is left to the model and the system prompt.
- Chunks are retrieved alone, so a term defined in another chunk may not arrive. "Electronics only" came back without the definition of
  electronics, and the model guessed wrong. A line that depends on a definition should carry it. Print the passages before blaming the model.

## Evals

- YAML treats an unquoted ` #` as a comment: `order #1005` silently became "Can you check order".
- Models write curly apostrophes, so string checks normalise them.
- The OpenAI client caches connections, so pytest needs one event loop:
  `-o asyncio_default_test_loop_scope=session`. Otherwise cases fail with `Event loop is closed`.

## LangGraph

- On resume, a node re-runs from the top, so side effects go after `interrupt()`.
- A resumed turn gets `tool_end` with no `tool_start`, because the tool started before the pause.

## Identity and cookies

- Inside a LangGraph node, an MCP interceptor's `request.runtime` is `None`. Pass identity with a `ContextVar`.
- `SameSite` ignores ports, so another app on `localhost:3000` counts as same-site, and the Vite dev server reflects
  localhost origins in CORS headers. The API's own `Origin` check is what actually protects it.
- `localhost` and `127.0.0.1` are different origins, so the API's exact check refused sign-in at `127.0.0.1:5173` with a 403. It's the API refusing, not a browser CORS error. Add an exact
  origin to `EXTRA_WEB_ORIGINS`, never a wildcard. A changed variable needs `docker compose up -d api`, not a restart.
- FastAPI 0.162 wraps `include_router` routes in `_IncludedRouter`, so `app.routes` doesn't list them. A test walking
  routes must also use `app.openapi()["paths"]`, and should assert that known routes were actually seen.
- FastAPI app-level dependencies don't cover `/docs` or `/openapi.json`. Use ASGI middleware to protect everything.

## Type checks and lint

- One missing return type can cause dozens of errors: `db.connect()` alone made every row look like a tuple. Sort by cause, not by file.
- A `# pyright: ignore` inside a multi-line f-string is part of the string, so it would go into the SQL. Wrap the value instead: `db.trusted()`.
- A linter's automatic fix can change behaviour. A `<button>` in a form submits by default, so `type="button"` would have broken sign-in.
- A tool's peer dependencies decide whether it fits: `typescript-eslint` stops below TypeScript 6.1. Check before choosing, not after.

## Docker

- Listing a lesson in `course.json` before its file exists makes the plugin fail with `ENOENT`, so the course stops loading. With a new stage folder it stayed
  stuck after the files arrived, and `docker compose restart web` fixed it. Test-first lesson work triggers this, so restart before a browser run.

- A `git checkout` that rewrites `web/` can leave Vite failing with `Failed to resolve import "./index.css"`, though the file exists, and every
  page goes blank. `docker compose restart web` fixes it. The HTML still returns 200, so check `/src/main.tsx`, not just the page.

- PyPI downloads in a Docker build can crawl at about 35 KB/s here, because this ISP's IPv4 route to
  `files.pythonhosted.org` is slow and containers have no IPv6. Other hosts run at full speed, and it isn't Docker's
  fault. Test the same server with `curl -4` and `curl -6` before blaming the build.
- Workaround with no repo changes: `HTTPS_PROXY` is a predefined build arg, so `docker build --build-arg
  HTTPS_PROXY=http://host.docker.internal:PORT` can use a local CONNECT proxy, limited to PyPI's hosts, that runs on the
  host and so gets IPv6. Hash pinning still verifies every package. Only needed when `requirements.txt` changes.
- `web` keeps `node_modules` in an anonymous volume, so `docker compose up --build` builds the new packages and then hides
  them behind the old volume. Use `docker compose up --build -V web` after changing `package.json`.

## Integration tests

- The MCP server reads the real database, so a test going through the agent can't use the scratch database. It must run as demo
  users and delete what it creates in a `finally`.

## Keeping copies honest

- The web container sees only `web/`, so it can't read `knowledge/`. `web/src/shop/returns-policy.md` is a copy of the agent's policy,
  and a test fails if they differ: edit both.

## Writing lessons

- Run every Try it step. "Open What's stored" read fine, but it's a heading, with documents to expand. Only doing it showed that.
- Check a claim against the source you link, not a search summary. One interview claim had no source that said it.
- Never write an interview answer claiming something the project hasn't done. The reader will repeat it.
- `search.ts` beside `Search.tsx` fails TypeScript on Windows, where those are the same name.
- Don't quote a spec's acceptance criterion in a `file=` snippet. Its `- [ ]` becomes `- [x]` at Verify, and the snippet test then fails. Use a blockquote.

- A public tracker can state the opposite of a company's own page: one said Anthropic allows AI in coding rounds, with no source. Read the company's page.
- Add a lesson's file before listing it in `course.json`. A test can read the file directly, so test-first still works, and Vite doesn't get stuck.

- Measure the exercise, not just the idea. A repeated prompt took 0.07 s by direct call, but repeating a chat question changed nothing, because the
  conversation had grown.

## React state

- Effects run twice in development (StrictMode), so an effect that calls a server must be safe to repeat. Take the work out of
  shared state first, then call. Quantities capped at 10 can hide a double merge, so check with an item well under the cap.
- A `disabled` button only takes effect after a render, so a double click still fires twice. Guard with a ref.

- An arrow effect returns its value: `useEffect(() => el.scrollIntoView())` crashed the whole app in Chromium, where it returns a Promise
  ("destroy is not a function"). TypeScript didn't flag it. Use braces in effects.

## React Router

- Inside a `*` route, a relative link resolves against the whole current URL, so `to="tools"` on `/how-it-works/rag` gave
  `/how-it-works/rag/tools`. Use absolute paths there.

## Sabotage checks

- `scripts/evals_local.sh` resets the real demo orders, so sabotaging `reset()` damages real data. Run
  `docker compose up setup` afterwards to restore owners.
- Restoring a file doesn't guarantee the `mcp` container reloads it. Run `docker compose restart mcp` after sabotaging
  `mcp_server.py`, and before trusting any live result.
- A "no leaks" result needs a positive control: check that each real user still sees their own data. Without one, a
  server that treats everyone as the same user also shows no leaks.

## Frontend and accounts

- Isolation applies in the browser too: key the signed-in tree by user id, clear the query cache on login and logout.
- The local card rule flags any 13-19 digit number, so a timestamp in a message gets blocked. Use letters in test data.
- Browser runs against the live stack leave real conversations in demo accounts. Remove them by their exact test message.
- A URL glob like `**/staff/orders` also matches `/signin?next=/staff/orders`, so a script can run signed out and report success. Wait
  for something only a signed-in page has, and look at a screenshot before believing a clean result.
- Browsers log every 4xx as a console error. To judge "no console errors", list failed responses by URL.

## Searching for leaks

- Checkpoints are binary, so `pg_dump | grep` misses them. Search with `position('x'::bytea in blob)` and include a
  control word you know is there.

## Measuring model behaviour

- Check wording against the live agent. "How long does delivery take?" made it ask for an order number, and "What is your delivery
  policy?" retrieved a passage with no delivery times. Accept nothing just because a tool was called: check the terms in the answer.

- LM Studio's prompt cache makes repeated prompts repeat their result: one refund wording scored 20/20 repeated and 0/20
  interleaved. Evals passing several times proved little. Put other questions between samples.
- A prompt rule can look fixed and not be. Anything a customer relies on needs a check in code.
- A brand name the model doesn't know reads as a product, not a policy, so it skips `search_policy` and answers anyway. Naming "ShopHelper
  Care" in the prompt made this worse: it then invented which categories Care covers. Failures follow the wording, not chance (the same 4
  of 8 failed every round), so one passing eval case says little. Test several wordings.

## Testing vector search

- Uniform random vectors are the worst case for HNSW: recall@10 was only 0.28 to 0.60 on 50,000 of them. They say nothing about
  real text, so measure recall on real embeddings before quoting a number.
- On 24 chunks, top 4 is a sixth of the data, so most retrieval changes show no difference. Say the test can't tell, not that the
  change doesn't matter.

## Cleaning up test data

- `psql -c "a; b; c"` runs as one transaction, so one bad statement rolls back all of it, and piping to `tail` can hide that. Use a
  separate `-c` per statement, then check the row count.

## Claude Code

- A Claude Code hook that doesn't match does nothing, with no error. On Windows, `file_path` arrives with backslashes, so a `migrations/` pattern let
  every edit through. Match `migrations[/\\]+`, and test a hook by watching it block something.
- Git Bash rewrites `claude -p "/context"` into a file path. Set `MSYS_NO_PATHCONV=1`.
- Backslashes in a Python heredoc sent through the Bash tool arrive halved, so `\n` became a real newline three times, breaking test files. Never write test code that way: use Write or Edit.
- An experiment that edits a file needs a reset between runs. One leftover edit made the next run a different test.

## Measuring glass

- Headless Chrome can't measure blur's cost: 121 frames a second for every version, even at 4x slower CPU. Blur is GPU work, so test on a real phone.
- A number that doesn't change when its input does is a broken test. Contrast stayed the same at every opacity because `body`'s background hid the ground.
- With `html` and `body` both given backgrounds, a `z-index: -1` layer sits under `body`'s. Make `body` transparent.
- To test text on a glass navbar, keep real content under it. Hiding the product images made 70% look safe.

## Sabotage steps

- Adding `/orders` to `PUBLIC_PATHS` fails no route test, because the route's own dependency still returns 401. Run a sabotage step before
  writing it down as one a learner can try.

## Reading AWS prices and docs

- WebFetch resets on aws.amazon.com and docs.aws.amazon.com. curl works, and exact prices come from
  `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<service>/current/<region>/index.json`.
