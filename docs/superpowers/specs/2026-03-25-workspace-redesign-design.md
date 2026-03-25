# Workspace Redesign: Design System Update + Landing Page

**Date:** 2026-03-25
**Status:** Approved (spec review passed)
**Scope:** Approach B — design system tokens + global components + landing page

---

## Problem

The current workspace landing page has flat visual hierarchy. Everything competes for attention: a 4-column stats grid, provider badges, a 3-column "Resume Recent Work" section, and a 6-bullet "Next Actions" list all sit at equal visual weight. The result feels like a dashboard, not a home.

The rest of the app uses flat divider-based layouts with no container grouping, which makes pages feel like lists of items rather than organized spaces.

## Goals

1. **"I'm home"** — the landing page should feel like a safe, organized archive, not a tool or dashboard
2. **Import as gravitational center** — the primary CTA ("bring more in") anchored by trust messaging
3. **Discord-inspired containers and rhythm** — rounded grouped containers, spacious padding, calm interactive feedback
4. **Two-accent system** — green for actions, purple for interactive/selection states
5. **Consistent across all pages** — design system changes carry through every template

## Non-Goals

- No changes to nav structure, labels, or grouping
- No changes to route paths
- No new pages or features
- No changes to the imported explorer (3-column layout)
- No upgrade/upsell on the landing page

---

## Prerequisites: Unfreeze Accent Rule

Before implementation, update these files to formally sanction the two-accent system:

1. **`DECISIONS.md`** — Remove the stale "two accent colors only: wine/gold" line (leftover from Torchlit Vault). Add: "Two accents: green (#4ade80) for actions, purple (#7c5cbf) for interactive feedback. Approved 2026-03-25."
2. **`docs/product/brand.md`** — Update the "No second accent" line to: "Two accents: green (actions), purple (interactive states). No third accent."

These docs currently contradict each other (DECISIONS.md references wine/gold from the old theme, brand.md says green-only). Both need reconciliation regardless of this spec.

---

## Part 1: Design System Changes (`app.css`)

### New CSS Custom Properties

```css
/* Dark theme additions */
--accent-secondary: #7c5cbf;
--accent-secondary-dim: #6b4dab;
--accent-secondary-muted: rgba(124,92,191,0.15);

--radius-sm: 6px;     /* buttons, badges, inputs, hover feedback */
--radius-md: 10px;    /* content group containers */
--radius-lg: 14px;    /* hero blocks, modals */

--space-container: 16px;  /* internal container padding */

/* Light theme additions */
[data-theme="light"] {
  --accent-secondary: #6b4dab;
  --accent-secondary-dim: #5a3d96;
  --accent-secondary-muted: rgba(107,77,171,0.12);
}
```

### CSS Override to Remove

The existing blanket reset on line ~109 of `app.css`:
```css
.page-header,.surface-card,.record-card,...{border-radius:0;box-shadow:none}
```
must be narrowed. Remove `.container-card` and `.record-card` from this rule (or split it). The `box-shadow:none` portion can stay for all elements. The `border-radius:0` should only apply to elements that genuinely need it (`.page-header`, `.content-block`, etc.), not to the new container system.

### Accent Split Rule

| Color | Role | Examples |
|-------|------|----------|
| Green (`--accent`) | "Do this" — actions, CTAs, success | Import button, active nav border, success badges |
| Purple (`--accent-secondary`) | "You're here / looking at this" — interactive feedback | Row hover, sidebar active background, selected items |

### `.container-card` (New Group Containers)

**Important:** This is a NEW class, not a modification of the existing `.surface-card`. The existing `.surface-card` (flat, no background, bottom-border divider) is used across 13+ templates and must not be changed. The new `.container-card` is a Discord-inspired grouped container with background, radius, and padding.

```css
.container-card {
    background: var(--surface);
    border-radius: var(--radius-md);
    padding: var(--space-container);
    border: 1px solid var(--line);
}

@media (max-width: 760px) {
    .container-card {
        border-radius: 0;
        border-left: none;
        border-right: none;
    }
}
```

Migration path: Existing `.surface-card` usages stay as-is. New landing page and list containers use `.container-card`. Over time, individual pages can migrate from `.surface-card` to `.container-card` one at a time, outside this spec's scope.

