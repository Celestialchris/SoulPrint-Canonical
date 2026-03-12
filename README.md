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
| `/` | Shared home surface with ledger and activity overview |
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

## Current Priority

Product coherence, not capability breadth. The immediate focus is aligning the shared workspace, import lifecycle, in-app Ask, and Passport surface around the canonical ledger that already exists.

## Docs

- [Getting started](docs/getting-started.md)
- [Product positioning](docs/product/positioning.md)
- [Product context](docs/product/context.md)
- [Memory Passport spec](docs/specs/memory-passport-spec.md)

## License / Contributing

SoulPrint is available under the Apache License 2.0. See [LICENSE](LICENSE). For contribution rules and review expectations, see [CONTRIBUTING.md](CONTRIBUTING.md).
