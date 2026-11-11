# 032 — Fluid Glass Redesign · Implementation Plan

**Spec:** `./spec.md` · **Status:** Approved (2026-11-07: the owner asked to go straight to implementation, with a review after slice 1)

## Approach

### §1 One recipe, in tokens

All of the look lives in `web/src/index.css`, as tokens and a few named surfaces. Components use those names and never write a blur or a raw colour (AC-5).

| Surface | Paper | Blur | Used for |
| ------- | ----- | ---- | -------- |
| `glass-chrome` | 86% | Yes | Anything with page content moving behind it: navbar, menus, chat panel |
| `glass-card` | 62% | Yes | The footer and phone bar, which sit on the ground and stay on screen |
| `glass-tile` | 62% | No | Tiles and cards. The ground is already soft, so blurring it again shows nothing and costs the GPU on all 42 cards |
| `surface-solid` | 92% | No | Reading and work: lessons, tables, forms, checkout, staff pages |

The 86% comes from the spec's measurement: 85% was the lowest that passed everywhere, and 80% left little margin.

### §2 The ground

A fixed layer behind everything, as `body::before` with `z-index: -1`. `html` keeps the paper colour and `body` becomes transparent, otherwise `body`'s background hides the layer. It's soft radial gradients from cobalt, teal and amber, blurred once so there's no visible edge. It never animates.

### §3 Glass that can hold glass

An element with `backdrop-filter` becomes the backdrop for its children, so a dropdown inside a frosted navbar would have nothing to blur. The navbar's glass therefore goes on a `::before` layer, leaving the menu free to blur the real page (AC-4).

### §4 Fluid

- **Sizes:** `clamp()` tokens for titles and page gutters.
- **Page changes:** the Web Animations API on `<main>`, 220 ms, when the route changes. Keying the route would remount `Learn` and lose its state, so this animates without remounting. It doesn't run on first load, so Largest Contentful Paint isn't touched.
- **Controls:** one transition rule for colour, shadow and transform, and a small press on buttons.
- All of it sits behind `prefers-reduced-motion: no-preference`, or checks it in code.

### §5 Fallbacks

`@supports not (backdrop-filter: blur(1px))`, `prefers-reduced-transparency` and `forced-colors` make the surfaces solid, and the last two remove the ground (AC-10). These only change token values, so no component needs to know.

### §6 Slices

1. **Shell:** tokens, ground, navbar, menus, footer, phone bar, chat, page motion. **Stops for the owner's review.**
2. **Shop:** home, catalogue, product, cart, checkout.
3. **The rest:** the course, How it works, sign-in, account, staff and admin pages.

## Files

| File | Change | Purpose |
| ---- | ------ | ------- |
| `web/src/index.css` | modify | Tokens, ground, surfaces, motion, fallbacks |
| `web/src/shared/layout/*.tsx` | modify | Navbar, menus, footer, page motion |
| `web/src/features/chat/*.tsx` | modify | Launcher and panel |
| `web/src/features/shop/*`, `cart/*` | modify | Slice 2 |
| `web/src/features/learn/*`, `how-it-works/*`, `auth/*`, `staff/*` | modify | Slice 3 |
| `web/src/design.test.ts` | new | The design rules in AC-4 and AC-5 |

No new package, and no change to `src/`, `infra/`, the database or the API.

## Test Approach

| AC | Test | Type |
| -- | ---- | ---- |
| AC-1, AC-2 | Screenshots in both themes | review |
| AC-3 | Computed opacity of each reading surface | measurement |
| AC-4, AC-7, AC-8, AC-10 | Browser run with emulated media | e2e |
| AC-5 | `design.test.ts`: no blur or raw colour outside `index.css`, and the shell uses the surfaces | unit |
| AC-6 | Sideways scroll at 320, 390, 768, 1024 and 1440 px | e2e |
| AC-9 | Worst pixel behind text, with real content scrolling under the navbar | measurement |
| AC-11, AC-12 | axe, keyboard, LCP and layout shift, as in 021's T090 | measurement |
| AC-13 | A real phone, by the owner | manual |
| AC-14, AC-15 | Request hosts, `scripts/check.sh`, and the flows from 021 and 022 | e2e |

## Risks & Mitigations

- **Speed on phones can't be measured here.** Blur is limited to a few large surfaces, and AC-13 can remove it on phones.
- **Contrast depends on the ground.** A stronger ground means measuring again, so AC-9 runs per slice.
- **AC-25 from 021:** the chat button must never cover Add to cart, so the phone bar stays a layout element.
- **A blank site after `git checkout`.** Restart `web`, as in the learnings.

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Spec before code | ✅ | Spec Approved |
| II. Test-gated delivery | ✅ | `design.test.ts`, plus measurements per slice |
| III. Small dependencies | ✅ | No new package |
| IV. Memory maintained | ✅ | D-028, and learnings per slice |
| V. The model asks, code acts | ✅ | The agent isn't touched |
| VI. AWS stays the default | ✅ | No setting or infrastructure change |
| VII. Local first | ✅ | No outside calls (AC-14) |
| VIII. Built to learn | ✅ | Measured limits, and honest about what couldn't be measured |
| IX. Stream changes additive | ✅ | No stream changes |