### `.record-card` Hover (Inside `.container-card`)

Individual items inside a `.container-card`. Flat at rest, interactive on hover. The hover uses padding + background swap (not negative margins) to avoid layout jank.

```css
/* Records inside container-cards get horizontal padding to match container */
.container-card .record-card {
    padding: 12px var(--space-container);
    margin: 0 calc(-1 * var(--space-container));
    border-bottom: 1px solid var(--line);
    border-radius: var(--radius-sm);
    background: transparent;
    transition: background 150ms ease;
}

.container-card .record-card:last-child {
    border-bottom: none;
}

.container-card .record-card:hover {
    background: var(--accent-secondary-muted);
}

@media (hover: none) {
    .container-card .record-card:hover {
        background: transparent;
    }
}
```

Note: The padding + negative margin is set at rest (not on hover), so the box model never changes during interaction. Only `background` transitions on hover — no layout shift.

### Sidebar Updates

```css
/* Active link: existing green border + new purple background */
.app-nav__link--active {
    border-left: 2px solid var(--accent);
    color: var(--t1);
    background: var(--accent-secondary-muted);
}

/* Hover on inactive links: half-opacity purple */
.app-nav__link:hover:not(.app-nav__link--active) {
    background: rgba(124,92,191,0.08);
}
```

### Empty States

```css
/* Replace dashed border with container-card styling */
.empty-state {
    background: var(--surface);
    border-radius: var(--radius-md);
    border: 1px solid var(--line);
    padding: var(--space-container);
    text-align: center;
}
```

### What Does NOT Change

- Color hierarchy (t1/t2/t3/t4)
- Typography (system sans, JetBrains Mono, Forum wordmark)
- Lane colors
- No box-shadows anywhere
- Nav structure, labels, grouping
- Existing responsive breakpoints (1180px, 920px, 760px)

---

## Part 2: Landing Page (`index.html`)

### First-Run State (`workspace.has_any_data == False`)

**Remove the existing `page-header` section entirely.** Neither state uses the standard eyebrow + h1 + badges page header pattern. The landing page has its own layout.

Vertically centered on page. Three elements only.

**Layout:**
```
[wordmark]           Forum, large, --t1
[tagline]            "A virtual USB stick for your AI life."
                     system sans, 16px, --t2

╭─ container-card (trust + CTA) ────────────────╮
│                                               │
│  Your files are processed locally.            │
│  Nothing is sent anywhere. No account.        │
│  No cloud. Everything stays on your machine.  │
│                                               │
│  ┌─────────────────────────────────────┐      │
│  │  Bring your first conversation home │      │
│  └─────────────────────────────────────┘      │
│                          green filled CTA     │
╰───────────────────────────────────────────────╯
```

**Specifications:**
- Max-width: 420px, `margin: 0 auto`
- Vertically centered via flexbox on `.main-content` (`min-height: calc(100vh - sidebar-footer)`, `align-items: center`)
- Wordmark: Forum, ~2rem, `--t1`. **Prerequisite:** Add `Forum` to the Google Fonts import in `base.html` if not already present: `https://fonts.googleapis.com/css2?family=Forum&display=swap`
- Tagline: system sans, 16px, `--t2`, `margin-bottom: 24px`
- Trust + CTA card: `.container-card` with `radius-md`
- Trust text: 14px, `--t2`, line-height 1.6
- CTA button: green filled, full-width inside card, `min-height: 42px`, `radius-sm`
- No badges, no counts, no other content

**Design principle:** "Safety and action are the same thing." The trust statement and the import button live in the same container because they're the same message: this is safe, go ahead.

### Post-Import State (`workspace.has_any_data == True`)

Top-aligned, two cards stacked vertically.

