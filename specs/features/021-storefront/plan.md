# 021 — Storefront · Implementation Plan

**Spec:** `./spec.md` · **Status:** Approved

## Approach

### §1 Design system

Grounded in the subject, following the spec's design process. ShopHelper sells everyday goods across eight quite different
categories, so the look comes from **a printed store catalogue**: products on a ruled grid, each category with its own
colour, and clear prices. That's the one bold idea. Everything else stays quiet.

**Colours** (contrast measured against WCAG 2.2 AA, which needs 4.5:1 for text):

| Name | Hex | Role | Contrast |
| ---- | --- | ---- | -------- |
| Ink | `#1B2340` | Text and headings | 15.4:1 on Paper |
| Paper | `#FFFFFF` | Page | |
| Shelf | `#EFF1F6` | Quiet bands, footer | Ink 13.7:1 |
| Muted | `#566079` | Secondary text, form borders | 6.3:1 on Paper |
| Rule | `#D3D8E3` | Grid lines, decoration only | 1.4:1, so never on form fields |
| Cobalt | `#2340D9` | Actions: Add to cart, links | 7.5:1 with white |
| Marigold | `#F2B01E` | Rating stars and cart count only | Ink 8.1:1 |

Each category has a flat tint behind its illustrations: Audio `#DCE4FF`, Keyboards and mice `#E4E0FA`, Laptop accessories
`#D8EEF0`, Phone accessories `#FBE3DC`, Power and charging `#FFF0C9`, Home and kitchen `#E0F0DF`, Bags and travel `#F3E5D8`,
Fitness and outdoors `#D9F0E8`. Ink on any of them is at least 12:1.

**Dark mode** follows the device setting. Same roles, measured the same way:

| Name | Hex | Contrast |
| ---- | --- | -------- |
| Ink | `#EEF1F8` | 15.3:1 on Paper |
| Paper | `#141A2E` | |
| Shelf | `#1D2540` | Ink 13.4:1 |
| Muted | `#A9B3C9` | 8.2:1 on Paper |
| Rule | `#323B57` | Decoration only |
| Cobalt | `#8FA3FF` | Dark text on it 7.3:1; as a link 7.3:1 |
| Marigold | `#F2B01E` | 9.0:1 on Paper |

Dark category tints: Audio `#2A3563`, Keyboards and mice `#352F63`, Laptop accessories `#1F4A50`, Phone accessories `#5A3229`,
Power and charging `#574513`, Home and kitchen `#2A4A2C`, Bags and travel `#4F3B2A`, Fitness and outdoors `#1F4C3F`. Ink on any
of them is at least 8.2:1. Each SVG carries its own `prefers-color-scheme` style, which works inside an `<img>`.

Added during T003: `field` (form borders, same as Muted), `on-cobalt` and `on-marigold` (fixed text colours, because Ink flips in
dark mode), and the existing trace colours, measured the same way. Light `danger` became `#B5362F` to pass on its own tint.
Marigold stars are 1.91:1 on white, below the 3:1 for graphics, so they're decoration: the numeric rating always sits beside them.

**Type:** one family, Schibsted Grotesk, built for news and strong at both headline and small sizes. Self-hosted. Only the staff
orders table uses tabular numerals. Elsewhere prices don't, because this font's tabular dot looks spaced out. Scale: 14, 16, 20, 28, and a fluid 40-64 for one headline. It replaces Inter.

**Shape:** products sit in a grid divided by hairlines, not separate cards. No shadows on content, and square image areas.
The chat panel is the only raised surface, because it really does sit above the page. Buttons have a 4 px radius.

**Motion:** only in response to the user: the cart count ticks when an item is added, and the chat panel slides in. All of
it stops under `prefers-reduced-motion`. No scroll reveals and no hover effects on every card.

**Wording:** sentence case. "Add to cart", "Place order" and "Sign in" stay the same everywhere.

### §2 Wireframes

