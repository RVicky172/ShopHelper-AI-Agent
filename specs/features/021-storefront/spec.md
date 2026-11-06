# 021 — Storefront

**Status:** Implemented
**Roadmap phase:** 2 · **Created:** 2026-11-04 · **Owner:** RVicky172

## Summary

ShopHelper is a support tool for a store that doesn't visibly exist: you log in to a dashboard of tabs. This feature
turns it into a real shop. Anyone who opens the site lands on products, can browse categories, read a product page and
fill a cart, and only signs in when it matters. A chat button at the bottom of every page opens the support agent. For
a learning project this matters because the agent finally has a real job: helping with orders that a person actually
placed, in the place where they would really ask.

## User Stories

- **US-1:** As a visitor, I want to see products as soon as the site opens, so that I don't have to log in to look around.
- **US-2:** As a visitor, I want to browse by category, sort, and open a product, so that I can find what I want.
- **US-3:** As a shopper, I want a cart that keeps my items, so that I can decide before buying.
- **US-4:** As a shopper, I want my cart to survive signing in, so that I never lose what I picked.
- **US-5:** As a customer, I want to ask for help from any page, so that I don't have to leave what I'm doing.
- **US-6:** As a staff member, I want my queue and tools easy to reach, so that the shop doesn't get in my way.
- **US-7:** As a learner, I want to still see how the agent works, so that the shop doesn't hide what this project teaches.

## Acceptance Criteria

### Landing and navigation

- [x] **AC-1:** Given a signed-out visitor, when they open `/`, then they see products with no login page and no
      redirect. _(e2e)_
- [x] **AC-2:** The navbar appears on every page, with the logo, categories, a cart icon showing the item count in the
      upper right, and a Sign in link. Once signed in, Sign in becomes an account menu with the user's name. _(e2e)_
- [x] **AC-3:** Every page has its own URL, so the back button, reload and a shared link all work. _(e2e)_
- [x] **AC-4:** Sign in and sign-up return the user to the page they were on, not to a fixed page. _(e2e)_
- [x] **AC-5:** The landing page shows at least one product from every category, and uses no auto-rotating carousel.
      _(e2e)_

### Categories and product list

- [x] **AC-6:** The catalogue has at least 8 categories and at least 40 products: electronics and lifestyle. Each product has
      a name, price, category, description, specifications, rating and rating count. All 7 demo order items are real
      products. _(integration)_
- [x] **AC-7:** Each category has its own page, listing only its products and showing the total product count. _(e2e)_
- [x] **AC-8:** Products can be sorted by price (both ways), rating and newest. The choice survives a reload. _(e2e)_
- [x] **AC-9:** A list shows at most 12 products, then a Load more button. Each item shows image, name, price, rating
      and rating count, and has an Add to cart control. _(e2e)_
- [x] **AC-10:** While products load, placeholders hold their space, so the page doesn't jump. An unknown category or
      product shows a helpful not-found page. _(e2e)_

### Product page

- [x] **AC-11:** Each product has a page with its images, price, rating, description and specifications, in sections
      rather than horizontal tabs, plus a link to the return policy. _(e2e)_
- [x] **AC-12:** Add to cart is the single most prominent control on the page, with a quantity choice from 1 to 10. After
      adding, the cart count updates and the page confirms it without leaving. _(e2e)_
- [x] **AC-13:** A product page shows at least 3 related products from the same category. _(e2e)_

### Cart

- [x] **AC-14:** A cart page lists each item with quantity and line total, plus the order total. Quantity can be changed
      from 1 to 10, and an item can be removed. An empty cart invites the shopper back to the products. _(e2e)_
- [x] **AC-15:** A guest's cart survives a page reload and closing the browser. _(e2e)_
- [x] **AC-16:** When a guest signs in, their items merge into the account's cart, adding quantities (up to 10) for items
      in both, with nothing dropped silently. If anything changed, the shopper is told. _(unit + e2e)_
- [x] **AC-17:** A signed-in cart follows the user to another browser. _(integration)_
- [x] **AC-18:** A cart belongs to one user. Nobody can read or change another user's cart, and after logout no cart
      contents remain on the page or in browser storage. _(unit + e2e)_

### Checkout

- [x] **AC-19:** A signed-in customer can place an order from the cart, with no payment step. A guest is asked to sign in
      first, and returns to the cart. _(e2e)_
- [x] **AC-20:** The order total comes from the server's prices. A request that sends its own price or total changes
      nothing. _(unit)_
- [x] **AC-21:** A placed order empties the cart, belongs to that customer, and appears under their orders. _(e2e)_
- [x] **AC-22:** The agent can answer about that new order, and another customer can't reach it. _(e2e)_

