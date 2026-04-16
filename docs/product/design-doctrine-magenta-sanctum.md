# Magenta Sanctum — SoulPrint Design Doctrine v2

**Status:** Active. Supersedes the "USB Drive" doctrine documented in `docs/archive/dual-theme-spec.md`.

**Precedence rule:** If any committed doc contradicts this file, this file wins. If this file contradicts `src/app/static/app.css`, the CSS wins — live code is always the final authority.

**Reference mockup:** `docs/product/mockups/soulprint-discord-bun-mockup.html`. This file is the visual ground truth. Every token and component below is transcribed from it.

**Audience:** Human (Chris), AI coding agents (Claude Code), future contributors. Every UI-touching Claude Code session must read this before editing templates or CSS.

---

## 1. Intent

The USB Drive doctrine was right for v0.1–v0.5: flat, hardware-adjacent, no decoration, everything legible in one second. It got SoulPrint to a shipping product. What it left behind was a tool that reads as a utility rather than a place.

Magenta Sanctum is what the app becomes when it's honest about what it actually is: a personal archive of thought. That's not a utility. It's a space.

The doctrine borrows two structural patterns from products that already solved adjacent problems: **Discord's four-column workspace shell** (rail → sidebar → main → context panel) for the architecture of attention, and **Bun's subtle editorial restraint** (muted grays, one hot-pink accent, serif display heading) for the aesthetic language. Neither is imitated; both are absorbed.

Two rules carry the whole doctrine:

- **Shell is editorial.** Rail, sidebar, header bar, hero greeting, and context panel are designed surfaces. Playfair Display (or system serif fallback) for personality. Single pink accent. Ambient radial glow behind main area at 6% opacity. Solid accents — no gradients in the app shell.
- **Data is flat.** Conversation rows, message lists, stats, provider lists, search results — unchanged from USB Drive principles. Mono labels, tabular nums, hairline dividers, no cards wrapping rows, no shadows.

If a design decision drifts into decoration-on-data or utility-on-shell, it's wrong.

**Gradient policy:** The pink-to-magenta gradient (`#fb7185 → #e879f9 → #d946ef`) lives on the **landing page only** — marketing chrome, not app chrome. The app shell uses solid `--accent`. This is an intentional split between "outside voice" and "inside voice."

---

## 2. Color tokens

### Brand — pink accent

| Token | Value | Use |
|---|---|---|
| `--accent` | `#f472b6` | Active rail icon, active sidebar item text, CTA fill, focus rings, `.highlight` inline spans |
| `--accent-dim` | `#be4b8a` | CTA hover, focused input border |
| `--accent-soft` | `rgba(244, 114, 182, 0.12)` | Active sidebar item background |
| `--accent-glow` | `rgba(244, 114, 182, 0.06)` | Ambient radial glow on `.main::before` |

Light-theme values (if the toggle is preserved): `--accent: #db2777`, `--accent-dim: #9d174d`, `--accent-soft: rgba(219,39,119,0.12)`, `--accent-glow: rgba(219,39,119,0.05)`.

### Secondary — green presence

| Token | Value | Use |
|---|---|---|
| `--green` | `#4ade80` | "local-first" status indicator in sidebar footer, user-status dot |
| `--green-soft` | `rgba(74, 222, 128, 0.12)` | Reserved; not currently used |

Green is not brand. Green means "alive, local, present." Only deploy on status indicators that communicate one of those three concepts.

### Background scale — five levels

| Token | Value | Use |
|---|---|---|
| `--bg-darkest` | `#111113` | Rail background, sidebar search input background |
| `--bg-dark` | `#18181b` | Sidebar background, stat cards, context panel, `.convo-item` hover |
| `--bg-mid` | `#1e1e22` | Main content area background |
| `--bg-light` | `#27272b` | Default rail icon background, context tags, `⌘K` kbd chip |
| `--bg-hover` | `#2e2e33` | Sidebar item hover, ghost button hover |

For backward compatibility during the phase-by-phase migration, the legacy tokens stay defined and map to the new scale:

```css
--bg: var(--bg-darkest);
--surface: var(--bg-dark);
--raised: var(--bg-mid);
```

### Provider lanes (muted, logo-derived)

