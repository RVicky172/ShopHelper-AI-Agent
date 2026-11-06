# 021 — Storefront · Tasks

**Plan:** `./plan.md`
Legend: `[P]` = can run in parallel with the previous task. Each task lists files and the proving test.
Test-first: each "tests" task must fail before its paired implementation makes it pass.
When a task is done, tick it and add an indented **Result (YYYY-MM-DD):** note: what was done, numbers measured,
anything surprising or deferred.

Gate after each task: `scripts/check.sh`. Also run `scripts/evals_local.sh` after any task marked **(evals)**.
UI checks are manual (D-012): record what was run in the task's Result.
Each stage must leave the app working.

## Setup

- [x] **T001** — Spike: draw 8 illustrations, one per category, in both themes, and show them to the owner. **Stop for
      review** before T062 · files: `web/public/products/*.svg` · test: owner's approval
      **Result (2026-11-04):** Owner approved the style for all 42 products, including solid shapes inverting in dark mode. 8 SVGs drawn, 1.1-2.4 KB each: headphones, keyboard,
      laptop stand, phone case, portable charger, French press, canvas backpack, kettlebell. The last three aren't demo items, so
      T010 must include them, and file names must match product slugs. Conventions for T062: 400x400 viewBox, `--tint`, `--ink` and
      `--paper` set in the file, 6 px lines, no text. Ink on tint measured 12.0-13.6:1 light and 8.2-10.7:1 dark. Readable at
      150 px. In Chromium, `prefers-color-scheme` inside an `<img>` followed the device with or without page `color-scheme`; other
      browsers weren't tested.
- [x] **T002** — Add `react-router` and the font package, rebuild the web image · files: `web/package.json`,
      `web/package-lock.json` · test: `npm run build`, and the `web` container starts
      **Result (2026-11-04):** Added `react-router` 8.5.1 and `@fontsource-variable/schibsted-grotesk` 5.3.0, 0 vulnerabilities.
      Neither resolved in the container before; both do now, and `web` serves 200, including an SVG. A plain `up --build` left the
      old `node_modules` volume in place, so `-V` is required. Added to `docs/local-setup.md` and `memory/learnings.md`.
- [x] **T003** — Design tokens for both themes, with a contrast script checking every pair · files: `web/src/index.css`,
      scratch script · test: every text pair at 4.5:1 or better, on both palettes
      **Result (2026-11-04):** The script reads `index.css` and failed 43 pairs before the change, then 1 real one: `danger` on its
      own 10% background was 4.43:1, so `danger` went from `#C2413A` to `#B5362F`. Now 27 text pairs per theme pass, lowest 5.11
      light and 5.42 dark, and 12 graphic pairs pass 3:1, lowest 3.29 light and 5.47 dark. The plan's contrast figures all matched.
      Added `field`, `on-cobalt`, `on-marigold`, a global focus ring and body colours, and moved all 9 form fields to `border-field`.
      Browser, both themes: font loads locally, no requests to other sites, no page errors, sign-in and chat work, and only the
      expected signed-out 401. `tabular-nums` works (`1111` and `0000` both 101.56 px). Old names (`panel`, `sunken`, `line`, `accent`,
      `on-accent`) stay as aliases until the views move; remove them in T081. Marigold stars are 1.91:1 on white, so T050 must
      keep the numeric rating beside them.

## Catalogue backend

- [x] **T010** — Write `products.json`: 8 categories, at least 40 products, including all 7 demo order items · files:
      `src/shophelper/data/products.json`, `tests/test_shop.py` · test: a test checks the counts, fields and demo items
      **Result (2026-11-04):** 8 categories, 42 products, 5 or 6 in each. All 9 ordered items, including the 2 sample orders, are
      products at the price paid, and all 8 drawings match a slug. Ids are fixed in the file because guest carts store them.
- [x] **T011** — Failing tests: list, category filter, 4 sorts, paging, product by slug, related products, 404s, and an
      unknown sort is refused · files: `tests/test_shop.py`
      **Result (2026-11-04):** Tests written first and failed on the missing module. They also cover paging reaching every product
      exactly once, a stable tie-break, and a page size capped at 12.
