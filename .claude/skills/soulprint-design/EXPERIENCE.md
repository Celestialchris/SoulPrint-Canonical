# Experience Bank: SoulPrint Design

Tactical notes for frontend/UI work in SoulPrint.
Chris is learning Jinja2 and CSS — these notes capture what's
been learned the hard way so future sessions don't repeat mistakes.

---

## Failure Patterns

### Referencing the Wrong Design System

- **When it happens:** Loading stale docs (brand.md, visual-direction.md, old SKILL.md) that reference "Torchlit Vault" with wine/gold accents and Cormorant Garamond
- **What goes wrong:** Claude builds against a design system that no longer exists. Introduces serif body text, wine-colored CTAs, gold headings — all wrong.
- **What actually works:** Always read `src/app/static/app.css` first. The live CSS is the authority, not docs in the repo. The current system is "USB Drive" — green accent, system sans-serif body, Forum only for the wordmark.
- **Why:** The design system was overhauled but several docs weren't updated. The CSS is truth.

### Content Floating Top-Left on Wide Screens

- **When it happens:** Any page with centered content on screens wider than ~1200px
- **What goes wrong:** Content hugs the left edge of the main area instead of centering. Looks unfinished.
- **What actually works:** Content containers need `max-width` and `margin: 0 auto`. The workspace welcome block already does this (max-width: 360px on tagline). Apply the same pattern to other centered content.
- **Why:** `.main-content` has `max-width: var(--content-wide)` (1380px) but no auto-centering — it's left-anchored by `margin-left: 200px` (sidebar width).

### Claude Breaking the Design System

- **When it happens:** Giving Claude broad instructions like "make this page look better"
- **What goes wrong:** Claude introduces cards with box-shadows, border-radius on containers, colored backgrounds, weight 600+ on headings, or decorative elements.
- **What actually works:** Always load the soulprint-design skill FIRST. Be specific: "use --accent for this link hover" not "make it green." Reference specific CSS classes from app.css.
- **Why:** Without the skill loaded, Claude defaults to generic UI patterns that contradict the flat, border-divider-only aesthetic.

### Jinja2 Template Inheritance Confusion

- **When it happens:** Creating a new page template or modifying block structure
- **What goes wrong:** Template doesn't extend base.html correctly, or overrides a block that breaks nav/footer. Or tries to use macros from _ui.html without importing.
- **What actually works:** Copy a working template that's similar, rename it, modify section by section. `{% extends "base.html" %}` must be first line. `{% block content %}` wraps page content.
- **Why:** Jinja2 inheritance is powerful but error messages are cryptic.

### Forgetting Mobile Breakpoint

- **When it happens:** CSS changes that look correct at desktop width
- **What goes wrong:** At 760px, sidebar becomes an overlay, layout collapses to single column. Grids that were 4-column become 2-column or 1-column. Content that fit at 1200px overflows at 480px.
- **What actually works:** Always check 760px specifically — that's where the major layout shift happens. The sidebar disappears and main-content loses its left margin.
- **Why:** The responsive rules at 760px are aggressive — they restructure multiple grids simultaneously.

---

## Strategic Shortcuts

### Copy-From-Working Pattern

- **Instead of:** Writing a new template from scratch
- **Do this:** Find the closest existing template, copy entire file, rename, modify section by section
- **Saves:** Hours of Jinja2 debugging. A working template proves the block structure is correct.

### "Don't Ask Me to Invent Solutions"

- **Instead of:** Telling Claude "improve the UI" and hoping
- **Do this:** Say "propose 2-3 specific layout changes with reasoning. Show me reference patterns I can say yes or no to. Don't ask me to invent solutions."
- **Saves:** Prevents back-and-forth where Claude asks design questions you can't answer. React > invent.

### Read app.css First, Always

- **Instead of:** Reading brand.md or visual-direction.md for design tokens
- **Do this:** Read the first 36 lines of app.css — that's the complete token definition for both themes
- **Saves:** Prevents building against stale documentation. CSS is the single source of truth.

---

## Context Traps

- **Forum is ONLY for the wordmark.** Every heading, nav link, and body text uses --font-body (system sans-serif). Using Forum anywhere else breaks the visual system.
- **Wrapped page is standalone.** `wrapped.html` does NOT extend base.html. Changes to base.html don't affect it. Changes to app.css DO affect it.
- **Green is the only accent.** There's no secondary accent color. If you need visual distinction beyond green, use the lane colors (purple for Claude, blue for Gemini) or the opacity levels (t1/t2/t3/t4).
- **Badges exist but are subtle.** Thin 1px border, border-radius 4px, no background fill. The --accent badge gets green border and text. Don't make badges louder.
- **Outline buttons vs filled buttons.** Filled = primary CTA (green bg, dark text). Outline = secondary (transparent bg, green border, green text). Don't mix them up.

---

## Changelog

| Date | Entry | Source |
|------|-------|--------|
| 2026-03-25 | Complete rewrite for USB Drive system | Live app.css analysis + screenshot review |
