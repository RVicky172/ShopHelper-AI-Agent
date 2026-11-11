# 032 — Fluid Glass Redesign · Tasks

**Plan:** `./plan.md`
When a task is done, tick it and add an indented **Result (YYYY-MM-DD):** note.

# Slice 1 — Shell

- [x] **T001** — Failing design rules: no blur or raw colour outside `index.css`, and the shell uses the named surfaces · files: `web/src/design.test.ts`
      **Result (2026-11-07):** 8 tests in `design.test.ts`. 6 failed first. The other 2 guard against blur and raw colours outside `index.css`, which didn't exist yet.
- [x] **T002** — Tokens, ground, surfaces, fluid sizes, fallbacks, and the keyboards tint · files: `web/src/index.css` · test: T001, screenshots
      **Result (2026-11-07):** All in `index.css`. Ground softened from the prototype, so text directly on it passes: worst 4.58:1 light, 4.88:1 dark. Five illustrations had the keyboards tint built in, which `test_catalog.py` caught, so they changed too.
- [x] **T003** — Navbar and menus on glass · files: `web/src/shared/layout/` · test: T001, a dropdown blurs the page behind it
      **Result (2026-11-07):** Floating navbar from 1024 px. Its glass is on a layer, so the dropdown really blurs the page: computed `blur(16px)`, and no stacked glass.
- [x] **T004** — Footer, phone bar and chat on glass · files: `web/src/shared/layout/Layout.tsx`, `web/src/features/chat/` · test: T001, AC-25 still holds
      **Result (2026-11-07):** All on glass. AC-25 holds: 0 overlaps at 1280 and 1440 px.
- [x] **T005** — Page and control motion · files: `web/src/shared/layout/Layout.tsx`, `web/src/index.css` · test: browser run, with and without reduced motion
      **Result (2026-11-07):** 220 ms on each page change, recorded as it starts. None on first load, and none with reduced motion. Controls ease over 160 ms, and buttons press.
- [x] **T006** — Measure slice 1: contrast (AC-9), fallbacks (AC-10), sideways scroll (AC-6), bundle size (AC-12) · test: recorded numbers
      **Result (2026-11-07):** Worst contrast, light and dark: navbar 4.94 and 5.19, menu 4.94 and 5.20, chat 5.11 and 5.83, footer 6.00 and 6.85. No sideways scroll at 5 widths on 6 pages. Reduced transparency and forced colours go solid. `@supports` couldn't be emulated, so it's unproven. Main JS 343.06 to 343.63 kB, and `index.css` source about 1.1 kB more compressed. The rest of AC-12 and speed on a phone wait for T290 and T291.
- [x] **T007** — **Stop for the owner's review of the look.** Record changes before more is built · test: owner's approval
      **Result (2026-11-07):** Owner approved carrying on, with no changes to the look.

# Slice 2 — Shop

- [x] **T101** — Home: category tiles and top rated
      **Result (2026-11-07):** Glass tiles framing each illustration, with placeholders on the same shape.
- [x] **T102** — Catalogue and product cards
      **Result (2026-11-07):** Cards on `glass-tile`, which has no blur: the ground is already soft, so blurring it showed nothing and would have cost the GPU on 42 cards. The catalogue has 1 blurred element plus the navbar's layer. Cards lift 2 px on hover, and not with reduced motion.
- [x] **T103** — Product page
      **Result (2026-11-07):** Buy box on glass. Description, specifications and questions on nearly solid panels, at 92%.
- [x] **T104** — Cart and checkout, on nearly solid surfaces
      **Result (2026-11-07):** Both on `surface-solid`. Flow run signed in as Asha: add, cart, checkout, remove. No order was placed, and the cart ended empty, as it began.
- [x] **T105** — Slice 2 measurements and browser run
      **Result (2026-11-07):** Worst text contrast on any shop surface 5.82:1 light and 6.77:1 dark, at 1440 and 390 px. Layout shift with products delayed 500 ms: 0.0000 and 0.0002 in the dev build. No sideways scroll at 5 widths on 6 pages. AC-25 holds, with 0 overlaps. No page errors.

# Slice 3 — The rest

- [x] **T201** — The course: lesson surface, stepper and question bank
      **Result (2026-11-07):** Lessons on a 92% panel, stage cards and the stepper on glass tiles. Fixed an older bug: the stepper stuck at `top-4` and slid under the navbar. It now sits 26 px clear. Mark as done, search, diagrams, the bank and Continue all still work.
- [x] **T202** — How it works and its trace views
      **Result (2026-11-07):** Status bar on glass, and panels on `surface-solid`. Also fixed `divide-line`, a colour token that never existed.
- [x] **T203** — Sign-in, account and orders
      **Result (2026-11-07):** On `surface-solid`, with fields and buttons on the shared radius.
- [x] **T204** — Staff and admin pages
      **Result (2026-11-07):** Tables and queues on `surface-solid`, checked at 92% as admin.
- [x] **T205** — Slice 3 measurements and browser run
      **Result (2026-11-07):** 14 pages as guest, customer, support and admin: no page errors, no failed requests, and no sideways scroll at 320, 390, 768, 1024 and 1440 px, with both themes at 390 and 1440. Worst text contrast 4.82:1 light, on the How it works bar, and 6.65:1 dark. New design rules fail on any old flat panel, button or field.

## Verify

- [x] **T290** — axe, keyboard, LCP and layout shift on a production build (AC-11, AC-12), then 022's T390
      **Result (2026-11-11):** Phone profile, 5 runs a page: shop LCP 1.42-1.91 s, course 2.07-2.35 s, layout shift at most 0.018, only this site's
      host. Main bundle +1.5 kB compressed over pre-032. axe: 84 runs, no failures. 771 targets at least 24 px, 92 main actions at least 44 px,
      1,192 focus stops all visible and uncovered. Fixed on the way: catalogue shift 0.11 (sort control wrapped late), lessons over 2.5 s (sign-in
      check now preloaded, first screen rendered first, stylesheet no longer fetched twice), 18 px breadcrumb links, and focus reaching what the
      open chat covers (launcher inert, page makes room beside the panel from 1280 px). 022's T390 stays in the backlog (D-026).
- [-] **T291** — Real phone check by the owner (AC-13)
      **Dropped (2026-11-11, D-029):** owner's call, no phone check for now.
- [x] **T292** — Request hosts, and every 021 and 022 flow (AC-14, AC-15)
      **Result (2026-11-11):** From T290's runs: only `localhost` contacted, and 21 views in 4 roles (shop, cart, checkout, orders, staff,
      admin, course, How it works, chat) loaded with no errors. No change to `package.json`, the API or infra since 032 started. `scripts/check.sh`
      passes: 396 backend and 128 frontend tests.
- [x] **T293** — Update `specs/architecture.md`, tick the criteria, update `roadmap.md` and `memory/`
      **Result (2026-11-11):** Done. 032 is Implemented, with AC-13 dropped.

## AC coverage

| AC | Tasks |
| -- | ----- |
| AC-1 | T002 |
| AC-2 | T003, T004, T101, T102 |
| AC-3 | T104, T201, T204 |
| AC-4 | T003, T006 |
| AC-5 | T001 |
| AC-6 | T002, T006, T105, T205 |
| AC-7 | T005 |
| AC-8 | T005 |
| AC-9 | T006, T105, T205 |
| AC-10 | T002, T006 |
| AC-11 | T290 |
| AC-12 | T006, T290 |
| AC-13 | T291 |
| AC-14 | T292 |
| AC-15 | T292 |
