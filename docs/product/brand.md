# SoulPrint — Brand Guide

## Mission

Every person should own their AI memory.

### One-liner

Your AI conversations are scattered everywhere. SoulPrint brings them home.

## Product Voice

- Warm, confident, technical but never cold
- Trustworthy — we handle people's conversation history
- Never corporate, never salesy
- Direct without being terse
- Warm without being cutesy
- Use "your" not "the user's" — speak to people, not about them

## Product Name

**SoulPrint** — one word, capital S, capital P.
Never: Soul Print, soul print, SOULPRINT, SP.

## Warm Nav Labels

Sidebar nav text and page heading text adopt warmer labels.
Routes are unchanged — only the visible text changes.

| Route             | Nav Label                   | Page Heading                  |
|-------------------|-----------------------------|-------------------------------|
| `/`               | Workspace                   | Workspace                     |
| `/ask`            | Ask your memory             | Ask your memory               |
| `/imported`       | What you've discussed       | What you've discussed         |
| `/chats`          | Your own notes              | Your own notes                |
| `/federated`      | Everything, together        | Everything, together          |
| `/intelligence`   | Themes & patterns           | Themes & patterns             |
| `/distill`        | Distill                     | Distill                       |
| `/answer-traces`  | How answers were found      | How answers were found        |
| `/import`         | Import                      | Bring conversations home      |
| `/passport`       | Take it with you            | Memory Passport               |

## Design System: USB Drive

The design communicates trust, calm, and local ownership. Green is a deliberate trust signal — users handing over their entire AI conversation history need to feel safe instantly.

### Color Tokens (dark theme, default)

| Token         | Value       | Usage                                    |
|---------------|-------------|------------------------------------------|
| --bg          | #0e0f11                       | Page background                          |
| --surface     | #141518                       | Sidebar, panel backgrounds               |
| --raised      | #1a1b1f                       | Elevated surfaces, empty state containers|
| --accent      | #4ade80                       | Primary accent — CTAs, active nav, badges|
| --accent-dim  | #22c55e                       | Hover state                              |
| --accent-muted| rgba(74,222,128,0.15)         | Subtle backgrounds, badge fills          |
| --lane-claude | #a78bfa                       | Derived/generated indicators, Claude lane|
| --t1          | rgba(240,242,238,0.88)        | Primary text                             |
| --t2          | rgba(240,242,238,0.55)        | Secondary text                           |
| --t3          | rgba(240,242,238,0.35)        | Muted text, labels                       |
| --t4          | rgba(240,242,238,0.15)        | Ghost text, disabled                     |
| --line        | rgba(255,255,255,0.06)        | Borders, dividers                        |

### Typography

| Role       | Family                              | Weight | Usage                    |
|------------|-------------------------------------|--------|--------------------------|
| Wordmark   | Forum, serif                        | 400    | "SoulPrint" in sidebar   |
| Body       | system-ui, -apple-system, sans-serif| 400    | All reading text, nav    |
| Mono       | JetBrains Mono, monospace           | 400    | IDs, labels, section headers, eyebrows |

Base font-size: 16px on html.

### Provider Lane Colors

| Lane     | Value     | Usage                                    |
|----------|-----------|------------------------------------------|
| ChatGPT  | #4ade80   | Green — shared with primary accent       |
| Claude   | #a78bfa   | Purple                                   |
| Gemini   | #60a5fa   | Blue                                     |
| Native   | #60a5fa   | Blue — same as Gemini for now            |

### Accent Rules

- Green (#4ade80) is the primary accent (--accent) — CTA buttons, active nav indicators, tab pills, search buttons
- Purple (#a78bfa) marks derived/generated surfaces (--lane-claude) — "Generated" badges, section labels on interpretation pages
- Green is a trust signal, not decoration
- Never use accents as background fills on large areas
- Buttons use solid green background with dark text

### Active Nav Indicator

The active sidebar nav item uses:
- Green (#4ade80) left border (3px solid)
- Slightly elevated background
- Text remains the same color

### Section Headers (eyebrows)

All section headers above page headings use:
- JetBrains Mono
- Uppercase
- Letter-spacing: 0.12-0.18em
- Color: green accent or muted (--t3) depending on context
- Font-size: ~0.65rem

### Tab Pills

- Active tab: green (#4ade80) border, green text
- Inactive tab: muted border, muted text
- Small, inline, next to page headings

### Derived Surface Labels

Surfaces showing generated/derived content display a small "Generated" badge:
- Green (#4ade80) outline
- Small font (JetBrains Mono)
- Positioned next to the page heading

## Critical Rules

- No box-shadows on containers
- No icons in nav — text only
- No font-weight above 500
- No decorative borders beyond 1px var(--line) dividers
- No stock photos
- No emoji in the UI (unless user-generated content contains them)
- No "AI" as a visual motif (no robot icons, no brain icons, no sparkles)
- Flat rows with border-bottom dividers preferred over card components
- Empty state containers may use subtle borders for visual grouping
- Typography and spacing create structure, not color

## Footer

Sidebar footer shows:
- "dark" text (theme indicator, left)
- "v0.1.0 · local-first" (right, JetBrains Mono, muted)