Landing page. The first thing on screen is the products, with no marketing hero:

```text
+--------------------------------------------------------------------------+
| ShopHelper   Shop v   How it works                  Sign in     Cart (2) |
+--------------------------------------------------------------------------+
| Everything for your desk, bag and home.                                  |
|                                                                          |
| +--------------+--------------+--------------+--------------+            |
| | [tint+art]   | [tint+art]   | [tint+art]   | [tint+art]   |  8 tiles,  |
| | Audio        | Keyboards    | Laptop       | Phone        |  4 by 2:   |
| +--------------+--------------+--------------+--------------+  the bold  |
| | Power        | Home         | Bags         | Fitness      |  moment    |
| +--------------+--------------+--------------+--------------+            |
|                                                                          |
| Top rated                                                 See all 42     |
| +-----------+-----------+-----------+-----------+                        |
| | [art]     | [art]     | [art]     | [art]     |                        |
| | Name      | Name      | Name      | Name      |                        |
| | * 4.6 (82)| * 4.4 (51)| * 4.7 (19)| * 4.2 (33)|                        |
| | $129.00   | $59.99    | $45.50    | $89.00    |                        |
| | Add to cart           ...                     |                 ( Chat ) |
+--------------------------------------------------------------------------+
```

Product page, and the chat open on desktop:

```text
+--------------------------------------------------------------------------+
| ShopHelper   Shop v   How it works                    Asha v    Cart (3) |
+--------------------------------------------------------------------------+
| Shop > Audio > Bluetooth Speaker                                         |
| +-------------------------+   Bluetooth Speaker                          |
| |                         |   * 4.5 (127)                                |
| |     [large art on       |   $89.00                                     |
| |      category tint]     |   Qty [ 1 v ]  [ Add to cart ]               |
| |                         |   30-day returns. Return policy              |
| +-------------------------+                                              |
| Description                                     +----------------------+ |
| Specifications                                  | Support          [x] | |
| Questions before you buy?                       | Hi Asha              | |
|   What's the warranty?  How do returns work?    | > What's the warranty| |
| Related products                                | [ Ask anything     ] | |
|   [art] [art] [art]                             +----------------------+ |
+--------------------------------------------------------------------------+
```

Phone. A bar along the bottom holds Chat and Cart, so nothing can sit under them (see §6):

```text
+------------------------+
| ShopHelper   Sign in   |
| [Shop v]               |
| +---------+---------+  |
| | [art]   | [art]   |  |
| | Name    | Name    |  |
| | $129.00 | $59.99  |  |
| | Add to  | Add to  |  |
| | cart    | cart    |  |
| +---------+---------+  |
+------------------------+
| ( Chat )     Cart (2)  |
+------------------------+
```

### §3 Pages and routes

Every page needs a real URL (AC-3), which tabs can't give. React Router is added for that.

| URL | Page | Who |
| --- | ---- | --- |
| `/` | Landing | Everyone |
| `/shop/:category` | Category list; `/shop/all` lists everything | Everyone |
| `/products/:slug` | Product page | Everyone |
| `/policies/returns` | Return policy, a checked copy of the agent's file (added in T053 for AC-11) | Everyone |
| `/cart` | Cart | Everyone |
| `/checkout` | Review and Place order | Signed in |
| `/signin`, `/signup` | Sign in, return to `?next=` | Everyone |
| `/account/orders` | Your orders | Signed in |
| `/staff/refunds`, `/staff/orders` | Queue, all orders | Staff |
| `/admin/users` | Users | Admin |
| `/how-it-works` | Trace, RAG explorer, tools (sub-pages) | Signed in, as today |

`next` accepts only paths starting with a single `/`, so a crafted link can't send someone to another site after sign-in.

### §4 Catalogue

`data/products.json` holds 42 products, and `setup` upserts them into a new `products` table, so they're visible in pgAdmin.
Prices live here and nowhere else. Orders' item names match products, so all 7 demo items exist (AC-6).

