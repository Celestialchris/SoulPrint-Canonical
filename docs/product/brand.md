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

| Route             | Old Label          | Warm Label                  |
|-------------------|--------------------|-----------------------------|
| `/`               | Workspace          | Workspace                   |
| `/chats`          | Native Memory      | Your own notes              |
| `/imported`       | Imported           | What you've discussed       |
| `/import`         | Import             | Import                      |
| `/federated`      | Federated          | Everything, together        |
| `/passport`       | Passport           | Take it with you            |
| `/ask`            | Ask                | Ask your memory             |
| `/intelligence`   | Notes              | Themes & patterns           |
| `/answer-traces`  | Answer Traces      | How answers were found      |

## Color Palettes

### Dark — "Torchlit Vault" (default)

| Token         | Value                          | Usage                            |
|---------------|--------------------------------|----------------------------------|
| --bg          | #0e0d0b                        | Page background                  |
| --surface     | #161513                        | Panel background                 |
| --raised      | #1d1b18                        | Elevated surface                 |
| --wine        | #6b3a3a                        | Primary accent                   |
| --wine-soft   | #8a5050                        | Hover / soft accent              |
| --gold        | #c9a84c                        | Bright highlight accent          |
| --gold-dim    | #a08848                        | Logo, active nav, subtle gold    |
| --t1          | rgba(210, 200, 185, 0.90)      | Primary text                     |
| --t2          | rgba(210, 200, 185, 0.55)      | Secondary text                   |
| --t3          | rgba(210, 200, 185, 0.30)      | Muted text, labels               |
| --t4          | rgba(210, 200, 185, 0.12)      | Ghost text, disabled             |
| --line        | rgba(210, 200, 185, 0.06)      | Borders, dividers                |

### Light — "Parchment Observatory"

| Token         | Value                          | Usage                            |
|---------------|--------------------------------|----------------------------------|
| --bg          | #f2f0e9                        | Page background                  |
| --surface     | rgba(255, 253, 248, 0.94)      | Panel background                 |
| --raised      | #ffffff                        | Elevated surface                 |
| --wine        | #6b3a3a                        | Primary accent                   |
| --wine-soft   | #8a5050                        | Hover / soft accent              |
| --gold        | #8a7230                        | Bright highlight accent          |
| --gold-dim    | #7a6528                        | Logo, active nav, subtle gold    |
| --t1          | #1f2933                        | Primary text                     |
| --t2          | #3d4f5f                        | Secondary text                   |
| --t3          | #667085                        | Muted text, labels               |
| --t4          | #a0a8b4                        | Ghost text, disabled             |
| --line        | #d7d0c2                        | Borders, dividers                |

## Provider Lane Colors

### Dark mode

| Lane     | Value     |
|----------|-----------|
| ChatGPT  | #5a8a6a   |
| Claude   | #a08848   |
| Gemini   | #5a7a9a   |
| Native   | #5a7a9a   |

### Light mode

| Lane     | Value     |
|----------|-----------|
| ChatGPT  | #3a6a4a   |
| Claude   | #7a6528   |
| Gemini   | #3a5a7a   |
| Native   | #3a5a7a   |

## Accent Rules