| Provider | Value | Inspiration |
|---|---|---|
| `--lane-chatgpt` | `#5a8a6a` | OpenAI green, desaturated |
| `--lane-claude` | `#c9a84c` | Anthropic clay/gold, desaturated |
| `--lane-gemini` | `#5a7a9a` | Google blue, desaturated |
| `--lane-native` | `#5a7a9a` | Matches Gemini for now; revisit if native notes gain their own identity |

**Note on Claude = gold, not purple.** Stored memory descriptions reference Claude as purple/violet. That description is retired — the app uses gold per this doctrine. The lane colors are intentionally muted so they sit *behind* the pink accent rather than competing with it. Data colors should never outshine brand color.

### Text hierarchy

| Token | Value | Use |
|---|---|---|
| `--t1` | `rgba(250, 250, 250, 0.92)` | Primary body |
| `--t2` | `rgba(250, 250, 250, 0.56)` | Secondary / descriptions |
| `--t3` | `rgba(250, 250, 250, 0.32)` | Mono labels, small caps, metadata |
| `--t4` | `rgba(250, 250, 250, 0.14)` | Disabled, decorative lines |

Base color is pure white `rgba(250,250,250,*)`, not the prior ivory tint. Tighter, less warm, more Discord-native.

### Lines — two strengths

| Token | Value | Use |
|---|---|---|
| `--line` | `rgba(250, 250, 250, 0.07)` | Standard dividers between sections |
| `--line-strong` | `rgba(250, 250, 250, 0.12)` | Ghost-button border, stat-card hover border, rail separator |

---

## 3. Typography

### Font strategy (read first)

The reference mockup uses **Playfair Display / DM Sans / JetBrains Mono from Google Fonts CDN**. That contradicts SoulPrint's "nothing leaves your machine" promise — Google Fonts phones home on every page load.

**Resolution:** Bundle the three typefaces locally under `src/app/static/fonts/` with `@font-face` declarations in `app.css`. The `--font-*` tokens reference the local family names. If font bundling is deferred (e.g., to ship a first cut faster), the fallback system stacks take over and the app renders in `ui-serif / system-ui / ui-monospace` — visually ~85% of the mockup, zero network calls.

**Never point the app at fonts.googleapis.com.** That is non-negotiable.

### Tokens

```css
--font-display: 'Playfair Display', ui-serif, Georgia, Cambria, "Times New Roman", serif;
--font-body:    'DM Sans', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
--font-mono:    'JetBrains Mono', ui-monospace, "SF Mono", Menlo, Consolas, monospace;
```

### Usage

- **Display serif:** hero greeting ("Good afternoon, Chris"), sidebar header wordmark, landing page H1, major section headlines. Weight 500, letter-spacing 0.02em on wordmark, normal on headings.
- **Body sans:** all nav items, page titles, button labels, card titles, row titles, descriptions. Weight 400–600.
- **Mono:** section labels (uppercase mono 11px, tracking 0.08em), stat values when tabular-nums needed, timestamps, provider badges, `⌘K` chip, count badges.

The prior **"Forum font for wordmark only"** rule is retired. Forum is deprecated.

---

## 4. Radii

| Token | Value | Use |
|---|---|---|
| `--r-sm` | `6px` | Sidebar items, ghost + accent buttons, search input, context tags |
| `--r-md` | `10px` | Stat cards, action cards, rail icon when active |
| `--r-lg` | `14px` | Reserved for larger feature cards (landing page, empty states) |

---

## 5. Shell — four-column layout

### Column A: Workspace rail (64px)

- Background `--bg-darkest`, right border `1px solid var(--line)`
- Contains top-to-bottom: active SP icon, rail separator (28px × 1px `--line-strong`), per-provider icons (Claude / ChatGPT / Gemini placeholders as C / G / Ge), flexible spacer, `+` import shortcut, `⚙` settings shortcut
- Rail icon: 42px round, `--bg-light` background, `--t2` icon color
- Rail icon hover: `border-radius: var(--r-md)` (morphs round → squircle), background `--accent`, text white
- Rail icon active: same as hover, plus a **4px × 24px pink pill** on the left edge (Discord-style active indicator), positioned at `left: -15px`

**The rail is core to v1. Not deferred.**

### Column B: Sidebar (240px)