Public, read-only routes: `GET /categories`, `GET /products?category=&sort=&offset=&limit=`, `GET /products/{slug}`.

### §5 Cart and checkout

| | Guest | Signed in |
| --- | ----- | --------- |
| Stored in | `localStorage`: product ids and quantities only, no prices | `cart_items` table |
| Survives | Reload, closing the browser | Any browser (AC-17) |

A pure `cartLogic.ts` holds add, change and merge, so it can be unit-tested.

On sign-in the client sends its guest items to `POST /cart/merge`. The server adds quantities, caps them at 10, drops unknown
products, and returns what changed, which the UI shows (AC-16). The guest copy is then deleted. After logout nothing of the
user's cart is left, because a signed-in cart is never stored in the browser (AC-18).

`POST /checkout` reads the cart and prices **from the database** in one transaction, creates the order, and empties the cart.
It accepts no body, so a tampered price has nowhere to go (AC-20). An empty cart returns 409, so a double click can't place
two orders.

Orders keep their current shape and add `items`. `item` becomes "Wireless Mouse" or "Wireless Mouse + 2 more", and `total` is
the sum, so `get_order_status`, refund checks and the queue all keep working unchanged.

### §6 Chat button: solving AC-25

A fixed button floating over a scrolling list **must** eventually sit on top of something, so positioning alone can't meet
AC-25. The layout has to give it its own space:

- **Under 1280 px:** a full-width bottom bar holds Chat and Cart. It's a normal layout element below the scrolling page, not fixed over
  it, because anything fixed over a scrolling page has controls slide under it. The page therefore scrolls in its own region, `#page`,
  and Layout restores scroll positions on Back, which the browser only does for the window.
- **1280 px and up:** a bottom-right button sits in a gutter reserved by the page's maximum width, so content can't reach it. The
  page is 1120 px wide below 1440 px, so the gutter at 1280 px fits a labelled button.
- **The nudge** sits in the bar, or in the gutter above the button, so the same reasoning covers it.

`scroll-padding-bottom` keeps keyboard focus clear of the bar (WCAG 2.4.11). AC-25 is tested by measuring: scroll each page in
steps, and assert the button's rectangle never intersects any Add to cart control's. The nudge (AC-37) is checked the same way.

### §7 Chat across pages

`useChat` moves into a `ChatProvider` above the router, so navigation can't interrupt a stream (AC-24). It stays keyed by user
id, keeping feature 020's client-side isolation. The provider keeps each turn's trace, so "See how this was answered" opens
`/how-it-works/trace?turn=...` and the chat stays open.

The panel holds the conversation list, messages and page-matched starters. `useChatContext()` gives starters from the current
route. Starters only ask about orders or policies, because the agent doesn't know the catalogue (AC-35).

The nudge uses `sessionStorage` to appear at most once. It only starts counting on product pages, and any click, key press or
adding to the cart resets the 45 seconds (AC-37).

### §8 Public routes: changing feature 020's rules (D-011)

`PUBLIC_PATHS` is an exact list, but product pages have variable paths. `AccountsGate` gains `is_public(method, path)`, which
also allows **GET only** on `/categories` and `/products...`. The route-walking test keeps asserting that everything else
gets a 401, and adds the exact public set, so a mistake here still fails.

All new routes use `accounts_only`, so they return 404 on AWS (AC-31).

### §9 The agent and policies

- `SYSTEM_PROMPT` and `raw_agent.py` change "electronics store" to a general store (AC-38).
- `returns.md` and `warranty.md` gain the lifestyle terms (AC-39). `setup` re-embeds only those two, using the content hash.
- These change what the model sees, so the refund rate is re-measured with interleaved prompts, 60 of 60 (AC-40), and evals
  run 3 times. The same text reaches AWS on the next deploy, through the Knowledge Base.

### §10 Mark delivered

