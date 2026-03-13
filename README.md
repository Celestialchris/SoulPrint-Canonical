# SoulPrint

Your AI conversations are scattered everywhere. SoulPrint brings them home.

SoulPrint is a local-first memory continuity system for AI users. It imports conversation history from multiple providers, preserves it in a canonical local ledger, lets you inspect and search it with provenance, answers from it conservatively, and exports or validates it as a Memory Passport. The system stays grounded in local ownership: canonical SQLite records remain authoritative, and every derived result traces back to stable IDs and timestamps.

## What It Is Not

- Not a hosted SaaS
- Not a mem0 clone
- Not an AI dashboard

## Product Loop
See `docs/product/positioning.md` for the practical doctrine and boundaries.
See `docs/specs/memory-passport-spec.md` for the formal v1 Memory Passport package contract.

Import -> Inspect -> Search -> Answer -> Export / Validate

## What Works Today

- Three-provider import with auto-detection
- Canonical SQLite ledger with explicit native/imported lanes
- Transcript explorer with prompt-level TOC and minimap rail
- Federated cross-lane retrieval
- Grounded local answering with citation provenance
- Answer trace audit residue
- Citation-to-record handoff
- Memory Passport export
- Memory Passport validation
- Shared app shell with calm, low-clutter visual grammar

## Main Surfaces

| Surface | Purpose |
| --- | --- |
| `/` | Shared workspace surface with ledger and activity overview |
| `/import` | Live web import surface for supported conversation export JSON files |
| `/ask` | Live in-app Ask surface for grounded answers with trace and citation handoff |
| `/passport` | Live capability/status surface for Memory Passport export and validation; current web scope does not inspect a specific artifact |
| `/chats` | Native memory lane browser |
| `/imported` | Imported conversation list and search |
| `/imported/<id>/explorer` | Transcript explorer for one imported conversation |
| `/federated` | Cross-lane retrieval with explicit provenance |
| `/answer-traces` | Derived answer trace audit browser |

## Repo Map

- `src/app/` Flask app shell, browsing surfaces, and handoff views
- `src/importers/` provider adapters, auto-detection, and persistence
- `src/retrieval/` federated retrieval across explicit storage lanes
- `src/answering/` grounded answering and derived trace residue
- `src/passport/` Memory Passport export and validation
- `docs/` product doctrine, operator guides, and specifications

## Current State — March 13, 2026

- 216 passing tests
- 3 provider importers (ChatGPT, Claude, Gemini) with auto-detection
- 9 web surfaces (Workspace, Import, Ask, Notes, Passport, Imported, Federated, Native Memory, Answer Traces)
- Intelligence layer: per-conversation summaries, cross-conversation topic detection, digest synthesis
- Memory Passport export + validation
- Grounded answering with citation handoff and trace audit
- Design system: "Torchlit Vault" — dark warm palette, Forum/Cormorant Garamond/JetBrains Mono typography, hierarchy through opacity

## Architecture

```
Layer A — Truth         Canonical SQLite ledger. Explicit lanes. Stable provenance.
Layer B — Legibility    Browse, search, inspect, trace, export. Read-only over truth.
Layer C — Intelligence  Summaries, topics, digests, continuity packets. All derived. All traceable.
Layer D — Distribution  Desktop app, landing page, installer, freemium gate.
```

Build sequence: truth → legibility → intelligence → distribution.
Current position: Layer C (continuity packets), then Layer D.

## Next Milestone

**Continuity Packet MVP** — convert finished conversations into structured handoff packets that can seed the next chat without dragging 100k tokens forward. See `ROADMAP.md` for the full sequence.

---

## Project Knowledge Index

### Root

| File | Purpose |
|------|---------|
| `README.md` | This file. Project map and current state. |
| `DECISIONS.md` | Frozen decisions log. What has been decided and should not be revisited. |
| `ROADMAP.md` | Sequenced build plan with phases and priorities. |

### `roadmap/` — Planning Documents

| File | Purpose |
|------|---------|
| `30-DAY-VISION.md` | Full 30-day product vision: brand, landing page, desktop, freemium, wrapped summary. |
| `UPGRADE-CONTINUITY.md` | Continuity packet architecture: session handoff, lineage model, bridge assembly, engine choice. |
| `BRAND-PROMPTS.md` | 5 sequential Claude Code prompts for distribution features. Execute in order after continuity MVP. |

### `design/` — Visual Direction

| File | Purpose |
|------|---------|
| `TORCHLIT-VAULT-SPEC.md` | Canonical design system specification. Colors, typography, components, 9 surface layouts. **This is the design contract.** |
| `DESIGN-MARKET-ANALYSIS.md` | Marketability analysis. Two-personality brand (public lucid / inner glow), commercial positioning. |
| `UX-REVIEW.md` | Senior PM review. Hierarchy critique, nav grouping, glow grammar, provenance components. |
| `heritage/thraenix-reference.html` | Single consolidated Thraenix design DNA file. Source of Forum font, dark gradient, gold glow treatment. Reference only. |

---

## Doctrine

Canonical records stay authoritative. Derived intelligence is always labeled, traceable, and rebuildable from stable IDs and timestamps. Local-first means no data leaves the machine. The product is calm before clever.

See `DECISIONS.md` for the full list of frozen architectural and design decisions.

The next engineering milestone is to generate compact, provenance-bound continuity packets from canonical conversations. These packets will act as derived handoff artifacts for starting fresh chats without dragging full long-context history forward.

Sequence:
- Continuity packet generation
- Bridge assembly for next-chat handoff
- Lineage suggestions between related threads
- Design and distribution work after the continuity spine is in place

---

## Docs

- [Getting started](docs/getting-started.md)
- [Product positioning](docs/product/positioning.md)
- [Product context](docs/product/context.md)
- [Memory Passport spec](docs/specs/memory-passport-spec.md)

## License / Contributing

SoulPrint is available under the Apache License 2.0. See [LICENSE](LICENSE). For contribution rules and review expectations, see [CONTRIBUTING.md](CONTRIBUTING.md).