- Background `--bg-dark`, right border `1px solid var(--line)`, flex-column
- Sidebar header: 48px tall, `--font-display`, 16px, weight 500, letter-spacing 0.02em. Contains wordmark "SoulPrint".
- Search input: below header, 7px vertical padding, `--bg-darkest` background, `--line` border, `--r-sm` radius. Focused border becomes `--accent-dim`. A `⌘K` kbd chip is positioned absolutely in the right-padding area, 10px mono, `--bg-light` background.
- Nav groups, each with:
  - Group label: mono 10.5px uppercase, tracking 0.08em, `--t3`, padding `16px 8px 6px`
  - Items: 6px/8px padding, `--r-sm` radius, 13.5px body font, `--t2` text
  - Item hover: `--bg-hover` background, `--t1` text
  - Item active: `--accent-soft` background, `--accent` text
  - Optional 3px × 16px vertical lane color bar (2px radius) on the left for items tied to a specific provider
  - Optional right-aligned mono badge (count) or 8px pink unread dot
- Sidebar footer: 10px/12px padding, top border `--line`, flex row — avatar circle 32px, user-info stack (name `--t1` 13px weight 500 + status "local-first" in `--green` 11px with a 6px green dot prepended via `::before`)

### Column C: Main content (flex)

- Background `--bg-mid`, flex-column
- Header bar: 48px tall, 0 20px padding, bottom border `--line`. Contains page title (body 15px weight 500 `--t1`) + page description (body 13px `--t3`, 8px left margin) + right-aligned action buttons (ghost + accent)
- Content area: `overflow-y: auto`, padding `28px 32px`
- **Ambient glow:** `.main::before` is a 600×600 radial gradient of `--accent-glow` positioned top: -200px / right: 100px, fixed, pointer-events: none, z-index: 0. Main content sits at z-index: 1.

### Column D: Context panel (260px)

- Background `--bg-dark`, left border `1px solid var(--line)`, flex-column
- Header: 48px tall matching main header, bottom border `--line`, contains "Context" (body 13px weight 500 `--t2`)
- Scrollable section area below:
  - Each section: 16px padding, bottom border `--line` (last section no border)
  - Section label: mono 10.5px uppercase tracking 0.08em `--t3`
  - Providers: flex-row items with 10px dot (provider lane color), name (body 13px `--t1`), count (mono 11px `--t3` right-aligned)
  - Top Themes: inline `context-tag` spans — 12px body, `--t2` text, `--bg-light` background, 3px/8px padding, 4px radius
  - Recent Activity: stacked items with 8px vertical padding, text `--t2` 12.5px, time mono 10.5px `--t3`. `.highlight` spans within text are `--accent` color.

---

## 6. Components

### Stat card (3 per workspace top row)

- `--bg-dark` background, `--line` border, `--r-md` radius, 18px/20px padding
- Hover: border becomes `--line-strong` (subtle)
- Label: mono 10.5px uppercase tracking 0.08em `--t3`, 8px bottom margin
- Value: 28px weight 600 `--t1`, tabular-nums. Exactly **one** value per page may wrap its number in `<span class="accent">…</span>` to apply `--accent` color (used for "Themes found: 14")
- Sub-line: 12px `--t3`, 4px top margin

### Action card / quick action (3 per workspace)

- `--bg-dark` background, `--line` border, `--r-md` radius, 20px padding, cursor pointer
- Hover: border `--accent-dim`, background `--bg-light`
- Title (h3): 14px weight 500 `--t1`, 6px bottom margin
- Body (p): 13px `--t2`, line-height 1.5
- Meta: mono 11px `--t3`, 12px top margin

### Conversation row (recent conversations list)

- Flex row, 10px/14px padding, `--r-sm` radius, cursor pointer
- Hover: `--bg-dark` background
- 8px round lane dot + title (flex-1, body 13.5px `--t1`, ellipsis) + provider badge (mono 10.5px uppercase tracking 0.04em `--t3`) + date (mono 11px `--t3`)

### Section label

Used above Quick Actions, Recent Conversations, and similar groupings inside main content.
- mono 11px uppercase tracking 0.08em
- color `--accent` (this is the magenta section-label pattern from the mockup)
- 14px bottom margin

### Primary button (`.btn-accent`)

- `--accent` background, white text, no border, 5px/14px padding, `--r-sm` radius, weight 500, 13px
- Hover: `--accent-dim`

### Ghost button (`.btn-ghost`)