- Wine (#6b3a3a) and gold (#c9a84c / #a08848) are the only accent colors
- Wine is the primary accent — used for interactive elements, selection highlights
- Gold is the secondary accent — used for logo, active nav states, subtle highlights
- Never mix accents with lane colors
- Never use accents as background fills on large areas

## Typography

### Font Stack

| Role       | Family                          | Weight | Usage                    |
|------------|--------------------------------|--------|--------------------------|
| Wordmark   | Forum, serif                   | 400    | "SoulPrint" brand text   |
| Body       | Cormorant Garamond, serif      | 400–500| All reading text, nav    |
| Mono       | JetBrains Mono, monospace      | 400    | IDs, timestamps, labels  |

### Base Size

`font-size: 17px` on `html`.

### Scale

| Element         | Size       | Weight | Letter-spacing |
|-----------------|------------|--------|----------------|
| Page heading    | 1.35rem    | 400    | 0              |
| Section label   | 0.6rem     | 400    | 0.18em         |
| Nav link        | 0.92rem    | 500    | 0              |
| Body text       | 1rem       | 400    | 0              |
| Mono label      | 0.6rem     | 400    | 0.04em         |

## Hero Wordmark

In dark mode, the "SoulPrint" wordmark uses:
- Font: Forum, serif
- Color: var(--gold-dim) / #a08848
- Letter-spacing: 1.5px
- Weight: 400

No glow, gradient, or text-shadow in light mode.

## Body Atmosphere

### Dark mode

Background is layered radial gradients over --bg:
- Gold warmth at top-left (opacity ~0.02)
- Wine warmth at top-right (opacity ~0.015)
- Dark vignette at center-bottom (opacity ~0.58)
- Amber warmth at bottom-left (opacity ~0.03)

Grain overlay: fractal noise SVG at opacity 0.018, fixed position.
Vignette: vertical linear gradient fading to black at top (0.16) and bottom (0.22).

### Light mode

No grain, no vignette. Clean, flat parchment background.

## Selection Colors

```css
/* Dark */
::selection { background: rgba(107, 58, 58, 0.30); }

/* Light */
::selection { background: rgba(107, 58, 58, 0.18); }
```

## Logo

The SoulPrint logo is a stylized fingerprint mark composed of concentric
arcs that suggest both identity (fingerprint) and conversation (speech
bubble rhythm). It works at favicon size (16px) and hero size (200px+).

### Usage Rules
- Primary color: gold-dim (#a08848)
- Monochrome variant: var(--t1) for high-contrast contexts
- Minimum clear space: equal to the logo's width on all sides
- Never stretch, rotate, or apply effects to the logo
- Always pair with the wordmark "SoulPrint" in body text — the mark alone
  is for favicons and compact contexts only

## Critical Rules

- No card components — use flat rows with line dividers
- No badge components — use inline mono labels
- No box-shadows — use border-bottom or var(--line) dividers only
- No icons in nav — text only
- No font-weight above 500
- No decorative borders or dividers beyond 1px var(--line)
- No stock photos
- No emoji in the UI (unless user-generated content contains them)
- No "AI" as a visual motif (no robot icons, no brain icons, no sparkles)

## Wordmark Glow — "Embers in Velvet Darkness"

The SoulPrint wordmark glow is not a neon effect. It is a controlled incandescent bloom with typographic anchor.

### Why it works

The glow is five-layer and decaying. The innermost shadow (1px, high opacity warm white) creates a white-hot edge hugging the letterforms — this is what produces the "heated from within" look. Without it, the text has a distant haze instead of radiating heat. The second layer (6px, bright incandescent orange) is the primary visible bloom; it must be tight and hot. The middle layers create atmospheric spread at increasing distance. The outermost dark shadow anchors the letters so they do not dissolve. Without the black under-shadow, the text looks cheap.

The close bloom uses incandescent orange — the same spectrum as heated metal. On the near-black background, this reads as furnace heat, not neon. The tight blur radius (6px) keeps the glow hugging the letterforms rather than floating free.

Forum does half the work. Its high-contrast serif forms catch the glow on thin-thick transitions, producing a "sacred manuscript in firelight" quality. A sans-serif with the same shadow would not produce the same effect.

The page background completes the illusion. The glow sits over layered radial gradients, grain, and vignette — not flat black. The light belongs to an environment, which is why the word looks lit from within rather than simply blurred.

### CSS specification

```css
.hero-name {
  color: var(--t1);                              /* warm white, NOT gold */
  font-family: var(--font-display);              /* Forum */
  text-shadow:
    0 0 1px rgba(245, 240, 234, 0.82),           /* white-hot edge — crisp incandescent core */
    0 0 6px rgba(255, 69, 0, 0.88),              /* close bloom — tight, hot, hugs letterforms */
    0 0 16px rgba(255, 69, 0, 0.48),             /* medium atmospheric — visible spread */
    0 0 34px rgba(255, 69, 0, 0.18),             /* ambient warmth — soft outer haze */
    0 2px 4px rgba(0, 0, 0, 0.4);                /* typographic anchor — keeps letters grounded */
}
```

### Constraint language for any model or contributor

Keep the title glow subtle and aristocratic, like heated metal or candlelit amber in a dark chapel. Avoid neon, avoid cyberpunk blue/orange, avoid blur-heavy haze. The letters must stay crisp at the core, with a soft layered bloom and a faint dark anchor shadow underneath.

### What to never do

- Never increase blur radius beyond 40px on the outermost color layer
- Never widen the close bloom beyond 8px blur — the glow must hug the letterforms
- Never use blue-spectrum, green-spectrum, or cool-toned glow colors
- Never remove the dark anchor shadow (the `0 2px 4px rgba(0,0,0,0.4)`)
- Never apply this glow to body text, nav items, or any element besides the hero wordmark and the app workspace heading
- Never use a sans-serif font with this shadow stack
- Never add more than five shadow layers — the stack is tuned, not additive

The glow works because it is disciplined. It is not shouting. It is smoldering.
