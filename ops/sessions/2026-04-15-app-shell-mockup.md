# Session: App Shell Mockup

## Goal
Design a real search-first SoulPrint app shell mockup without touching the Flask backend, schema, importer, retrieval, or answer semantics.

## What changed
- Added an isolated app shell prototype at `docs/design/soulprint-app-shell/`
- Reused shared design tokens from `docs/design/soulprint-visual-directions/tokens.css`
- Implemented one search-first shell with:
  - dominant search canvas
  - provider filter row
  - recent imports strip
  - recovered results area
  - contextual provenance inspector
  - empty archive state

## Product choices
- Quiet Archive is the structural base
- Soft Intelligence warmth is used only in spacing and material softness
- Modern Study rigor is used only in selective header emphasis
- MCP remains advanced and downstream
- no stats-first hero
- no dashboard card carpet

## Mapping note
- mockup structure is intentionally close to Flask + Jinja2 partials:
  - left rail
  - top search section
  - provider filter partial
  - recent imports partial
  - results list partial
  - contextual inspector partial
  - empty-state partial