**Layout:**
```
[trust one-liner]    "Local-only · nothing leaves your machine"
                     mono, 11px, --t3, uppercase

╭─ Continuity card ─────────────────────────────╮
│  CONTINUITY                         eyebrow   │
│                                               │
│  You have 62 conversations                    │
│  across 3 providers.                          │
│                                               │
│  ┌─────────────────────────────────────┐      │
│  │    Import more conversations        │      │
│  └─────────────────────────────────────┘      │
│                          green filled CTA     │
╰───────────────────────────────────────────────╯

╭─ Archive card ────────────────────────────────╮
│  YOUR ARCHIVE                       eyebrow   │
│                                               │
│  ▎ ChatGPT   47 conversations                │
│  │ last: "API rate limiting strategy"      →  │
│  ─────────────────────────────────────────── │
│  ▎ Claude    12 conversations                 │
│  │ last: "SoulPrint import pipeline"       →  │
│  ─────────────────────────────────────────── │
│  ▎ Gemini     3 conversations                 │
│  │ last: "Travel planning notes"           →  │
│  ─────────────────────────────────────────── │
│                                               │
│  Browse everything together                →  │
╰───────────────────────────────────────────────╯

[dark space — page ends]
```

**Trust one-liner:**
- `--font-mono`, 11px, uppercase, `--t3`, letter-spacing 0.12em
- Sits above the first card, directly on `--bg`
- `margin-bottom: 16px` — gap to first card, no separator line (the card's own border provides enough visual separation)

**Continuity card** (`.container-card`):
- "CONTINUITY" eyebrow: mono, 11px, uppercase, `--t3`
- Continuity sentence: 16px, `--t1`, system sans, weight 500
- Text: "You have X conversations across Y providers." (simplified from current `continuity_sentence` which includes native count — update the template to use `imported_conversation_count` and `providers|length` directly, or update `continuity_sentence` to drop native/trace counts)
- CTA: green filled button, "Import more conversations" → `/import`

**Archive card** (`.container-card`):
- "YOUR ARCHIVE" eyebrow: mono, 11px, uppercase, `--t3`
- Provider rows (`.record-card` inside `.container-card`):
  - 2px left border in lane color
  - Provider name: 15px, `--t1`, weight 500
  - Conversation count: mono, 12px, `--t3`
  - Most recent title: 14px, `--t2`, ghost link (arrow suffix) → conversation explorer
  - Hover: purple tint (no layout shift — see Part 1 hover spec)
- Footer link: "Browse everything together" ghost link → `/federated`
- **Note:** The `/federated` page currently requires a search query to show results. This link is acceptable — users who click "Browse everything together" are primed to search. No changes needed to the federated page for this spec.

**Max-width:** 560px for both cards, `margin: 0 auto`
**Gap between cards:** 16px

### What Gets Removed from Current `index.html`

| Current Element | Disposition |
|----------------|-------------|
| 4-column stats grid | Removed — counts are inline in provider rows |
| Provider badges | Removed — lane colors identify providers |
| 3-column "Resume Recent Work" | Removed — recent titles are in provider rows |
| 6-bullet "Next Actions" | Removed — sidebar handles navigation |
| Compact welcome tagline | Replaced by trust one-liner |
| "Go deeper→" link | Removed from landing page — stays on gated route pages |

---

## Part 3: Global Component Updates

### Content List Pages

**Affected templates:** `imported_list.html`, `answer_trace_list.html`, `federated.html`, `view.html`

**Change:** Wrap the list of record rows in a `.container-card` wrapper. Individual rows stay as flat `.record-card` items inside. Existing `.surface-card` usages on these pages remain untouched.

**Before:**
```html
<div class="record-card">...</div>
<div class="record-card">...</div>
```

**After:**
```html
<div class="container-card">
  <div class="record-card">...</div>
  <div class="record-card">...</div>
</div>
```

### Page Headers

No change. Eyebrow + h1 + summary sit above the surface-card, directly on `--bg`. Header = context, card = content.

### Empty States

Replace `border: 1px dashed var(--t4)` with `.container-card`-style styling (background, radius, solid border). Content stays the same.

### Mobile (≤760px)

```css
@media (max-width: 760px) {
    .container-card {
        border-radius: 0;
        border-left: none;
        border-right: none;
    }
}

/* Disable hover effects on touch devices */
@media (hover: none) {
    .container-card .record-card:hover {
        background: transparent;
    }
}
```

- Landing page cards: full-width, reduced padding (`12px` instead of `16px`)

---

## View Model Changes

### `WorkspaceSummary` (`src/app/viewmodels/workspace.py`)

**New field (additive):** `provider_recent: list[dict]` — one entry per provider with:
```python
{
    "provider": "chatgpt",
    "count": 47,
    "recent_title": "API rate limiting strategy",
    "recent_id": 142,  # conversation ID for the ghost link
}
```

**Query:** Per-provider most recent conversation requires grouping by `source` and ordering by `id DESC` within each group (or a subquery with `MAX(id)`). Each provider entry needs `COUNT(*)` and the title of the row with the highest `id`.

**This is additive** — existing fields (`providers`, `recent_imported`, `recent_native`, `recent_traces`, `native_count`, `trace_count`) stay on the dataclass and keep working. Existing tests continue to pass. The landing page template simply uses `provider_recent` instead of the older fields.

**Kept (used by template):** `has_any_data`, `continuity_sentence`, `imported_conversation_count`.

**Kept (not used by template, still on dataclass):** `native_count`, `trace_count`, `recent_native`, `recent_traces`, `providers` — available for other pages or future use.

---

## Testing

- `python -m pytest tests/ -v` must pass after all changes
- Visual verification at 1200px, 768px, 480px
- Verify first-run state (empty DB) and post-import state (with data)
- Verify hover states show purple tint on record rows and sidebar links
- Verify green accent still used for CTAs, active nav border, success states

---

## Files Modified

| File | Change |
|------|--------|
| `DECISIONS.md` | Unfreeze single-accent rule, add two-accent (green+purple) decision |
| `docs/product/brand.md` | Update accent color rule to allow purple secondary |
| `src/app/static/app.css` | New tokens, `.container-card`, scoped record-card hover, sidebar active bg, empty state, narrow `border-radius:0` override, mobile rules |
| `src/app/templates/base.html` | Sidebar active link background style; verify Forum font import present |
| `src/app/templates/index.html` | Complete rewrite — remove page-header, two states, trust hero, provider stack |
| `src/app/templates/_ui.html` | Update `empty_state` macro styling |
| `src/app/templates/imported_list.html` | Wrap record list in `.container-card` |
| `src/app/templates/answer_trace_list.html` | Wrap record list in `.container-card` |
| `src/app/templates/federated.html` | Wrap record list in `.container-card` |
| `src/app/templates/view.html` | Wrap record list in `.container-card` |
| `src/app/viewmodels/workspace.py` | Add `provider_recent` field (additive) |

**Not modified (existing `.surface-card` usages stay as-is):**
`passport.html`, `ask.html`, `import.html`, `continuity_detail.html`, `imported_explorer.html`, `memory_detail.html`, `answer_trace_detail.html` — these use the old `.surface-card` class and are not affected by this spec.

---

## Decisions Log

| Decision | Rationale |
|----------|-----------|
| Two-accent split (green action, purple interactive) | Separates "do this" from "you're here" — different cognitive signals |
| New `.container-card` class (not modifying `.surface-card`) | Existing `.surface-card` used across 13+ templates — redefining it would break everything. New class allows incremental adoption. |
| Container-holds-rows pattern | Discord pattern: group container with internal dividers, not individual rounded rows |
| Record hover: padding at rest, background-only transition | Negative margins on hover cause layout jank. Set the box model at rest, only animate `background`. |
| Trust block combines safety + CTA | "Safety and action are the same thing" — they're one message |
| Trust messaging fades after first import | Full statement for first visit (earning trust), one-liner after (reinforcing) |
| Kill stats grid, action list, resume section | Redundant with provider stack and sidebar — flat hierarchy was the core problem |
| Upgrade link off landing page | Contextual upsell at gated routes is more effective than generic home-page prompt |
| Mobile: radius 0, flush to edges | Small screens need every pixel; rounded corners waste edge space |
| Mobile: `@media (hover: none)` disables hover effects | Touch devices don't have hover; showing hover styles on tap is confusing |
| Max-width 560px on post-import cards | Prevents content stretching on wide screens; centered and readable |
| `provider_recent` is additive on `WorkspaceSummary` | Existing fields and tests stay untouched; new field used only by new template |
| Unfreeze accent rule in DECISIONS.md | DECISIONS.md still references stale Torchlit Vault wine/gold — needs reconciliation regardless |