- [x] **T012** — `ProductRepo` in memory and Postgres, table, seeding · files: `catalog.py`, `schema.sql`,
      `setup_local.py`, `evals/test_integration.py` · test: T011, and a Postgres test
      **Result (2026-11-04):** Postgres returns exactly what the in-memory repo does, for 4 sorts, 3 category filters and 5 offsets,
      plus every product and its related list. 38 of 38 integration tests pass. `setup` on the real database: 42 products, with
      7 orders and 9 users kept. Seeding upserts by id, so a product removed from the file stays in the table.
- [x] **T013** — Public catalogue routes · files: `shop_api.py`, `api.py` · test: T011
      **Result (2026-11-04):** Three routes, default sort `rating`, related list of up to 4. Sabotage: removing `accounts_only` failed
      3 tests. T051 will need one product per category, and `/products` allows at most 12 per call, so it may need a small addition.
- [x] **T014** — Failing test for the exact public set, then `is_public`, GET only · files: `auth_api.py`,
      `tests/test_isolation.py` · test: route walk; sabotage: allow POST on a public path
      **Result (2026-11-04):** `PUBLIC` is now method and path pairs. Sabotage: ignoring the reads failed 21 tests, allowing any method
      failed 12, and prefix matching failed 4. Live as a guest through `/api`: catalogue reads work; `/orders`, `/cart` and
      `POST /products` return 401.

## Cart and orders backend

- [x] **T020** — Failing tests: add, change, remove, cap at 10, merge with changes reported, one user can't touch another's
      cart · files: `tests/test_shop.py`
      **Result (2026-11-04):** Tests written first and failed on the missing module. They also cover a tampered guest cart (a quantity
      of 10^30, duplicates), a 100-item limit, and that no cart route takes a user id.
- [x] **T021** — `CartStore` in memory and Postgres, and cart routes · files: `cart.py`, `shop_api.py`, `schema.sql` ·
      test: T020, and a Postgres test; sabotage: remove the user filter
      **Result (2026-11-04):** One pure `merge_items` serves both stores. A merge reports `combined`, `capped` and `unavailable`; a guest
      cart joining an empty account reports nothing. 8 merges racing lost nothing. Sabotage, all caught: shared memory cart (3 tests),
      Postgres read without the user filter (1), delete without it (1), merge without its lock (1), no cap (2).
- [x] **T022** — Failing tests: checkout uses server prices, ignores a sent price, empties the cart, refuses an empty cart,
      needs a session, gives the order an owner · files: `tests/test_shop.py`
      **Result (2026-11-04):** Written first, with T024's tests: 22 failed before the code existed.
- [x] **T023** — Checkout in one transaction, keeping the order shape · files: `orders.py`, `cart.py`, `shop_api.py` ·
      test: T022; sabotage: take the price from the request
      **Result (2026-11-04):** `DELETE ... RETURNING` claims the cart and the order is written on the same connection. 8 checkouts racing
      placed 1 order. Sabotage, all caught: price from the request (2 tests), cart not emptied (2), empty cart allowed (2), no owner
      (4), cart read before delete (1), cart committed before the order (1), everyone's cart emptied (1). `item` names the first line
      in product id order. A demo reset keeps bought orders. Live over HTTP: a sent total of 0.01 changed nothing (179.97 charged).
- [x] **T024** — Failing tests, then Mark delivered, by level and by status · files: `orders.py`, `shop_api.py`,
      `tests/test_shop.py` · test: customers get 403, a refunded order gets 409
      **Result (2026-11-04):** `POST /orders/{id}/deliver`. Customers get 403 before any lookup, so it reveals nothing about order
      numbers. The status check is in the Postgres `WHERE`. It also removes `estimated_delivery`. Sabotage, all caught: customers
      allowed (2 tests), any status in memory (3), any status in Postgres (3). Only the in-memory and Postgres repos have it, because
      this route doesn't exist on AWS.