`POST /orders/{order_id}/deliver`, for support and admin, sets `status` to `delivered` and `delivered_at` to today. It's allowed
only from `processing` or `shipped`, and anything else returns 409. A Mark delivered button sits on `/staff/orders`. It exists
so a learner can buy something, deliver it and refund it, end to end.

### §11 Illustrations

42 SVGs in `web/public/products/`, flat geometric shapes in Ink on the category tint, with one consistent line weight. Hand-
written, so they're small and load offline. A list loads them lazily with fixed dimensions, so nothing jumps (AC-10). The first
8 are a spike, for you to judge before the other 34 are drawn.

## Files

| File | Change | Purpose |
| ---- | ------ | ------- |
| `src/shophelper/data/products.json` | new | 8 categories, 42 products |
| `src/shophelper/catalog.py` | new | `ProductRepo`, in-memory and Postgres |
| `src/shophelper/cart.py` | new | `CartStore`, merge and checkout rules |
| `src/shophelper/shop_api.py` | new | Catalogue, cart and checkout routes |
| `src/shophelper/schema.sql` | modify | `products`, `cart_items` |
| `src/shophelper/auth_api.py` | modify | `is_public` |
| `src/shophelper/orders.py` | modify | Create an order from a cart |
| `src/shophelper/setup_local.py` | modify | Seed the catalogue |
| `src/shophelper/graph.py`, `raw_agent.py` | modify | General store wording |
| `knowledge/policies/returns.md`, `warranty.md` | modify | Lifestyle terms |
| `web/src/index.css` | rewrite | Design tokens |
| `web/src/App.tsx` | rewrite | Routes and layout |
| `web/src/layout/*` | new | Navbar, account menu, footer, bottom bar |
| `web/src/shop/*` | new | Landing, category, product, product grid |
| `web/src/cart/*` | new | `cartLogic.ts` with tests, `useCart`, cart and checkout pages |
| `web/src/chat/ChatProvider.tsx`, `ChatPanel.tsx`, `ChatLauncher.tsx`, `starters.ts` | new | Chat as a widget |
| `web/src/views/*` | modify | Move existing pages under the new layout |
| `web/public/products/*.svg` | new | 42 illustrations |
| `tests/test_shop.py` | new | Catalogue, cart, checkout |
| `tests/test_isolation.py` | modify | The new public set |
| `evals/golden_cases.yaml`, `evals/test_integration.py` | modify | Lifestyle cases, Postgres cart and checkout |
| `docs/learn/07-frontend.md`, `docs/learn/10-*.md`, `docs/architecture.md`, `docs/local-setup.md`, `README.md` | modify | The shop |
| `specs/architecture.md`, `specs/tech-stack.md` | modify | New contracts and packages |

## Data Structures & Interfaces

```sql
products   (id, slug UNIQUE, category, name, price NUMERIC(10,2), description, specs JSONB, rating, rating_count, added_at)
cart_items (user_id, product_id, quantity CHECK (quantity BETWEEN 1 AND 10), PRIMARY KEY (user_id, product_id))
```

```text
GET  /categories                                   public
GET  /products?category=&sort=&offset=&limit=12    public; sort = price_asc | price_desc | rating | newest
GET  /products?ids=1&ids=2                         public; a guest cart's products, at most 100 (added in T061)
GET  /products/{slug}                              public; includes related products
GET  /cart                                         signed in
PUT  /cart/{product_id}   {quantity}               signed in; 0 removes it
POST /cart/merge          {items}                  signed in; returns cart and changes
POST /checkout                                     signed in; no body; returns the order
```

## Techniques

- **Prices are never trusted from the client:** the browser sends only ids and quantities.
- **Sorting from an allowlist:** `sort` maps to fixed SQL, so it can't inject.
- **Sort in the URL:** `?sort=` survives a reload and can be shared (AC-8).
- **Performance:** route-level code splitting keeps the "How it works" pages out of the landing bundle. LCP and CLS are measured
  from a production build in a real browser.