### Chat button

- [x] **AC-23:** A chat button appears at the bottom of every page and opens the support chat over the page, without
      leaving it. It's hidden during checkout. _(e2e)_
- [x] **AC-24:** The chat keeps its conversation, and any answer still streaming, when the shopper moves between pages.
      _(e2e)_
- [x] **AC-25:** The button never covers an Add to cart control, at 390 px wide or on desktop, at any scroll position.
      _(e2e, checked by measuring both elements)_
- [x] **AC-26:** The chat opens and closes with the keyboard, Escape closes it, and focus returns to the button.
      _(e2e)_
- [x] **AC-27:** A signed-out visitor who opens the chat is asked to sign in and comes back to the same page. _(e2e)_
- [x] **AC-34:** The chat looks like part of the shop: same colours, typefaces and wording, with no default widget styling.
      On phones it opens full screen. On desktop it's a panel that leaves the page visible. _(e2e + screenshot review)_
- [x] **AC-35:** An empty chat offers 2 or 3 starter questions matched to the page: returns and warranty on a product page,
      order help on the orders page, delivery and returns in the cart. Every starter is one the agent can really answer
      from orders or policies. _(e2e)_
- [x] **AC-36:** A product page has a short "Questions before you buy?" section with the same kind of starters. Choosing one
      opens the chat with that question sent. _(e2e)_
- [x] **AC-37:** A quiet text nudge appears beside the chat button at most once per browser session: on a product page,
      after 45 seconds with no action, or after scrolling 60% of the page on a phone. It never pulses, never opens the chat
      by itself, never appears in the cart or checkout, can be dismissed, and stays away once dismissed. It also obeys
      AC-25. _(e2e)_

### Keeping what exists

- [x] **AC-28:** Staff reach the refund queue, and admins reach users, from the account menu. Their rules don't change.
      _(e2e)_
- [x] **AC-29:** A "How it works" area in the navbar holds the step trace, RAG explorer and tools. The chat has a "See how
      this was answered" link that opens the trace for that answer. _(e2e)_
- [x] **AC-30:** Product and category reads are public. Every other route still needs a session, and the route-walking
      test is updated to prove it. _(unit)_
- [x] **AC-31:** With accounts off (AWS), all the new routes return 404, and `test_defaults_are_the_aws_path` passes.
      _(unit)_
- [x] **AC-32:** All 33 evals and the integration tests still pass. _(e2e)_
- [x] **AC-38:** The agent treats this as a general store, not an electronics store, so a question about a lifestyle order
      isn't declined as off-topic. At least 2 new eval cases cover it. _(e2e)_
- [x] **AC-39:** The returns and warranty policies say what applies to lifestyle products: 30-day returns with no restocking
      fee, and a 90-day warranty against defects. The agent answers both from the policies. The warranty policy also says
      ShopHelper Care is for electronics only. 030 made the agent answer that reliably. _(e2e)_
- [x] **AC-40:** After the prompt and policy changes, refund requests still submit in at least 60 of 60 interleaved attempts.
      _(measurement)_
- [x] **AC-41:** Staff can mark a processing or shipped order as delivered from the all-orders page, which sets its delivery
      date to today, so a bought order can be refunded. Customers can't, and a delivered, cancelled or refunded order
      can't be marked. _(unit + e2e)_
- [x] **AC-42:** The whole site works in light and dark, following the device setting, with the contrast required above in
      both, including illustrations and category colours. _(measurement + screenshot review)_
- [x] **AC-33:** `docs/learn/07-frontend.md`, the README and `docs/architecture.md` describe the shop, and their Try it
      steps were run. _(manual)_

## Non-Functional Requirements

- Accessibility, WCAG 2.2 AA: text contrast of at least 4.5:1, visible keyboard focus, focus never fully hidden by the
  navbar or chat, pointer targets of at least 24 px (44 px for main actions), and `prefers-reduced-motion` respected.
- Performance, measured on the local build: Largest Contentful Paint under 2.5 s, Cumulative Layout Shift under 0.1.
- Responsive from 390 px to 1440 px, with no sideways scroll.
- Local first: images and fonts are served from this project, with no runtime calls to other sites (Constitution VII).

## Design Direction

The design combines two sources, by the owner's choice:

| Source | Decides | Used from it |
| ------ | ------- | ------------ |
| Anthropic `frontend-design` skill | How the whole site looks and moves | The process and rules below |
| Alhena: chat widget design | How the chat behaves | Page-specific rules, page-matched wording, brand match, product-page block, mobile rules, nudges |

**When they disagree, restraint wins.** Alhena suggests pulsing the chat button after 45 seconds. Anthropic says to use
unprompted motion sparingly. So the nudge is one quiet line of text, with no pulsing (AC-37).