- [x] **T025** — Confirm a bought order flows through the agent: lookup, cross-user refusal, deliver, refund · files:
      `evals/test_integration.py` · test: live run **(evals)**
      **Result (2026-11-04):** One test takes an order through the real model and MCP: the owner sees it, a stranger doesn't, an early
      refund is refused, then deliver, refund request, approval. Passed 4 of 4 runs. It uses the real database, because MCP does, and
      deletes its own rows; each run still uses up an order number. Evals 27 of 27, integration 56 of 56, unit 263.

## Agent and policies

- [x] **T030** — General store wording, lifestyle terms in the policies, re-embed · files: `graph.py`, `raw_agent.py`,
      `knowledge/policies/returns.md`, `warranty.md` · test: `setup` re-embeds exactly 2 documents **(evals)**
      **Result (2026-11-04):** `setup` embedded 2 documents and skipped 7. Both policies name the three categories and give example
      products, because customers ask about a yoga mat, not a category. Before the change the agent said a yoga mat had a 1-year
      warranty and a French press a 10% fee. Open question for the owner: whether ShopHelper Care covers lifestyle products.
- [x] **T031** — Add at least 2 lifestyle eval cases · files: `evals/golden_cases.yaml` · test: 3 full runs **(evals)**
      **Result (2026-11-04):** 3 cases added, 30 in all. Evals 30 of 30 in 3 full runs, faithfulness 5.0. On the old agent, 2 of the 3
      failed. The third (a kettlebell return) and the new test of a bought kettlebell order both passed there too, so they guard
      against regressions and don't prove a fix: the old prompt wasn't actually declining lifestyle questions.
- [x] **T032** — Measure refund submission with interleaved prompts · files: scratch · test: at least 60 of 60
      **Result (2026-11-04):** 60 of 60, over 8 wordings, 2 customers and a delivered lifestyle order, with an unrelated question after
      each attempt. Counted only when a request existed in the database. Qwen only: AWS gets this text on its next deploy, untested
      on Claude.

## Frontend shell

- [x] **T040** — Move `useChat` into `ChatProvider`, with the old layout intact, and prove a stream survives moving between
      tabs · files: `chat/ChatProvider.tsx`, `App.tsx` · test: browser check
      **Result (2026-11-04):** Browser, with the real model: moved away mid-stream and back, the answer arrived with 5 trace steps.
      Sabotage, provider mounted only inside the chat view: no answer, 0 trace steps. `useChat` now accepts a guest.
- [x] **T041** — Router and page URLs, with every existing page moved over and still working · files: `App.tsx`,
      `views/*` · test: browser check of each URL, reload and back button
      **Result (2026-11-04):** Every page has a URL, and reload and back work. The browser run caught a real bug: relative links in a
      `*` route resolved to `/how-it-works/rag/tools/tools`, so they're absolute now. A stream survives moving between real URLs.
      `/cart`, `/shop/*` and `/products/*` show not found until their tasks. How it works is its own 136 KB chunk.
- [x] **T042** — Navbar, account menu by level, footer, public landing with Sign in in the navbar · files: `layout/*`,
      `auth/*` · test: browser check as guest and each level
      **Result (2026-11-04):** Checked as guest, customer, support and admin: menu items, allowed pages, refused pages, log out. Shop menu
      opens with Enter, closes with Escape, and focus returns. No sideways scroll at 390 px. No failed responses. The cart count comes
      with T063. Landing is a stub until T051. `/account/orders` isn't offered to staff, because `/orders` returns everything for them.
- [x] **T043** — Sign in returns to `next`, and only accepts paths on this site · files: `auth/*` · test: browser check,
      including `?next=https://evil.example`
      **Result (2026-11-04):** `safeNext` asks the URL parser where a link really points, with 21 unit tests. Browser: 4 crafted links,
      including a backslash and a hidden tab, all landed on `/`. Sabotage, a text check only: 7 tests failed.
- [x] **T044** — "How it works" area holding the trace, RAG explorer and tools · files: `views/*` · test: browser check
      **Result (2026-11-04):** Sub-pages `/how-it-works/trace`, `/rag` and `/tools`, with the service status moved here. The trace page keeps
      the full chat beside the trace, sharing the provider, so the learning view stays after the widget arrives.

