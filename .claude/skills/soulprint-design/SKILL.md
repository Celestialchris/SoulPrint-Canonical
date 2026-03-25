---
name: soulprint-design
description: SoulPrint-specific visual direction and UI doctrine. Activates for all frontend, template, and CSS work in this repo.
---

# SoulPrint Design

> Visual identity and UI doctrine for SoulPrint. Every frontend change
> in this repo must pass through this skill.

---

## Metadata

| Field          | Value |
|----------------|-------|
| **Intent**     | Enforce a calm, trustworthy product aesthetic — not a dev tool, not a dashboard, not an AI gimmick. Every surface answers: What am I looking at? Where did it come from? Where can I go next? |
| **Method**     | Read CSS tokens → check hard rules → build/edit → verify at 3 breakpoints |
| **Difficulty** | Medium (strict tokens, Jinja2 templating requires care) |
| **Tool Hint**  | Run `python -m pytest tests/ -v` after template changes. Check at 1200px, 768px, 480px. |

---

## Trigger Conditions

Use this skill when:
- Editing any `.html` template in `src/app/templates/`
- Editing `src/app/static/app.css`
- Adding a new route with a visible page
- Changing nav structure, labels, or grouping
- Changing typography, color, or spacing
- Creating or modifying Jinja macros in `_ui.html`

Do NOT use this skill when:
- Editing backend Python with no template impact
- Changing test fixtures or CLI scripts
- Working on import/normalize/store internals

---

## Design System: USB Drive

**Tagline:** "A virtual USB stick for your AI life. Plug in. Take everything with you."

### Dark Theme Tokens (default)
```
--bg: #0e0f11               (page background)
--surface: #141518           (panel/hover background)
--raised: #1a1b1f            (elevated surface)
--accent: #4ade80            (green — primary accent, CTAs, links, active states)
--accent-dim: #22c55e        (hover/pressed green)
--accent-muted: rgba(74,222,128,0.15)  (subtle green backgrounds)
--accent-ghost: rgba(74,222,128,0.06)  (barely-there green tint)
--t1: rgba(240,242,238,0.88) (primary text)
--t2: rgba(240,242,238,0.55) (secondary text)
--t3: rgba(240,242,238,0.35) (muted labels, mono text)
--t4: rgba(240,242,238,0.15) (ghost/disabled)
--line: rgba(255,255,255,0.06) (borders, dividers)
--selection: rgba(74,222,128,0.20)
```

### Light Theme Tokens (data-theme="light")
```
--bg: #f4f5f0
--surface: #eaebe5
--raised: #ffffff
--accent: #16a34a
--accent-dim: #15803d
--accent-muted: rgba(22,163,74,0.12)
--accent-ghost: rgba(22,163,74,0.04)
--t1: rgba(14,15,17,0.88)
--t2: rgba(14,15,17,0.55)
--t3: rgba(14,15,17,0.35)
--t4: rgba(14,15,17,0.12)
--line: rgba(0,0,0,0.06)
--selection: rgba(22,163,74,0.15)
```

### Typography
```
--font-display: "Forum", serif                    (wordmark only)
--font-body: -apple-system, BlinkMacSystemFont,
             "Segoe UI", system-ui, sans-serif     (everything else — headings, nav, body)
--font-mono: "JetBrains Mono", ui-monospace,
             monospace                              (eyebrows, labels, metadata, timestamps)
```

Google Fonts in `base.html`: `Forum` (wordmark only), `JetBrains Mono:wght@400`

Base font-size: 16px on html.

### Lane Colors (2px left-border stripes for provider identity)
```
--lane-chatgpt: #4ade80  (green)
--lane-claude: #a78bfa   (purple)
--lane-gemini: #60a5fa   (blue)
--lane-native: #60a5fa   (blue)
```

### CTA System
```
--cta-bg: var(--accent)           (green background)
--cta-text: #0e0f11               (dark text on green)
--cta-hover-bg: var(--accent-dim)
--cta-border: var(--accent)
--cta-outline-text: var(--accent)  (ghost/outline button text)
```

Buttons: `border-radius: 6px`, `font-weight: 600`, `min-height: 42px`.
Outline buttons: transparent bg, `1px solid var(--accent)`, `color: var(--accent)`.

---

## Hard Design Rules

1. **No box-shadows on content.** Surface-card, record-card, route-card, content-block all have `box-shadow: none`.
2. **No border-radius on content containers.** Cards are flat with bottom-border dividers only.
3. **Small border-radius only on:** buttons (6px), badges (4px), inputs, minimap, empty states (6-8px).
4. **Hierarchy through opacity, not color.** Four text levels: t1, t2, t3, t4. Headings are t1, not accent-colored.
5. **Green accent for interactive elements only.** CTAs, links on hover, active nav border, badges with --accent class.
6. **Headings use --font-body at weight 500, not --font-display.** Only the wordmark uses Forum.
7. **Eyebrow labels** use --font-mono at 11px, uppercase, letter-spaced 0.10-0.16em, color --t3.
8. **No decorative elements.** No grain, no vignette, no atmosphere gradients, no glow effects.
9. **No icons in nav.** Text only.
10. **No stock photos, no emoji in UI, no AI visual motifs.**
11. **Lane identity through 2px left-border,** not background fills or badges.

---

## Design Principles

