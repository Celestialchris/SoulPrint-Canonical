---
name: soulprint-design
description: SoulPrint-specific visual direction and UI doctrine. Activates for all frontend, template, and CSS work in this repo.
---

# SoulPrint Design Skill

## Identity
SoulPrint is a local-first memory continuity system. The UI must feel
like a calm, trustworthy product — not a developer tool, not a dashboard,
not an AI gimmick.

## Design System: Torchlit Vault (dark default)

The app uses a dual-theme system. Dark ("Torchlit Vault") is the default.
Light ("Parchment Observatory") is the toggle variant. The canonical
visual reference is `src/app/static/app-mock.html`.

### Dark Theme Tokens (default)
```
--bg: #0e0d0b
--surface: #161513
--raised: #1d1b18
--wine: #6b3a3a          (CTAs, actions, active indicators ONLY)
--wine-soft: #8a5050     (hover states)
--gold: #c9a84c          (bright highlight — rare)
--gold-dim: #a08848      (headings, provenance, active nav, wordmark)
--t1: rgba(210,200,185,0.90)   (primary text)
--t2: rgba(210,200,185,0.55)   (secondary text)
--t3: rgba(210,200,185,0.30)   (muted labels, mono text)
--t4: rgba(210,200,185,0.12)   (ghost/disabled)
--line: rgba(210,200,185,0.06) (borders, dividers)
--selection: rgba(107,58,58,0.30)
```

### Light Theme Tokens (data-theme="light")
```
--bg: #f2f0e9
--surface: #eae7df
--raised: #ffffff
--wine: #6b3a3a
--gold-dim: #7a6328
--t1: rgba(31,41,51,0.92)
--t2: rgba(31,41,51,0.55)
--t3: rgba(31,41,51,0.32)
--t4: rgba(31,41,51,0.12)
--line: rgba(31,41,51,0.07)
--selection: rgba(107,58,58,0.15)
```

### Typography
```
--font-display: "Forum", serif           (wordmark, page headings)
--font-body: "Cormorant Garamond", serif (all reading text, nav links)
--font-mono: "JetBrains Mono", monospace (IDs, timestamps, labels, eyebrows)
```
Google Fonts loaded in base.html via:
`Forum`, `Cormorant Garamond:ital,wght@0,400;0,500;1,400`, `JetBrains Mono:wght@400`

Base font-size: 17px on html.

### Lane Colors (2px vertical stripes for provider identity)
```
--lane-chatgpt: #5a8a6a  (sage)
--lane-claude: #a08848   (gold)
--lane-gemini: #5a7a9a   (steel)
--lane-native: #5a7a9a   (steel)
```

### Body Atmosphere (dark mode only)
- Layered radial gradients over --bg (gold warmth top-left, wine warmth top-right)
- Grain overlay: fractal noise SVG at opacity 0.018, fixed position
- Vignette: vertical linear gradient fading to black at top (0.16) and bottom (0.22)
- Light mode: no grain, no vignette, clean flat background

### Wordmark Glow (dark mode only, wordmark element only)
```css
text-shadow:
  0 0 7px rgba(220,140,70,0.50),
  0 0 20px rgba(210,120,60,0.35),
  0 0 50px rgba(200,100,50,0.18),
  0 0 100px rgba(180,80,40,0.07),
  0 2px 4px rgba(0,0,0,0.4);
```

## Hard Design Rules

1. **No cards.** No border-radius on containers, no box-shadows.
2. **No badges as visual components.** Use inline mono labels.
3. **No icons in nav.** Text only. Nav uses --font-body at 500 weight.
4. **No font-weight above 500.** Ever.
5. **No decorative borders** beyond 1px var(--line) dividers.
6. **Hierarchy through opacity, not color.** Four text levels: t1, t2, t3, t4.
7. **Wine for actions only.** CTA borders, active nav indicator, action buttons.
8. **Gold for headings/provenance only.** Page headings, provenance citation borders, stat numbers.
9. **Never mix accents with lane colors.**
10. **Never use accents as background fills on large areas.**
11. **No stock photos, no emoji in UI, no AI visual motifs** (no robot icons, no brain icons, no sparkles).

## Design Principles
- Every surface answers: What am I looking at? Where did it come from? Where can I go next?
- Canonical vs derived must be visually distinct (labels, not badges)
- Transcript explorer: TOC on side, clean reading pane, minimap rail
- Empty states are calm and helpful, never sad or broken-looking
- Navigation is obvious — user never wonders "how do I go back?"
- Typography carries structure. Spacing creates hierarchy. Color is restrained.

## Anti-Patterns
- No giant sidebars stuffed with noise
- No "AI everywhere" visual gimmicks
- No cluttered admin panels or dashboard bloat
- No metrics/charts unless they serve the continuity story
- No scroll-scroll-scroll transcript hell
- If style conflicts with clarity, choose clarity

## Current Surfaces (19 templates, all dark-first)
- `/` (Workspace) — index.html
- `/import` — import.html
- `/ask` — ask.html (Pro-gated)
- `/passport` — passport.html
- `/intelligence` — intelligence.html (Pro-gated)
- `/imported` — imported_list.html
- `/imported/<id>/explorer` — imported_explorer.html
- `/federated` — federated.html
- `/chats` — view.html
- `/memory/<id>` — memory_detail.html
- `/answer-traces` — answer_trace_list.html
- `/answer-traces/<id>` — answer_trace_detail.html
- `/intelligence/continuity/<id>` — continuity_detail.html
- `/distill` — distill.html + distill_result.html (Pro-gated, conversation selection + result)
- `/summary` — wrapped.html (standalone, always dark, no base.html)
- `/upgrade` — upgrade.html (Pro upsell)

## Template Architecture
- `base.html` — shell with topbar nav, Google Fonts, theme toggle, data-theme on html
- `_ui.html` — Jinja macros (nav_link, badge, empty_state)
- `wrapped.html` — standalone, does NOT extend base.html (always dark, cinematic)
- Theme toggle: inline JS in base.html, persists to localStorage as `soulprint-theme`

## When Editing Frontend
- Read `src/app/static/app.css` first (1850 lines, complete design system)
- Read `docs/product/brand.md` for authoritative token values
- Read `src/app/static/app-mock.html` as the canonical visual reference (47KB)
- Preserve all CSS custom properties — extend, don't replace
- Keep server-rendered Jinja templates
- Every visual change must work at 1200px, 768px, and 480px widths
- Run `python -m pytest tests/ -v` after any template changes

## Frozen Nav Labels (from PRODUCT-GRAMMAR-LOCK.md)
| Route | Nav Label |
|-------|-----------|
| `/` | Workspace |
| `/chats` | Your own notes |
| `/imported` | What you've discussed |
| `/import` | Import |
| `/federated` | Everything, together |
| `/passport` | Take it with you |
| `/ask` | Ask your memory |
| `/intelligence` | Themes & patterns |
| `/answer-traces` | How answers were found |

Do NOT change nav labels or route structure without explicit instruction.
