# 032 — Fluid Glass Redesign

**Status:** Implemented
**Roadmap phase:** Backlog · **Created:** 2026-11-07 · **Owner:** RVicky172

## Summary

ShopHelper works well but looks flat: white paper, square tiles, no depth, and only two small animations. The owner wants a fluid interface with
glassmorphism across the website. This feature gives the whole site one new look, with a soft colour ground, frosted surfaces that float above it, and
sizes and movement that flow. It changes how the site looks and moves, and nothing about what it does. Glass reduces contrast and costs speed, so
this spec sets measured limits for both, and keeps 021's accessibility and performance promises.

## Analysis

From reading `web/` and trying the look on the live site with injected CSS on 2026-11-07. No file in `web/` was changed.

- **The site is about 3,850 lines** in 42 components and 2 stylesheets. Colours are tokens in `web/src/index.css`, so most of the change can start in one
  place. Layout lives in `shared/layout/`.
- **Nothing is there for glass to show.** There's no gradient, blur or shadow today, and frosted glass over a flat page is invisible. A ground has to come first.
- **The page scrolls in `#page` (D-013),** so a glass navbar has real content sliding under it, including dark product illustrations.
- **Text on glass is the main risk,** and it depends on what's behind it:

| Surface | What's behind it | Paper opacity needed | Measured |
| ------- | ---------------- | -------------------- | -------- |
| Navbar | Products scrolling under it | **85%** | Worst case at 85%: light 5.02:1, dark 5.37:1. At 80%: 4.63:1 and 4.71:1. At 70% it fails: 3.95:1 and 3.68:1 |
| Cards and lesson panel | The colour ground only | 40% is enough | Worst case at 40%: light 5.38:1, dark 6.32:1 |

  The worst case is the lowest contrast of muted, cobalt or ink text against sampled pixels, at 1280 px on `/shop/all`, with the prototype's ground.
  It must be measured again on the real build.
- **Scroll smoothness couldn't be measured.** Headless Chrome reported 121 frames a second for every version, even with the CPU slowed 4 times, because
  it doesn't do the GPU work that blur costs. That number says nothing, so AC-13 needs a real phone.
- **The skill's rules conflict with this brief.** `design-taste-frontend` bans glass, `backdrop-filter` and CSS gradients on shop sites, and "one section
  per screen" doesn't suit an app with a catalogue, lessons and staff tables. Its finish gate can't pass on what the owner asked for (Q3).

**Direction chosen: layered glass.** Three options were considered:

| Option | Look | Verdict |
| ------ | ---- | ------- |
| Glass on the navbar, chat and menus only | Calm, but the page stays mostly flat | Too little for this brief |
| **Layered: glass on chrome and shop surfaces, nearly solid where people read or work** | Clear depth, and text stays easy to read | **Chosen** |
| Glass on everything | Strongest look | Long lessons and staff tables get harder to read, and each blurred layer costs speed |

## User Stories

- **US-1:** As a shopper, I want the shop to feel modern and calm, so that I trust it and enjoy browsing.
- **US-2:** As a shopper, I want movement that responds to what I do, so that the site feels smooth rather than abrupt.
- **US-3:** As a shopper on any screen size, I want sizes and spacing that flow, so that nothing looks squeezed or stranded.
- **US-4:** As a learner, I want lessons to stay easy to read for a long time, so that the new look never gets in the way.
- **US-5:** As a person with low vision or motion sensitivity, I want the same access as before, so that the redesign doesn't shut me out.
- **US-6:** As staff, I want tables and queues that stay plain and quick to scan, so that my work isn't slowed.

## Acceptance Criteria

### The look

- [x] **AC-1:** Every page sits on one soft colour ground, in light and dark, made from the site's own colours, with no violet or lavender in the ground
      and no visible edge or banding. _(screenshot review)_
- [x] **AC-2:** The navbar, footer, chat panel, menus, category tiles and product cards are frosted glass: what's behind them shows through, blurred. _(screenshot review)_
- [x] **AC-3:** Lesson text, tables, forms, checkout, and staff and admin pages sit on a nearly solid surface of at least 90% paper. _(measurement)_
- [x] **AC-4:** Glass is never stacked on glass: no frosted surface sits inside another. _(e2e)_
- [x] **AC-5:** One radius scale, one shadow scale and one glass recipe, all as tokens, used on every page. A test fails on a raw blur or colour outside the
      tokens. _(unit)_