## Shop pages

- [x] **T050** — Product grid, with placeholders, ratings and Load more · files: `shop/ProductGrid.tsx` · test: browser
      check; layout shift measured
      **Result (2026-11-04):** Hairline grid, 2 then 4 columns, placeholders in the same shape, Load more to 42, then focus moves to the
      first new product. With the API delayed: CLS 0.0001 on `/shop/all`. Add to cart comes with T063. Standalone prices don't use
      tabular numerals: this font's tabular dot looks spaced out, so they're kept for columns (plan updated).
- [x] **T051** — Landing page · files: `shop/Landing.tsx` · test: browser check as a guest
      **Result (2026-11-04):** 8 tiles at 4:3, so the whole shop fits on one 1280x800 screen, then top rated. `/categories` gained `cover`,
      each category's top-rated product, so one call covers AC-5. CLS 0.0007. No carousel. Most covers aren't drawn yet, so those
      tiles are blank until T062.
- [x] **T052** — Category pages, sorting in the URL, not-found pages · files: `shop/CategoryPage.tsx` · test: browser check
      **Result (2026-11-04):** All 4 sorts checked, a sort survives a reload, and a bad `?sort=` falls back to top rated. Unknown category
      and product pages work. No sideways scroll at 390 px on any shop page.
- [x] **T053** — Product page · files: `shop/ProductPage.tsx` · test: browser check
      **Result (2026-11-04):** Sections, not tabs. CLS 0.057. Added `/policies/returns` for AC-11: a copy of the agent's file, with a test
      that fails if they differ, because a public API route would break AC-30. The wireframe's "Free returns" was untrue (a $5.99
      label, and 10% on opened electronics), so the page says "30-day returns". Browser run 40 of 40. Add to cart comes with T063.

## Cart pages

- [x] **T060** — Failing tests, then `cartLogic.ts` · files: `cart/cartLogic.ts`, `cart/cartLogic.test.ts` · test: `npm test`
      **Result (2026-11-04):** 22 tests, written first. Storage is treated as untrusted: odd entries are dropped, quantities are capped,
      and a stored price is ignored. Totals are in whole cents and match the server's.
- [x] **T061** — `useCart`, guest and signed in, merge at sign-in, cleared at logout · files: `cart/useCart.ts` · test: browser
      check, including nothing left in storage after logout
      **Result (2026-11-04):** `cart/useCart.tsx`, since it's a provider. Added `GET /products?ids=`, because a guest cart stores ids only
      and its page needs names and prices. The merge takes items out of storage before calling the server, so React's double effects
      can't repeat it. Sabotage, cleared only after the merge: Yoga Mat became 4 instead of 2, in the database. Sabotage, a signed-in
      cart kept in storage: caught after logout. A failed merge keeps the items, and the next load finishes it. Two tabs stay in step.
- [x] **T062** — Remaining illustrations, after T001 is approved · files: `web/public/products/*.svg` · test: every product
      has one, in both themes
      **Result (2026-11-04):** 34 drawn, 42 in all, 176 KB, the largest 2.6 KB. Tests failed first, 43 of them. Every product has exactly
      one drawing, and each file's light and dark tints must match the design tokens: sabotage with a wrong tint failed 1 test. All 42
      reviewed in both themes on contact sheets. Redrawn after review: mugs collided, charging pad and skillet oversized. Weakest:
      the vertical mouse, and the phone grip stand, which reads as a ring. Shop browser run still 40 of 40, CLS at most 0.062.
- [x] **T063** [P] — Cart page, with Add to cart wired to every list and product page · files: `cart/CartPage.tsx`,
      `shop/*` · test: browser check
      **Result (2026-11-04):** Cart page, and Add to cart on every list and product page, which measured as the largest control. The
      confirmation has reserved space, so nothing moves. The count ticks, except under reduced motion. Tabular numerals looked wrong
      here too, so only the staff orders table keeps them. Merge changes appear on whichever page the shopper lands on.
