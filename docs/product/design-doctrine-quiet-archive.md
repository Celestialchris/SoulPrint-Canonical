# Quiet Archive — SoulPrint Design Doctrine v3

**Status:** Active (since v0.7.0-alpha.1). Supersedes Magenta Sanctum v2 (`docs/archive/design-doctrine-magenta-sanctum.md` — retired).

**Precedence rule:** If any committed doc contradicts this file, this file wins. If this file contradicts `src/app/static/app.css`, the CSS wins — live code is always the final authority.

**Audience:** Human (Chris), AI coding agents (Claude Code), future contributors. Every UI-touching session must read this before editing templates or CSS.

---

## 1. Core truth

SoulPrint is a **quiet archive** — a warm, intimate, lived-in place where a person keeps the record of their thinking. Not a utility. Not a showroom. Not a dashboard. A room with a lamp on, the floorboards worn smooth where people walk, and everything where the owner left it.

The Magenta Sanctum phase was correct to reject the flat-utility aesthetic, but its pink accent read as loud, consumer, and generic — nightclub signage pointing at journal pages. Quiet Archive keeps the editorial restraint and dark canvas, and replaces pink with the colors of a warm interior: clay, warm black, cream, and a single gold identity glow on the wordmark.

## 2. Design law

> **Glow for identity, flatness for usage.**

Identity surfaces carry warmth and presence: the wordmark, the hero greeting, empty states, the landing page, summary / wrapped. These surfaces earn tone — ember glow, gold leaf, serif display, generous negative space.

Usage surfaces stay flat: conversation rows, message lists, stats, provider lists, search results, traces. Hairline dividers, mono labels, tabular nums, no cards wrapping rows, no shadows. Identical to Magenta Sanctum and USB Drive on this point — the law doesn't change when colors do.

If a design decision drifts into decoration-on-data or utility-on-identity, it's wrong.

---

## 3. Color tokens

### Brand — clay accent

| Token | Value (dark) | Value (light) | Use |
|---|---|---|---|
| `--accent` | `#A25B47` | `#8E4F3E` | Active rail icon, active sidebar item text, CTA fill, CTA border, focus rings, `.highlight` inline spans |
| `--accent-dim` | `#8E5748` | `#6F3D30` | CTA hover, focused input border |
| `--accent-soft` | `rgba(162,91,71,0.12)` | `rgba(142,79,62,0.12)` | Active sidebar item background, selection tint |
| `--accent-glow` | `rgba(162,91,71,0.05)` | `rgba(142,79,62,0.05)` | Ambient warm glow (applied selectively on identity surfaces only) |

### Wordmark — gold identity

| Token | Value (dark) | Value (light) | Use |
|---|---|---|---|
| `--wordmark-gold` | `#E7C98A` | `#B08A3E` | Landing-page wordmark, and any identity-surface rendering of "SoulPrint" |
| `--wordmark-glow` | `rgba(231,201,138,0.28)` | `rgba(176,138,62,0.22)` | Torchlit ember glow around the wordmark (recipe finalized in Phase 2) |

**App-shell wordmark recipe (Phase 2):** overrides the gold with the Torchlit Vault orange-red text-shadow. Left-column shell wordmark reads as ember; right-column landing/hero wordmark reads as gold. Phase 1 does not implement this split — the tokens exist, their usage arrives in Phase 2.

### Secondary — green presence

| Token | Value (dark) | Value (light) | Use |
|---|---|---|---|
| `--green` | `#4ade80` | `#16a34a` | "local-first" status dot, sidebar footer status |

Green is not brand. Green means "alive, local, present." Only deploy on status indicators that communicate one of those three concepts.

### Background scale — warm parchment, five levels

| Token | Value (dark) | Value (light) | Use |
|---|---|---|---|
| `--bg-darkest` | `#0F0D0B` | `#F4EFE5` | Rail background, search input background, body canvas |
| `--bg-dark` | `#151210` | `#ECE6D9` | Sidebar background, stat cards, context panel, row hover |
| `--bg-mid` | `#1B1714` | `#FFFFFF` | Main content area |
| `--bg-light` | `#26211D` | `#E4DECF` | Default rail icon, context tags, `⌘K` kbd chip |
| `--bg-hover` | `#2E2823` | `#DCD6C7` | Sidebar item hover, ghost button hover |

Legacy aliases `--bg`, `--surface`, `--raised` remain defined (mapped to `--bg-darkest` / `--bg-dark` / `--bg-mid`) for selectors that still use them during the phased migration.

### Provider lanes — Quiet Archive palette

| Provider | Value (dark) | Value (light) | Inspiration |
|---|---|---|---|
| `--lane-chatgpt` | `#23955D` | `#1C7A4C` | Deeper, less-neon OpenAI green |
| `--lane-claude` | `#C69224` | `#A7791E` | Anthropic gold, warmer |
| `--lane-gemini` | `#2D6FE8` | `#235FCC` | Google blue, slightly desaturated |
| `--lane-native` | `#2D6FE8` | `#235FCC` | Matches gemini for now |
| `--lane-grok` | `#6F47E6` | `#5B3BC0` | xAI violet (dormant) |

Lane colors mark data identity, not brand. They also appear muted enough to not compete with the clay accent on hover/active states.