Not used from Alhena: event tracking to outside analytics (Constitution VII), an inline chat on help pages (the shop has
none), and two nudges per session (one is enough). Its conversion figures are vendor claims and weren't relied on. Its
45-second and 60% thresholds are the author's opinion, so they're starting values, not proven numbers.

The plan must follow this process, adapted from Anthropic's `frontend-design` skill, and be reviewed before any UI code:

1. Ground the look in the subject: an electronics store, its customers and its products.
2. Write a compact design system: 4-6 named colours, typefaces and their roles, and wireframes of the key pages.
3. Check that plan against the brief, and replace anything that reads as a generic default.
4. Build, then critique with screenshots, and remove anything that doesn't serve the brief.

Rules taken from the research:

- Put boldness in one place, and keep the rest quiet.
- Avoid the common AI look: identical rounded cards with soft shadows, gradient washes, cream with terracotta, and
  near-black with one acid accent. The current app's Inter font and uniform cards should be reconsidered.
- Motion is for feedback on what the user did, plus at most one deliberate moment. No fade-in on every section.
- Plain, sentence-case wording. Actions keep one name throughout: "Add to cart" everywhere.

Sources: [frontend-design skill](https://github.com/anthropics/skills/tree/main/skills/frontend-design),
[Baymard: 35 best practices](https://baymard.com/blog/ecommerce-ux-best-practices),
[Baymard: Product Page UX 2026](https://baymard.com/research-articles/current-state-ecommerce-product-page-ux),
[Baymard: avoid horizontal tabs](https://baymard.com/blog/avoid-horizontal-tabs),
[WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[commercetools: cart merges](https://docs.commercetools.com/learning-implement-carts-and-shopping-lists/implement-carts/manage-cart-sessions-and-merges),
[Business Bloomer: WooCommerce cart merge](https://www.businessbloomer.com/woocommerce-cart-merge-sessions-changes/?mtke=488),
[Alhena: chat widget design](https://alhena.ai/blog/chat-widget-design-ecommerce-conversions/).
Most of Baymard's detail is paid, so its free guidance was used. Figures from vendors weren't relied on.

## Out of Scope

- Real payments, addresses, shipping costs, stock levels and tax.
- Search. With about 40 products, categories and sorting are enough for now. Baymard recommends prominent search, so it
  goes in the backlog.
- Writing reviews, wishlists, discounts and filters beyond category.
- Size and colour choices. Lifestyle products are picked so that none needs them, such as clothing or shoes.
- Teaching the agent about the catalogue (for example "do you sell USB-C hubs?"). That's a good next feature: a new
  read-only MCP tool. For now it knows orders and policies only.
- Hosting the shop on AWS. With accounts off, the shop doesn't exist there.

## Open Questions

All answered by the owner on 2026-11-04:

- **Q1** The cart leads to a simple Place order button. No payment gateway.
- **Q2** Signed-out visitors are asked to sign in before using the chat.
- **Q3** Product images are simple illustrations stored in the repo, one per product.
- **Q4** A "How it works" area in the navbar holds the learning tools.
- **Q5** Feature 020 was closed first. This feature then changes two of its rules openly (D-011): signed-out visitors can
  see the shop (020 AC-22), and product and category reads are public (020 AC-8).
- **Q6** Categories: Audio, Keyboards and mice, Laptop accessories, Phone accessories, Power and charging, plus lifestyle
  products, like Amazon: Home and kitchen, Bags and travel, Fitness and outdoors.

The owner approved the lifestyle categories and the policy terms in AC-39 on 2026-11-04.

## Changelog

- 2026-11-04 — Created. Scope includes the owner's update: products as the landing page, login in the navbar, product
  list and product pages, design based on web research.
- 2026-11-04 — Owner chose to combine Anthropic's `frontend-design` skill and Alhena's chat widget design. Added AC-34 to
  AC-37 and the rule for resolving conflicts between them.
- 2026-11-04 — Questions answered and spec Approved. Lifestyle products added, with AC-38 to AC-40.
- 2026-11-04 — Plan review: added AC-41 (mark delivered) and AC-42 (light and dark). Lifestyle choices approved.
- 2026-11-06 — Owner decided ShopHelper Care is for electronics only (D-015), added to AC-39. The trace page keeps its chat, as built.
- 2026-11-06 — All 42 criteria proven, status Implemented.
- 2026-11-06 — Owner cut the evals to 1 run by default, with `EVAL_RUNS` to repeat them (D-017).
- 2026-11-06 — Owner accepted a known gap (D-016): AC-39 no longer claims the agent answers Care questions. AC-32's count updated to 33.