- [x] **T064** — Checkout page, sign-in step, your orders · files: `cart/CheckoutPage.tsx`, `views/OrdersView.tsx` ·
      test: browser check
      **Result (2026-11-04):** Review, Place order, then confirmation on the orders page. A double click still sent a second request,
      which got a 409 and did no harm, so a synchronous guard now stops it: no failed responses. Browser run 39 of 39, twice.
- [x] **T065** [P] — Staff all-orders page with Mark delivered · files: `views/OrdersView.tsx` · test: browser check
      **Result (2026-11-04):** Button only on processing and shipped orders, and only for staff. Support delivered a real bought order and
      the customer saw it change.

## Chat widget

- [x] **T070** — Chat button, bottom bar and reserved gutter, hidden in checkout · files: `chat/ChatLauncher.tsx`,
      `layout/*` · test: measure rectangles while scrolling at 390, 768, 1280 and 1440 px
      **Result (2026-11-04):** 0 overlaps over 1,287 scroll positions and 5,186 Add to cart controls in view, at 6 window sizes, clipped to
      the scrolling page. The plan's fixed bar was wrong: as sabotage it gave 105 overlaps, because controls slide under anything fixed
      over a scrolling page. So the page scrolls in `#page`, above the bar (D-013). A page too wide for the gutter gave 46. Back
      restores the scroll position. Page width is 1120 px below 1440 px, so the gutter fits a labelled button. Hidden at checkout.
- [x] **T071** — Chat panel: full screen on phones, panel on desktop, keyboard and focus, sign-in for guests · files:
      `chat/ChatPanel.tsx` · test: browser check, keyboard only
      **Result (2026-11-04):** Full screen at 390 px, with the page behind `inert`; a 400 px panel on desktop. Enter opens with focus in the
      message box; Escape and Close return focus to the button. A guest is asked to sign in and comes back to the page. Loaded on first
      use, keeping the main bundle at 342 KB, not 474 KB. On desktop the open panel covers part of the page, by design. The browser run
      caught a crash: `scrollIntoView` returns a Promise here, so an effect written as `() => el.scrollIntoView()` blanked the app.
- [x] **T072** — Page-matched starters, and the product page's questions section · files: `chat/starters.ts`,
      `shop/ProductPage.tsx` · test: each starter gets a real answer from the live agent
      **Result (2026-11-04):** 57 of 57 from the live agent: warranty and returns for 2 products in each of the 8 categories, and 5 general
      questions 5 times each, interleaved, with the terms checked. It took 4 rounds. First 32 of 37: a phone case, desk mat and card
      wallet got the lifestyle warranty, because the policies never defined electronics, and 2 starters made the agent ask for an
      order number. The policies now list the 5 electronics categories, without changing any terms, and 2 starters were reworded. After
      that: `setup` embedded 2 documents, evals 31 of 31 in 3 runs (1 new case), faithfulness 5.0, 5.0 and 4.9, refunds 60 of 60 again.
- [x] **T073** — The nudge · files: `chat/ChatNudge.tsx` · test: browser check, and rectangles as in T070
      **Result (2026-11-04):** With a controlled clock: nothing at 44 s, a click restarts the wait, and it appears after 45 quiet seconds. On a
      phone, not at 30% scrolled, and it appears after 60%. No animation, never opens the chat, dismissed for the session, never in the
      cart. It sits in the bar, or in the gutter above the button, so it can't reach an Add to cart.
- [x] **T074** — "See how this was answered" link · files: `chat/ChatPanel.tsx`, `views/*` · test: browser check
      **Result (2026-11-04):** Opens `/how-it-works/trace?turn=...` on that answer, with the chat still open on desktop. On a phone the chat
      closes, because it would cover the trace. Only offered for answers given in this visit, since reloaded history has no trace.
      All browser checks rerun on the new scrolling layout: 55, 40, 39 and 42, with no failed responses.

## Docs

