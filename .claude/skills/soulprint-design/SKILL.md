---
name: soulprint-design
description: SoulPrint-specific visual direction and UI doctrine. Activates for all frontend, template, and CSS work in this repo.
---

# SoulPrint Design Skill

## Identity
SoulPrint is a local-first memory continuity system. The UI must feel
like a calm, trustworthy product — not a developer tool, not a dashboard,
not an AI gimmick.

## Visual DNA
- Warm parchment palette (existing: --bg: #f2f0e9, --surface: rgba(255,253,248,0.94))
- Lane-colored badges: native=blue, imported=green, derived=amber
- Apple-like restraint: generous whitespace, obvious navigation, no clutter
- Typography: clean sans-serif, clear hierarchy, readable at all sizes
- Cards with subtle shadows, rounded corners (existing --radius-lg: 18px)
- No metrics theater, no ornamental AI gimmicks, no admin-panel energy

## Design Rules
1. Every surface answers: What am I looking at? Where did it come from? Where can I go next?
2. Canonical vs derived must be visually distinct (badges, not just labels)
3. Transcript explorer: TOC on side, clean reading pane, minimap rail
4. Empty states are calm and helpful, never sad or broken-looking
5. Navigation is obvious — user never wonders "how do I go back?"
6. Search should land you at the right place fast

## Anti-Patterns
- No giant sidebars stuffed with noise
- No "AI everywhere" visual gimmicks
- No cluttered admin panels
- No metrics/charts unless they serve the continuity story
- No dark mode yet (keep light, warm, parchment-first)

## Current Surfaces (all need consistent treatment)
- / (Workspace)
- /import
- /ask
- /passport
- /intelligence (Notes — summaries, topics, digests)
- /imported, /imported/<id>/explorer
- /federated
- /chats, /memory/<id>
- /answer-traces, /answer-traces/<id>

## When restyling
- Read src/app/static/app.css first (1005 lines, existing design tokens)
- Preserve all CSS custom properties (--bg, --surface, --border, etc.)
- Extend the existing system, don't replace it
- Keep server-rendered Jinja templates for now
- Every visual change must work at 1200px, 768px, and 480px widths