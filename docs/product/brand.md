# SoulPrint — Brand Guide

## Mission

Every person should own their AI memory.

### One-liner

A virtual USB stick for your AI life.

### Tagline (landing page hero)

A virtual USB stick for your AI life. Plug in. Take everything with you.

### Trust line

Everything stays on your machine. Nothing is sent anywhere.

## Product Voice

- Direct, clear, trustworthy
- Technical when needed, never cold
- Never corporate, never salesy
- "Your" not "the user's" — speak to people
- Green = safe, verified, go. Use it to reinforce privacy and ownership.
- Never use: vault, ember, torchlit, capsule, portable mode

## Product Name

**SoulPrint** — one word, capital S, capital P.
Never: Soul Print, soul print, SOULPRINT, SP.

## Identity Metaphor

SoulPrint is a virtual USB stick. The metaphor carries through:
- The logo is a pixel-art USB stick with a green body and cutout center
- The LED blinks green (active, alive, working)
- "Plug in" = import your data
- "Take it with you" = Memory Passport export
- The favicon is the same USB icon at 32px

## Color Palette

### Dark (default)

| Token        | Value                           | Usage                           |
|--------------|----------------------------------|----------------------------------|
| --bg         | #0e0f11                          | Page background                  |
| --surface    | #141518                          | Panel/sidebar background         |
| --raised     | #1a1b1f                          | Elevated surface                 |
| --accent     | #4ade80                          | Primary accent — CTAs, active states, trust signals |
| --accent-dim | #22c55e                          | Hover state for accent           |
| --accent-muted | rgba(74,222,128,0.15)          | Icon backgrounds, badges         |
| --accent-ghost | rgba(74,222,128,0.06)          | Subtle hover fills               |
| --t1         | rgba(240,242,238,0.88)           | Primary text                     |
| --t2         | rgba(240,242,238,0.55)           | Secondary text                   |
| --t3         | rgba(240,242,238,0.35)           | Muted text, labels               |
| --t4         | rgba(240,242,238,0.15)           | Ghost text, disabled, borders    |
| --line       | rgba(255,255,255,0.06)           | Borders, dividers                |

### Light

| Token        | Value                           | Usage                           |
|--------------|----------------------------------|----------------------------------|
| --bg         | #f4f5f0                          | Page background                  |
| --surface    | #eaebe5                          | Panel background                 |
| --raised     | #ffffff                          | Elevated surface                 |
| --accent     | #16a34a                          | Primary accent                   |
| --accent-dim | #15803d                          | Hover state                      |
| --t1         | rgba(14,15,17,0.88)              | Primary text                     |
| --t2         | rgba(14,15,17,0.55)              | Secondary text                   |
| --t3         | rgba(14,15,17,0.35)              | Muted text                       |
| --t4         | rgba(14,15,17,0.12)              | Ghost text                       |

### Provider Lane Colors

| Lane     | Dark      | Light     |
|----------|-----------|-----------|
| ChatGPT  | #4ade80   | #16a34a   |
| Claude   | #a78bfa   | #7c3aed   |
| Gemini   | #60a5fa   | #2563eb   |
| Native   | #60a5fa   | #2563eb   |

## Accent Rules

- Green (#4ade80) is the ONLY accent color
- No second accent. No wine. No gold.
- Green is used for: CTAs, active nav indicator, badges, lane stripes, links on hover, trust signals
- Never use green as a large background fill (only ghost/muted variants)

## Typography

### Font Stack

| Role       | Family                                              | Weight  | Usage                    |
|------------|-----------------------------------------------------|---------|--------------------------|
| Body       | -apple-system, BlinkMacSystemFont, system-ui, sans  | 400-600 | All reading text, nav, headings |
| Mono       | JetBrains Mono, ui-monospace, monospace             | 400-500 | IDs, timestamps, labels, code |
| Landing    | Outfit, sans-serif                                  | 300-600 | Landing page only        |

### Size Rules

| Element         | Size    | Weight | Notes              |
|-----------------|---------|--------|--------------------|
| Page heading    | 1.5rem  | 500    | System sans-serif  |
| Section heading | 17px    | 500    |                    |
| Nav link        | 14px    | 400    |                    |
| Body text       | 14-15px | 400    |                    |
| Mono label      | 11px    | 400    | Minimum size       |
| Sidebar brand   | 18px    | 600    | Distinct from nav  |

Absolute minimum font size: **11px**. Nothing smaller, ever.

## Logo

The SoulPrint logo is a stylized USB stick icon:
- Metal connector at top (gray, with cutout rectangle)
- Green body (#4ade80) below
- Center cutout (dark, matching background)
- Works at favicon size (16px) and hero size

### Usage Rules
- Primary color: green body with gray connector
- Minimum clear space: 8px on all sides
- Never stretch, rotate, or apply effects
- In the sidebar: 24px, paired with "SoulPrint" in 18px/600 weight

## Buttons

- Primary CTA: filled green background, dark text, 6px radius, 600 weight
- Secondary: transparent background, 1px border in --t4, --t1 text, 8px radius
- Inline actions: transparent with 1px green border, green text, 6px radius
- Ghost links: --t2 text, arrow suffix, hover to green
- No uppercase buttons. No letter-spacing on buttons.

## Critical Rules

- No serif fonts in the app UI
- No grain overlay, no vignette, no ember glow
- No radial gradient backgrounds
- No card shadows, no border-radius on flat panels
- No icons in nav — text only
- No decorative borders beyond 1px var(--line)
- No stock photos
- No emoji in the UI
- No "AI" as a visual motif (no robot icons, no brain icons, no sparkles)
- Trust-first: every design choice should make the user feel safe about their data
