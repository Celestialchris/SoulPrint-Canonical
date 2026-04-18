# SoulPrint Visual Direction

Doctrine files are not aesthetic playgrounds.

Do not alter product architecture, lane honesty, provenance display rules, or workflow structure in the name of style.

## Design system authority

The live `src/app/static/app.css` is always the authoritative source for design tokens, colors, fonts, and spacing. If this file and any documentation file disagree, the CSS wins.

**Current system: Quiet Archive v3** (since `v0.7.0-alpha.1`). Authoritative doctrine: [`docs/product/design-doctrine-quiet-archive.md`](design-doctrine-quiet-archive.md).

**Lineage** (most recent first):

- **Quiet Archive v3** — `v0.7.0-alpha.1+`. Clay accent (`#A25B47`) on warm-black parchment (`#0F0D0B`). Gold wordmark (`#E7C98A`). A lived-in personal archive.
- **Magenta Sanctum v2** — `v0.6.0` – `v0.6.1`. *Retired.* Pink (`#f472b6`) accent on near-black. Doctrine file archived under [`docs/archive/design-doctrine-magenta-sanctum.md`](../archive/design-doctrine-magenta-sanctum.md).
- **USB Drive** — `v0.1.0` – `v0.5.x`. *Retired.* Green (`#4ade80`) accent, hardware-adjacent flatness. Spec archived under [`docs/archive/dual-theme-spec.md`](../archive/dual-theme-spec.md).

The supersession chain is recorded in `DECISIONS.md` under the Design section.

## Where aesthetic prompting applies

Use aesthetic prompting only for:

- visual rhythm and spacing
- empty-state warmth
- brand atmosphere
- summary / wrapped / landing pages
- tasteful micro-interactions

## Where aesthetic prompting must never apply

Never use aesthetic prompting to redefine:

- route structure
- information architecture
- transcript explorer behavior
- import UX logic
- answer-trace trust model
- canonical vs derived boundaries

## UI style rules

SoulPrint should feel:

- calm
- fluid
- low-clutter
- readable
- warm
- trustworthy
- obvious to navigate

Avoid:

- dashboard bloat
- metrics theater
- noisy admin-panel energy
- ornamental AI gimmicks
- scroll-scroll-scroll transcript hell

## The two-layer principle

**Layer 1** (doctrine, architecture, execution) always wins.

**Layer 2** (visual direction, aesthetic polish) may only enhance finish without creating drift.

If style conflicts with clarity, choose clarity.
