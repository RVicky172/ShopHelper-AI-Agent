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

- [ ] **T101** — Home: category tiles and top rated
- [ ] **T102** — Catalogue and product cards
- [ ] **T103** — Product page
- [ ] **T104** — Cart and checkout, on nearly solid surfaces
- [ ] **T105** — Slice 2 measurements and browser run

# Slice 3 — The rest

- [ ] **T201** — The course: lesson surface, stepper and question bank
- [ ] **T202** — How it works and its trace views
- [ ] **T203** — Sign-in, account and orders
- [ ] **T204** — Staff and admin pages
- [ ] **T205** — Slice 3 measurements and browser run

## Verify

- [ ] **T290** — axe, keyboard, LCP and layout shift on a production build (AC-11, AC-12), then 022's T390
- [ ] **T291** — Real phone check by the owner (AC-13)
- [ ] **T292** — Request hosts, and every 021 and 022 flow (AC-14, AC-15)
- [ ] **T293** — Update `specs/architecture.md`, tick the criteria, update `roadmap.md` and `memory/`

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