### Text hierarchy — warm cream on warm black

| Token | Value (dark) | Value (light) | Use |
|---|---|---|---|
| `--t1` | `rgba(244,238,229,0.92)` | `rgba(26,22,18,0.92)` | Primary body |
| `--t2` | `rgba(244,238,229,0.62)` | `rgba(26,22,18,0.62)` | Secondary / descriptions |
| `--t3` | `rgba(244,238,229,0.34)` | `rgba(26,22,18,0.34)` | Mono labels, small caps, metadata |
| `--t4` | `rgba(244,238,229,0.16)` | `rgba(26,22,18,0.16)` | Disabled, decorative lines |

Base dark-theme color is warm cream `rgba(244,238,229,*)` — not pure white. The 4-point difference from Magenta Sanctum's `rgba(250,250,250,*)` is small on any single element but cumulatively gives the shell a candlelit rather than screen-lit feeling.

### Lines — two strengths

| Token | Value (dark) | Value (light) | Use |
|---|---|---|---|
| `--line` | `rgba(244,238,229,0.08)` | `rgba(26,22,18,0.08)` | Standard dividers between sections |
| `--line-strong` | `rgba(244,238,229,0.14)` | `rgba(26,22,18,0.14)` | Ghost-button border, stat-card hover border, rail separator |

---

## 4. Typography

Unchanged from Magenta Sanctum. Playfair Display / DM Sans / JetBrains Mono, bundled locally at `src/app/static/fonts/` with `@font-face`. Never point the app at fonts.googleapis.com.

- **Display serif** (Playfair Display 500 / 700): wordmark, hero greeting, landing H1, major section headlines.
- **Body sans** (DM Sans 400 / 500 / 600): nav, page titles, buttons, row titles, descriptions.
- **Mono** (JetBrains Mono 400 / 500): section labels (uppercase 11px, tracking 0.08em), tabular-nums stat values, timestamps, provider badges, `⌘K` chip.

---

## 5. Radii

| Token | Value | Use |
|---|---|---|
| `--r-sm` | `6px` | Sidebar items, ghost + accent buttons, search input, context tags |
| `--r-md` | `10px` | Stat cards, action cards, rail icon when active |
| `--r-lg` | `14px` | Reserved for larger feature cards (landing page, empty states) |

---

## 6. Shell & components

Structurally unchanged from Magenta Sanctum. The four-column shell (rail / sidebar / main / context-panel), stat cards, action cards, conversation rows, section labels, primary/ghost buttons, provider lane indicator, and context tags all inherit the new tokens without layout changes.

Section labels that were set to `color: var(--accent)` now read clay — quieter and more room-like than the prior magenta pop. The one "hero number per page" accent rule remains; the hero number is now clay, not pink.

---

## 7. Prohibited

- Drop shadows on cards. Hairlines, solid backgrounds, and warm ambient glow only.
- Icons in sidebar nav text. Text-only, with optional lane-color bars and right-aligned badges/dots.
- Web font CDN dependencies. Fonts bundled locally or system-fallback. No network calls for styling.
- Telemetry, analytics, or network requests outside explicit intelligence features.
- Using `--accent` for provider dots or data colors. Brand is clay, data is lane colors.
- Using lane colors for brand purposes (active nav, CTA). Data is data, brand is brand.
- Using `--wordmark-gold` anywhere except on the literal "SoulPrint" wordmark rendering. Gold is identity, not a palette color.
- Gradients in the app shell. (A scoped marketing gradient on the landing page is still permitted but not required.)
- Pure-white text on dark backgrounds. Always the cream `rgba(244,238,229,*)` scale.

---

## 8. Phase rollout

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Token swap in `app.css` (accent, backgrounds, text, lines, lanes, wordmark tokens defined). New doctrine doc. `DECISIONS.md` supersession row. Version bump `0.6.1 → 0.7.0-alpha.1`. CSS cachebust bump. | **This phase.** |
| Phase 2 | Apply orange-red Torchlit wordmark glow recipe on shell wordmark. Recolor `logo.svg` SP mark from `#f472b6` to clay. Remove any pink decorative references that surface on visual inspection. | Next. |
| Phase 3 (future) | Structural corrections: search-first home, reduced shell chrome on lower-priority routes. Listed as FUTURE WORK — no implementation commitment in this doctrine revision. | Future. |
| Phase 4 | Archive `docs/product/design-doctrine-magenta-sanctum.md` under `docs/archive/`. Update `docs/product/brand.md` (currently stale USB Drive doctrine). | Future. |

---

## 9. Doctrine drift detection

A session introduces drift if it:

- Adds a new `--` token without updating this doc
- Uses a hex literal inside a selector (all colors must go through tokens)
- Adds a gradient in the app shell
- Adds a web-font URL
- Uses `--accent` on a data/row surface or a lane color on a brand/chrome surface
- Uses `--wordmark-gold` outside a wordmark rendering

Reviewers (human or AI) flag any of the above in the diff.

---

## 10. Version & changelog pointer

This doctrine ships in SoulPrint `v0.7.0-alpha.1`. Magenta Sanctum v2 applied through v0.6.0–v0.6.1. USB Drive applied through v0.5.x. See `DECISIONS.md` for the supersession row and `CHANGELOG.md` for the release note once Phase 1 lands.