- [x] **T080** — Update chapters 7 and 10, the architecture page, local setup and README, then run their Try it steps · files:
      listed in the plan · test: exercises run; diagrams and links checked
      **Result (2026-11-04):** Chapter 7 gained the shop: URLs, the two-place cart, why the page scrolls in its own region, and the chat
      widget. Chapters 9, 10 and 11 and the architecture page gained their parts, and navigation steps were corrected in chapters 1
      to 5, 8 and 11. Chapter 9, which wasn't in the plan's list, needed its counts and gained the starter story. 157 links checked, 0
      broken. All 22 diagrams rendered with the real library. 16 of 16 changed Try it steps run in a browser, including the refund
      surviving an API restart, and the chapter 10 test step. Chapter 7's step 7 was run as T070's sabotage. Chapter 7's unchanged steps
      1 to 4 weren't rerun.
- [x] **T081** — Critique pass from the design process: screenshots of each page type, in both themes, and remove anything
      that doesn't serve the brief · files: `web/src/*` · test: screenshot review
      **Result (2026-11-04):** 15 page types reviewed in both themes, and phone sheets. Removed the old colour names and the older views'
      narrower columns and larger corners. "Your orders" lost "Live from Postgres" and a Customer column showing your own name. The
      headline no longer strands "home.", and the trace panel clears the Chat button. One `h1` and a title per page, measured with
      sideways scroll over 14 pages at 4 widths: 56 checks, 0 problems. That check first passed falsely, because a URL wait matched
      `?next=/staff/orders` and it measured the sign-in page; a screenshot showed it. Contrast still passes on 25 text pairs per theme.
      Left as they are: at 390 px staff tables scroll in their own box, so Mark delivered needs a swipe, and the trace is cramped.

## Verify

- [x] **T090** — Measure LCP and CLS on a production build, keyboard run, and WCAG checks · test: recorded numbers
      **Result (2026-11-04):** Production build, 5 runs each. Desktop: LCP 0.08-0.12 s. Phone profile (4x slower CPU, 1.6 Mbps, 150 ms): LCP
      at most 1.87 s, limit 2.5 s. CLS at most 0.074, limit 0.1. About 170 KB per page, nothing fetched from other sites. axe on 21 views
      in light and dark at 1280 and 390 px, 84 runs: 9 rules failed at first: 7 real, 1 false alarm and 1 artefact. Fixed: `aria-label` on a `<p>`, heading
      order, a second banner, content outside landmarks, a name not matching its visible text, scrollable tables not focusable,
      and a 20 px link and a 40 px button. The contrast hit was axe catching the panel mid-fade. Left: a select behind the open account
      menu, which is an artefact of auditing with a menu open. 1,148 targets at least 24 px, 220 main actions at least 44 px. 25 focus
      stops, all with a 2 px outline. A whole purchase by keyboard alone worked. Added: focus moves to the content on a new page,
      except out of an open chat. Axe finds only part of WCAG, and no real screen reader was used.
- [x] **T091** — Full browser run as guest, customer, support and admin, on an upgraded database and a clean rebuild · test:
      recorded here, with failed responses listed by URL
      **Result (2026-11-04):** Clean rebuild, web with no cache, keeping the database: 9 users, 7 orders, 42 products and 24 chunks before and
      after. `setup` on an empty scratch database also worked. One story with the real agent, 17 of 17: guest shops, signs in, buys, asks
      the agent; another customer is refused; support delivers; refund requested in the chat, approved, seen by the customer; admin
      reset keeps the order; logout leaves nothing. Other checks on the rebuilt stack: 55, 40, 39 and 44. Failed responses: only the
      expected signed-out `401 GET /api/auth/me`, and `/api/auth/logout` reported as aborted. Checked 3 times, that's harmless: 204,
      session row deleted, and the old cookie gets 401.
- [x] **T092** — Confirm `git status infra` is empty, and that AWS mode returns 404 for the new routes.
      **Result (2026-11-04):** `infra/` unchanged. With accounts off, all 9 new route forms return 404 and `/health` returns 200.
- [x] **T093** — Update `specs/architecture.md`.
      **Result (2026-11-04):** New modules and contracts added, and the public routes line corrected.