- **Fonts:** bundled with `@fontsource-variable`, so there are no calls to Google (Constitution VII).

## Test Approach

| AC | Test | Type |
| -- | ---- | ---- |
| AC-1 to AC-5, AC-7 to AC-14, AC-19, AC-21 | Browser run | manual e2e |
| AC-6, AC-17 | `evals/test_integration.py` | integration |
| AC-15, AC-16 | `cartLogic.test.ts`, `tests/test_shop.py`, browser run | unit + e2e |
| AC-18, AC-20 | `tests/test_shop.py`, sabotage; browser run for logout | unit + e2e |
| AC-22 | `tests/test_shop.py`, and a live cross-user check | unit + e2e |
| AC-23, AC-24, AC-26, AC-27 | Browser run | manual e2e |
| AC-25 | Browser run, measuring rectangles while scrolling, 390 to 1440 px | measurement |
| AC-28, AC-29, AC-33 | Browser run; Try it steps | manual |
| AC-30, AC-31 | `tests/test_isolation.py`, `tests/test_local_stack.py` | unit |
| AC-32, AC-38, AC-39 | `scripts/evals_local.sh`, 3 runs | e2e |
| AC-34 to AC-37 | Browser run and screenshot review | manual e2e |
| AC-40 | Interleaved measurement, 60 attempts | measurement |
| AC-41 | `tests/test_shop.py`, sabotage; browser run | unit + e2e |
| AC-42 | Contrast script on both palettes; screenshots of each page type in both themes | measurement |
| NFRs | Contrast script, keyboard run, LCP and CLS in a production build | measurement |

UI checks stay manual: the owner again chose not to add browser tests (D-012), to keep building and learning. The accepted
cost is that UI regressions aren't caught automatically. Server rules are still covered by automated tests.

## Risks & Mitigations

- **Illustration quality.** Hand-written SVGs could look amateur, which would undercut the whole design. Spike: 8 illustrations,
  reviewed by you first. Fallback: simpler icons on the tints, or photos.
- **Moving the chat could break streaming.** `ChatProvider` moves first, with the old layout intact, and the browser run proves
  a stream survives navigation before anything else changes.
- **The prompt change could bring back false refund promises.** Re-measured under AC-40, and the code check stays regardless.
- **A public route too wide.** `is_public` is GET-only with an exact test of the public set, plus a sabotage check.
- **Size.** This is larger than feature 020 on the frontend. Each stage leaves the app working.
- **The new image needs no new Python packages,** so the slow PyPI route shouldn't matter. Only npm packages are added.

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Spec before code | ✅ | Spec Approved on 2026-11-04 |
| II. Test-gated delivery | ✅ | Every AC has a test or measurement |
| III. Small dependencies | ✅ | Two npm packages, justified below, approved by the owner (D-012) |
| IV. Memory maintained | ✅ | D-011 logged; package decision logged on approval |
| V. The model asks, code acts | ✅ | Checkout is user-driven, and the agent gets no new powers |
| VI. AWS stays the default | ⚠️ | New routes return 404 on AWS. The prompt and two policies are shared, so AWS gets those on its next deploy, untested on Claude |
| VII. Local first | ✅ | Fonts and images ship with the project |
| VIII. Built to learn | ✅ | How it works stays, and the docs are updated |
| IX. Stream changes additive | ✅ | No stream change |

### Proposed packages

| Package | Why | Size | Licence | Alternative rejected |
| ------- | --- | ---- | ------- | -------------------- |
| `react-router` | Real URLs, back button, shared links (AC-3) | Tree-shaken in the bundle | MIT | Hand-written routing: more bug-prone, and teaches less |
| `@fontsource-variable/schibsted-grotesk` | Self-hosted type | About 160 KB unpacked | OFL 1.1 | Google Fonts: a runtime call to another site, which breaks Constitution VII |
