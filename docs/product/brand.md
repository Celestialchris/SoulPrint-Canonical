# SoulPrint — Brand Guide

## Mission

Every person should own their AI memory.

## Tagline

Your AI conversations are scattered everywhere. SoulPrint brings them home.

## Voice

- Calm, confident, technical but not cold
- Trustworthy — we handle people's conversation history
- Never corporate, never salesy
- Direct without being terse
- Warm without being cutesy
- Use "your" not "the user's" — speak to people, not about them

## Product Name

**SoulPrint** — one word, capital S, capital P.
Never: Soul Print, soul print, SOULPRINT, SP.

## Logo

The SoulPrint logo is a stylized fingerprint mark composed of concentric
arcs that suggest both identity (fingerprint) and conversation (speech
bubble rhythm). It works at favicon size (16px) and hero size (200px+).

### Usage Rules
- Primary color: accent blue-grey (#3f5f73)
- Monochrome variant: var(--text) for dark contexts
- Minimum clear space: equal to the logo's width on all sides
- Never stretch, rotate, or apply effects to the logo
- Always pair with the wordmark "SoulPrint" in body text — the mark alone
  is for favicons and compact contexts only

## Color Palette

### Core
| Token             | Value                        | Usage                        |
|-------------------|------------------------------|------------------------------|
| --bg              | #f2f0e9                      | Page background              |
| --surface         | rgba(255, 253, 248, 0.94)    | Card/panel background        |
| --text            | #1f2933                      | Primary text                 |
| --text-secondary  | #3d4f5f                      | Secondary body text          |
| --muted           | #667085                      | Metadata, labels, timestamps |
| --accent          | #3f5f73                      | Links, primary actions, logo |
| --accent-hover    | #2e4d5f                      | Hover state for accent       |
| --accent-soft     | #e8eef2                      | Active nav pill, light accent bg |

### Lane Colors
| Lane     | Background | Border   | Text    |
|----------|------------|----------|---------|
| Native   | #eef5fa    | #c2d6e3  | #2e5068 |
| Imported | #eff6f0    | #c4d8c4  | #3a5a3a |
| Derived  | #f9f2e8    | #e0c6a5  | #6d5030 |

### Surfaces
| Token        | Value                                              |
|--------------|----------------------------------------------------|
| --border     | #d7d0c2                                            |
| --border-strong | #c4bcae                                         |
| --shadow     | 0 1px 3px rgba(54,61,66,0.04), 0 6px 16px rgba(54,61,66,0.05) |
| --shadow-hover | 0 2px 6px rgba(54,61,66,0.06), 0 12px 28px rgba(54,61,66,0.1) |

## Typography

### App (all surfaces)
```
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", Inter,
             "Segoe UI", system-ui, sans-serif;
```

### Monospace (code blocks, IDs)
```
font-family: "SF Mono", ui-monospace, SFMono-Regular, Consolas,
             "Liberation Mono", monospace;
```

### Scale
| Element        | Size           | Weight | Letter-spacing |
|----------------|----------------|--------|----------------|
| Page title     | clamp(1.5-2.1rem) | 700 | -0.02em       |
| Section heading | 1.05rem       | 600    | -0.01em        |
| Card title     | 1rem           | 600    | 0              |
| Body text      | 0.92rem        | 400    | 0              |
| Eyebrow/label  | 0.72rem        | 600    | 0.1em          |
| Badge          | 0.72rem        | 600    | 0.02em         |

## Iconography

- No icon library — keep surfaces text-driven
- Arrow glyphs (unicode) for navigation: <- back, -> forward
- Minimal decorative elements

## Photography & Imagery

- No stock photos
- Screenshots should show real (or realistic) conversation data
- Landing page hero: workspace with populated data, not empty states

## Do Not

- Use gradients on text
- Use drop shadows heavier than the defined tokens
- Add decorative borders or dividers between sections
- Use emoji in the UI (unless user-generated content contains them)
- Use "AI" as a visual motif (no robot icons, no brain icons, no sparkles)