### Fluid

- [x] **AC-6:** Headings, spacing and page gutters scale smoothly between 390 px and 1440 px, with no sideways scroll at 320, 390, 768, 1024 or 1440 px. _(e2e)_
- [x] **AC-7:** Moving between pages, opening the chat and opening a menu each animate in 300 ms or less, and buttons and cards answer hover and press.
      Nothing moves because the page scrolled. _(e2e)_
- [x] **AC-8:** With `prefers-reduced-motion`, all of this movement stops and nothing stays hidden. _(e2e)_

### Keeping what exists

- [x] **AC-9:** Text on every glass surface keeps at least 4.5:1 against the worst pixel behind it, in both themes, measured with real content scrolling under
      the navbar. _(measurement)_
- [x] **AC-10:** Where a browser has no `backdrop-filter`, or the user asks for reduced transparency or forced colours, surfaces become solid and stay readable. _(e2e)_
- [x] **AC-11:** Keyboard focus stays visible on every surface, is never hidden by the navbar or chat, and pointer targets stay at least 24 px, or 44 px for main
      actions. axe finds no new failures on the views 021 measured, in both themes at 1280 and 390 px. _(measurement)_
- [x] **AC-12:** On 021's phone profile, Largest Contentful Paint stays under 2.5 s and layout shift under 0.1, and the shop's main bundle grows by no more than
      5 kB compressed. _(measurement)_
- [-] **AC-13:** _(dropped 2026-11-11 by the owner, D-029: no phone check for now)_ On a real mid-range phone, scrolling the catalogue and a long lesson shows no visible stutter. If it does, blur is reduced or removed on phones. _(manual)_
- [x] **AC-14:** Everything is served from this project, with no runtime calls to other sites, and no new runtime package. _(e2e)_
- [x] **AC-15:** No API, agent or AWS behaviour changes, every existing frontend and backend test still passes, and every 021 and 022 flow still works. _(unit + e2e)_

## Non-Functional Requirements

- Performance and accessibility: as in AC-9 to AC-13. 021's limits stay in force.
- Honesty: colours and copy keep describing the same shop. No invented products, reviews or claims.
- Upkeep: glass is a small set of tokens and classes, so it can be tuned or removed in one place.

## Out of Scope

- New features, pages, routes or copy changes, beyond what the look needs.
- Replacing the product illustrations (Q2).
- Changing the API, the agent, `docs/` content or AWS.
- A manual light or dark switch. The site keeps following the device.
- Shaders, WebGL, or anything that animates the ground all the time.

## Open Questions

All answered by the owner on 2026-11-07, who accepted the proposals (D-028).

- **Q1** Which pages change? _Answer:_ the whole site, as you asked, in 3 slices: **1.** the ground, tokens, navbar, footer and chat. **2.** Home,
  catalogue, product, cart and checkout. **3.** The course, How it works, and staff and admin pages. Each slice is usable on its own, and slice 1 stops for your review
  of the look before the rest is built.
- **Q2** Keep the product illustrations, or use photographs? The skill wants real photographs and rejects drawings, but you approved these in 021.
  _Answer:_ keep them. Dark line art looks good on glass, and the shop keeps its own character. Photographs would need licensed stand-ins and credits.
- **Q3** How is the skill used, given it bans what you asked for? _Answer:_ your brief wins. Use its checker as advice, and its copy and motion
  rules where they fit. Don't arm its finish gate, which would fail on the glass itself and hold every turn open, and don't copy its kit into `public/`. The proof is this
  spec's criteria.
- **Q4** What does "fluid" mean to you? _Answer:_ both meanings: sizes that flow with the screen (AC-6), and smooth movement (AC-7).
- **Q5** The keyboards tint and the RAG trace colour are lilac and purple. Change them? _Answer:_ keep the RAG colour, which marks a tool in the
  learning views, and move the keyboards tint towards blue, so the shop has no lavender. The skill bans it, and it's a small change.
- **Q6** When does 022's T390 run? _Answer:_ after slice 3, because it measures pages this feature changes. 022 stays In Progress until then (D-026).

## Changelog

- 2026-11-07 — Created, from the owner's request and an analysis of `web/`, with contrast measured on a runtime prototype.
- 2026-11-07 — Questions answered and spec Approved.
- 2026-11-11 — AC-13 dropped by the owner (D-029). From 1280 px the page makes room beside the open chat (AC-11). Status Implemented.