- [x] **T094** — Every Definition-of-Done gate green (`specs/constitution.md`), with evals run once (D-017); record the numbers.
      **Result (2026-11-06):** `scripts/check.sh` passed: 331 backend tests, 82 frontend tests. Build passed. Evals 3 full runs, each 88 of 88
      (31 golden, 57 integration), faithfulness 5.0, 164-172 s, no failures to explain. Locally the judge is the agent's own model, and
      the 3 runs ask in the same order, so LM Studio's prompt cache makes them less independent than they look. `infra/` unchanged, so gate
      6 doesn't apply. Gates 7 and 8 rest on T091 and T080: no source file changed after 2026-11-04. Demo data clean afterwards: 7 orders,
      all owned, 42 products. Gates 1 and 5 are T095's own work.
      **Reopened (2026-11-06):** The ShopHelper Care decision (D-015) changed `warranty.md` and both prompts, so those numbers are out of date.
      On the new code: `scripts/check.sh` passes, and 1 full eval run gave 90 of 90 (33 golden, 57 integration), faithfulness 5.0. But an
      interleaved check found only 12 of 24 Care questions searched the policy, the same 4 of 8 wordings failing each round. The 2 new eval
      cases use wordings that pass, so they don't show this. Still to do: fix that, 3 eval runs, and refunds 60 of 60 again (AC-40).
      **Final result (2026-11-06):** Owner accepted the Care gap (D-016) and cut the evals to 1 run (D-017). On the final code: `scripts/check.sh`
      passed (331 backend, 82 frontend), build passed, evals 90 of 90 in 1 run (33 golden, 57 integration), faithfulness 5.0. Refunds 60 of 60,
      over 8 wordings, 2 customers and a delivered lifestyle order, interleaved, each confirmed in the database (AC-40). Starters 57 of 57
      (AC-35): the strict check said 53, and the 4 misses were complete cancellation answers ending in an offer to check an order, which
      its "asks for an order number" rule flagged. Read in full, and repeated: a false alarm. The browser run wasn't repeated: only the
      prompt, a policy and the eval script changed, no UI.
- [x] **T095** — Tick ACs in `spec.md` (Status `Implemented`), update `roadmap.md`, `memory/progress.md`,
      `memory/MEMORY.md`. Only after every gate has passed.
      **Result (2026-11-06):** All 42 criteria ticked, each traced to a finished task. Status `Implemented`, roadmap and memory updated.

## AC coverage

| AC    | Tasks            |
| ----- | ---------------- |
| AC-1  | T042, T051       |
| AC-2  | T042, T063       |
| AC-3  | T041             |
| AC-4  | T043             |
| AC-5  | T051             |
| AC-6  | T010, T012       |
| AC-7  | T052             |
| AC-8  | T011, T052       |
| AC-9  | T011, T050       |
| AC-10 | T050, T052       |
| AC-11 | T053             |
| AC-12 | T053, T063       |
| AC-13 | T011, T053       |
| AC-14 | T060, T063       |
| AC-15 | T060, T061       |
| AC-16 | T020, T021, T060, T061 |
| AC-17 | T021             |
| AC-18 | T020, T021, T061 |
| AC-19 | T064             |
| AC-20 | T022, T023       |
| AC-21 | T023, T064       |
| AC-22 | T025             |
| AC-23 | T070, T071       |
| AC-24 | T040, T071       |
| AC-25 | T070, T073       |
| AC-26 | T071             |
| AC-27 | T071             |
| AC-28 | T042             |
| AC-29 | T044, T074       |
| AC-30 | T014             |
| AC-31 | T013, T092       |
| AC-32 | T094             |
| AC-33 | T080             |
| AC-34 | T071, T081       |
| AC-35 | T072             |
| AC-36 | T072             |
| AC-37 | T073             |
| AC-38 | T030, T031       |
| AC-39 | T030, T031       |
| AC-40 | T032             |
| AC-41 | T024, T065       |
| AC-42 | T001, T003, T081 |