- Transparent background, `--line-strong` border, `--t2` text, 5px/12px padding, `--r-sm` radius, 13px
- Hover: `--bg-hover` background, `--t1` text

### Provider lane indicator (sidebar)

- 3px × 16px vertical bar, 2px radius, filled with `var(--lane-{provider})`
- Sits left of the item label when an item is tied to a specific provider

### Context tag (top themes)

- Inline span, 12px `--t2`, `--bg-light` background, 3px/8px padding, 4px radius
- 0/4px/4px/0 margin (forms inline-flow row)

---

## 7. Interactions

- Focus ring: accent-dim border on inputs; `outline: 2px solid var(--accent)` on interactive elements, `outline-offset: 2px`
- Hover shifts happen over `0.12–0.2s` — standardized on 0.15s for buttons, 0.12s for rows, 0.2s for card borders
- Rail icon border-radius transition: `border-radius 0.2s, background 0.2s` (the circle → squircle morph is signature Discord and should be preserved)
- Active states always use `--accent` directly

---

## 8. Prohibited

- Drop shadows on cards. Hairlines, solid backgrounds, and the one ambient radial glow only.
- Icons in sidebar nav text. Text-only, with optional lane-color bars and right-aligned badges/dots.
- More than one magenta value in stats at a time. One hero number per page maximum.
- Web font CDN dependencies (Google Fonts, Adobe Fonts, etc.). Fonts are either bundled locally or system-fallback. No network calls for styling.
- Telemetry, analytics, or network requests that aren't part of explicit intelligence features (Ask, Distill, Themes) using the user's own API key.
- Using `--accent` for provider dots or data colors. Brand is pink, data is lane colors.
- Using lane colors for brand purposes (active nav, CTA). Data is data, brand is brand.
- Gradients in the app shell. The pink-red gradient is marketing (landing page) only.

---

## 9. Class-name conventions

Consistent class naming is how drift gets caught in PRs. Use these prefixes; if something doesn't fit, propose an addition rather than inventing a new convention.

| Family | Prefix | Examples |
|---|---|---|
| Shell | `shell`, `rail`, `sidebar`, `main`, `context-panel` | `rail-icon`, `sidebar-item`, `main-header` |
| Sidebar items | `sidebar-` | `sidebar-group-label`, `sidebar-footer` |
| Workspace page | `workspace-greeting`, `stats-row`, `stat-card`, `card-grid`, `convo-list`, `convo-item` | — |
| Context | `context-panel`, `context-section`, `context-provider`, `context-tag`, `activity-item` | — |
| Buttons | `btn-accent`, `btn-ghost` | — |
| Utilities | `.t1`, `.t2`, `.t3`, `.t4`, `.highlight`, `.accent`, `.scrollable` | — |

BEM is used where the mockup uses it (e.g., `sidebar-item .lane`, `sidebar-item .badge`). Deep nesting is avoided.

---

## 10. Responsive breakpoints

| Breakpoint | Behavior |
|---|---|
| `≥ 1280px` | Full four-column shell (rail 64 / sidebar 240 / main flex / context 260) |
| `1024–1279px` | Context panel collapses; rail + sidebar + main only |
| `768–1023px` | Sidebar collapses to slide-over; rail stays; main takes full width |
| `< 768px` | Rail collapses to a top mobile bar with a hamburger; sidebar and context are slide-overs triggered from the bar |

---

## 11. Doctrine drift detection

A session introduces drift if it:

- Adds a new `--` token without updating this doc
- Uses a hex literal inside a selector (all colors must go through tokens)
- Adds a gradient in the app shell (landing page is exempt)
- Adds a web-font URL to any CSS or HTML
- Adds a class that doesn't match a family in §9
- Uses `--accent` on a data/row surface or a lane color on a brand/chrome surface

Reviewers (human or AI) flag any of the above in the diff. The doctrine exists so drift is *visible*, not so it's *forbidden* — changes are welcome, they just need to be updates to this file, not silent overrides in CSS.

---

## 12. Version & changelog pointer

This doctrine ships in SoulPrint v0.6.0. Previous "USB Drive" doctrine applied through v0.5.x. The reference mockup `soulprint-discord-bun-mockup.html` lives at `docs/product/mockups/` and is the visual canon. See `CHANGELOG.md` for the shipping note once the five-phase UI revamp lands.
