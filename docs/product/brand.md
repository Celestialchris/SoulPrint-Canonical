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
| `/`               | Workspace                   | Search your archive           |
| `/ask`            | Ask your memory             | Ask your memory               |
| `/imported`       | What you've discussed       | What you've discussed         |
| `/chats`          | Your own notes              | Your own notes                |
| `/federated`      | Everything, together        | Everything, together          |
| `/intelligence`   | Recurring themes            | Recurring themes              |
| `/distill`        | Create a digest             | Create a digest               |
| `/answer-traces`  | How answers were found      | How answers were found        |
| `/import`         | Import                      | Bring conversations home      |
| `/passport`       | Take it with you            | Memory Passport               |

## Design System: Quiet Archive v3

**Authoritative doctrine:** [`docs/product/design-doctrine-quiet-archive.md`](design-doctrine-quiet-archive.md). **Live tokens:** `src/app/static/app.css`. If this file disagrees with either of the above, they win — this brand guide is a human-readable summary, not authority.

The design communicates trust, calm, and warm local ownership. SoulPrint is **a quiet archive** — a warm, intimate, lived-in place where a person keeps the record of their thinking. Not a utility, not a dashboard. A room with a lamp on.

**Design law:** *Glow for identity, flatness for usage.* Identity surfaces (wordmark, hero greeting, empty states, landing, summary / wrapped) earn tone — ember glow, gold leaf, serif display, generous negative space. Usage surfaces (conversation rows, message lists, stats, search results, traces) stay flat — hairline dividers, mono labels, tabular nums, no cards wrapping rows, no shadows.

### Color Tokens — Dark Theme (default)

| Token             | Value                            | Usage                                             |
|-------------------|----------------------------------|---------------------------------------------------|
| `--bg-darkest`    | `#0F0D0B`                        | Rail, search input, body canvas                   |
| `--bg-dark`       | `#151210`                        | Sidebar, stat cards, context panel, row hover     |
| `--bg-mid`        | `#1B1714`                        | Main content area                                 |
| `--bg-light`      | `#26211D`                        | Default rail icon, context tags, `⌘K` chip        |
| `--bg-hover`      | `#2E2823`                        | Sidebar item hover, ghost button hover            |
| `--accent`        | `#A25B47`                        | Clay — CTAs, active nav, focus rings, highlights  |
| `--accent-dim`    | `#8E5748`                        | CTA hover, focused input border                   |
| `--accent-soft`   | `rgba(162,91,71,0.12)`           | Active sidebar item background, selection tint    |
| `--accent-glow`   | `rgba(162,91,71,0.05)`           | Ambient warm glow on identity surfaces only       |
| `--wordmark-gold` | `#E7C98A`                        | Landing-page wordmark + any identity-surface "SoulPrint" |
| `--wordmark-glow` | `rgba(231,201,138,0.28)`         | Torchlit ember glow around wordmark               |
| `--green`         | `#23955D`                        | "Local-first" status dot only — not brand         |
| `--t1`            | `rgba(244,238,229,0.92)`         | Primary text (warm cream)                         |
| `--t2`            | `rgba(244,238,229,0.62)`         | Secondary text                                    |
| `--t3`            | `rgba(244,238,229,0.34)`         | Muted text, mono labels                           |
| `--t4`            | `rgba(244,238,229,0.16)`         | Disabled, decorative lines                        |
| `--line`          | `rgba(244,238,229,0.08)`         | Standard dividers                                 |
| `--line-strong`   | `rgba(244,238,229,0.14)`         | Ghost-button border, stat-card hover              |

### Color Tokens — Light Theme (`[data-theme="light"]`)

| Token             | Value                            |
|-------------------|----------------------------------|
| `--bg-darkest`    | `#F4EFE5`                        |
| `--bg-dark`       | `#ECE6D9`                        |
| `--bg-mid`        | `#FFFFFF`                        |
| `--accent`        | `#8E4F3E`                        |
| `--wordmark-gold` | `#B08A3E`                        |
| `--green`         | `#16a34a`                        |

Light is the toggle variant, not the default. Every dark-theme token has a light-theme counterpart in `app.css`.

### Provider Lanes

Lane colors mark **data identity**, not brand. They are intentionally muted so they sit *behind* the clay accent rather than compete with it.

| Provider      | Dark       | Light      | Note                          |
|---------------|------------|------------|-------------------------------|
| `--lane-chatgpt` | `#23955D`  | `#1C7A4C`  | Deeper OpenAI green           |
| `--lane-claude`  | `#C69224`  | `#A7791E`  | Warmer Anthropic gold         |
| `--lane-gemini`  | `#2D6FE8`  | `#235FCC`  | Slightly desaturated Google blue |
| `--lane-native`  | `#2D6FE8`  | `#235FCC`  | Matches Gemini for now        |
| `--lane-grok`    | `#6F47E6`  | `#5B3BC0`  | xAI violet (dormant)          |

### Typography

| Role    | Family              | Use                                      |
|---------|---------------------|------------------------------------------|
| Display | `Playfair Display`  | Wordmark, hero headings, identity surfaces |
| Body    | `DM Sans`           | All reading text, nav labels, buttons    |
| Mono    | `JetBrains Mono`    | IDs, timestamps, labels, small caps      |

All three families are **bundled locally** under `src/app/static/fonts/`. No CDN calls, no Google Fonts network request at runtime. This is non-negotiable — it matches SoulPrint's "nothing leaves your machine" promise.

### Visual rules

- No box-shadows on data surfaces. Shell surfaces may use a subtle radial glow on identity areas only.
- No icons in nav labels — text carries meaning.
- Font weight never above 600 (DM Sans 600 is the heaviest used).
- Rows are flat with `border-bottom` dividers, never card-wrapped.
- Content sits on the dark canvas with typography and spacing creating structure, not decoration.

## Design system lineage

The active system (Quiet Archive v3) supersedes two prior systems. The history matters for anyone reading old PRs, old CHANGELOG entries, or archived docs:

- **Quiet Archive v3** — `v0.7.0-alpha.1+`. *Active.* Clay accent on warm-black parchment, gold wordmark. This document.
- **Magenta Sanctum v2** — `v0.6.0` – `v0.6.1`. *Retired.* Pink (`#f472b6`) accent on near-black (`#111113`). Doctrine archived under `docs/archive/design-doctrine-magenta-sanctum.md`.
- **USB Drive** — `v0.1.0` – `v0.5.x`. *Retired.* Green (`#4ade80`) accent, hardware-adjacent flatness. Spec archived under `docs/archive/dual-theme-spec.md`.

The supersession chain is recorded in `DECISIONS.md` under the Design section.