- Every surface answers: What am I looking at? Where did it come from? Where can I go next?
- Canonical vs derived must be visually distinct (mono labels, not decorative badges)
- Empty states are calm and helpful (`border: 1px dashed var(--t4)`, centered text)
- Navigation is obvious — user never wonders "how do I go back?"
- Typography and spacing carry structure. Color is restrained — green accent only for actions.
- Content containers are flat rows separated by `1px solid var(--line)` bottom borders.
- No background fills on containers — content sits directly on `--bg`.

---

## Current Nav Structure (sidebar, grouped)

```
SANCTUM
  Workspace              → /
  Ask your memory         → /ask            (Pro-gated)

MEMORY
  What you've discussed   → /imported
  Your own notes          → /chats
  Everything, together    → /federated

INTERPRETATION
  Themes & patterns       → /intelligence   (Pro-gated)
  Distill                 → /distill        (Pro-gated)
  How answers were found  → /answer-traces

CONTINUITY
  Import                  → /import
  Take it with you        → /passport
```

**Sidebar:** 200px fixed, `backdrop-filter: blur(12px)`, `--sidebar-bg` with transparency.
**Footer:** theme toggle (left), "v0.1.0 · local-first" (right), separated by `1px solid var(--line)`.
**Group labels:** --font-mono 11px uppercase, --t3, letter-spacing 0.14em.
**Active link:** `border-left: 2px solid var(--accent)`, color --t1.

**Not in nav:** `/summary` (standalone, always dark), `/upgrade` (via "Go deeper→")

Do NOT change nav labels, grouping, or route structure without explicit instruction.

---

## Current Surfaces

| Route | Template | Notes |
|-------|----------|-------|
| `/` | index.html | Workspace — wordmark, badges, tagline, CTA, stats, resume grid |
| `/import` | import.html | "Bring conversations home" |
| `/ask` | ask.html | Pro-gated |
| `/passport` | passport.html | Memory Passport export/validate |
| `/intelligence` | intelligence.html | Pro-gated |
| `/imported` | imported_list.html | Conversation list by provider |
| `/imported/<id>/explorer` | imported_explorer.html | 3-column: TOC, transcript, minimap |
| `/federated` | federated.html | Cross-provider view |
| `/chats` | view.html | Native memory |
| `/memory/<id>` | memory_detail.html | Single memory entry |
| `/answer-traces` | answer_trace_list.html | Trace list |
| `/answer-traces/<id>` | answer_trace_detail.html | Single trace |
| `/intelligence/continuity/<id>` | continuity_detail.html | Continuity packet |
| `/distill` | distill.html + distill_result.html | Pro-gated, multi-conversation distillation |
| `/summary` | wrapped.html | Standalone, always dark, cinematic |
| `/upgrade` | upgrade.html | "Go deeper" Pro upsell |

---

## Template Architecture

- `base.html` — shell with sidebar nav, Google Fonts, theme toggle, `data-theme` on `<html>`
- `_ui.html` — Jinja macros (nav_link, badge, empty_state)
- `wrapped.html` — standalone, does NOT extend base.html
- Theme toggle: inline JS in base.html, localStorage key `soulprint-theme`
- Mobile: sidebar collapses at 760px, mobile bar appears with hamburger toggle

---

## Key CSS Patterns

**Page header:** eyebrow (mono, t3, uppercase) + h1 (font-body, 1.5rem, weight 500) + optional badges + summary (t2, 15px)

**Content sections:** `.workspace-block` or `.content-block` — flex column, gap 10px, padding 20px 0, separated by `border-bottom: 1px solid var(--line)`

**Record cards:** flat rows, bottom-border, optional 2px left lane stripe. Title at 15px/500, body at 14px/t2, metadata in mono 11px/t3.

**Stats grid:** 4-column grid, mono 11px uppercase labels, 2.2rem numbers in --font-body weight 500.

**Responsive breakpoints:** 1180px (tighter padding), 920px (narrower sidebar), 760px (mobile — sidebar becomes overlay, single-column layouts).

---

## Anti-Patterns

- No giant sidebars stuffed with noise
- No "AI everywhere" visual gimmicks
- No cluttered admin panels or dashboard bloat
- No metrics/charts unless they serve the continuity story
- No scroll-scroll-scroll transcript hell
- If style conflicts with clarity, choose clarity

---

## Verification Checklist

- [ ] All colors use CSS custom properties (no hardcoded hex in templates)
- [ ] All fonts use the three-family stack (display/body/mono) per their roles
- [ ] Headings use --font-body weight 500, NOT --font-display (only wordmark uses Forum)
- [ ] No box-shadows on content containers
- [ ] Green accent only on interactive elements (CTAs, hover links, active nav)
- [ ] Renders correctly at 1200px, 768px, 480px
- [ ] Nav labels and grouping unchanged (unless explicitly instructed)
- [ ] `python -m pytest tests/ -v` passes

---

## Composition Notes

**Composes well with:** frontend-design (general patterns), brainstorming (for UI planning)
**Conflicts with:** any old reference to "Torchlit Vault", wine/gold accents, Cormorant Garamond, grain overlays
**Prerequisites:** none — always loaded for frontend work

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| 2026-03-25 | Full rewrite: USB Drive system from live app.css, 4-tuple structure, updated nav | Previous version referenced stale Torchlit Vault system |
