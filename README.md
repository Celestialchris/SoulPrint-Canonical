# SoulPrint

[![Tests](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml/badge.svg)](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**Your AI conversations are scattered everywhere. SoulPrint brings them home.**

A local-first memory continuity system. Import your AI conversation history from ChatGPT, Claude, and Gemini. Browse, search, discover themes, ask questions, and export a verifiable Memory Passport. Everything stays on your machine. Nothing is hosted. Your archive is yours.

---

## Quick Start

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical

pip install -r requirements.txt

python -m src.run
# Open http://127.0.0.1:5678
```

Drop an export file on the Import page. Your conversations appear in seconds.

---

## Why I Built This

I've been using ChatGPT, Claude, and Gemini daily for over a year. My conversation history & ideas, decisions, research threads, creative work is scattered across three platforms that don't talk to each other. Their exports are barely usable zip files that sit dead on disk.

Nobody was building a tool to bring all of that together locally, with provenance, intelligence, and real exportability. So I built one.

SoulPrint is not a hosted service that wants to hold your data. It's a local tool that treats your AI memory the way it should be treated: as yours.

---

## What SoulPrint Does

**Import** — Drop your ChatGPT `.zip`, Claude `.json`, or Gemini Takeout. Provider is auto-detected. Normalized into one local archive with duplicate guards.

**Browse** — Workspace dashboard, imported conversations by provider, transcript explorer with prompt-level TOC and minimap, native notes, cross-provider view. Every record carries stable IDs, timestamps, and source tracking.

**Search** — Full-text across all conversations, all providers. Search your notes and imported history together or separately.

**Ask** — Answers grounded in your own conversation record. Every answer cites specific conversations. Every answer has an auditable trace. Statuses: `grounded`, `ambiguous`, or `insufficient_evidence`.

**Discover** — Cross-conversation topic detection. Per-conversation summaries. Multi-conversation digests and distillation. Continuity packets for handoff into new chats. All generated, all traceable to source.

**Export** — Memory Passport with manifest, JSONL lanes, provenance index, and checksums. Validate any exported passport against the current contract.

---

## What SoulPrint Is Not

- **Not a hosted SaaS** — your data never leaves your machine
- **Not a mem0 clone** — SoulPrint is for users, not developer infrastructure
- **Not an AI dashboard** — no metrics theater, no admin-panel energy
- **Not a generic wrapper** — SoulPrint has its own local archive and trust chain

---

## Providers

| Provider | Format | Status |
|----------|--------|--------|
| ChatGPT | `.zip` export from OpenAI | ✓ Supported |
| Claude | `.json` export from Anthropic | ✓ Supported |
| Gemini | Google Takeout or Chrome extension JSON | ✓ Supported |

Adding a provider is bounded work: adapter, detector, registry entry, fixture, tests. The architecture supports unlimited providers.

---

## Intelligence (BYOK)

SoulPrint's intelligence features use your own API key. Configure once:

```bash
export SOULPRINT_LLM_PROVIDER=openai      # or: anthropic
export SOULPRINT_LLM_API_KEY=sk-...
```

Without a key, import, browse, search, and export all work fully. Intelligence features (summaries, topics, digests, ask, continuity packets) require a configured provider.

---

## Surfaces

| Route | What it does |
|-------|--------------|
| `/` | Workspace — overview, provider coverage, recent activity |
| `/import` | Import conversations from any supported provider |
| `/ask` | Ask questions answered from your conversation record (Pro) |
| `/intelligence` | Summaries, topic scans, and cross-conversation digests (Pro) |
| `/distill` | Multi-conversation distillation (Pro) |
| `/imported` | Browse imported conversations by provider |
| `/imported/<id>/explorer` | Transcript explorer with prompt-level TOC and minimap |
| `/federated` | Cross-provider view — search everything together |
| `/chats` | Native memory — notes created directly in SoulPrint |
| `/passport` | Export and validate your Memory Passport |
| `/answer-traces` | Audit trail for every generated answer |
| `/summary` | Your AI Memory — cinematic summary page |

---

## Architecture

```
Layer A — Truth         SQLite ledger. Explicit lanes. Stable provenance.
Layer B — Legibility    Browse, search, inspect, trace, export. Read-only over truth.
Layer C — Intelligence  Summaries, topics, digests, continuity. All derived. All traceable.
Layer D — Distribution  Web app, CLI, landing page, freemium gate.
```

Every derived artifact stores: source conversation stable IDs, generation timestamp, LLM provider used, and prompt template version. Derived never impersonates canonical.

---

## Repo Map

```
src/
├── app/            Flask web app, templates, static assets, viewmodels
├── importers/      Provider adapters, auto-detection, persistence, query
├── retrieval/      Federated retrieval across storage lanes
├── answering/      Grounded answering, trace audit, CLI
├── intelligence/   Summaries, topics, digests, continuity engine
├── obsidian/       Obsidian vault export bridge
├── passport/       Memory Passport export and validation
└── tools/          Memory query and tag validation utilities

tests/              51 test files, 537 test methods
sample_data/        Synthetic provider fixtures (ChatGPT, Claude, Gemini)
docs/               Architecture, specs, product docs, brand guide
landing/            Static landing page
```

---

## Tests

```bash
python -m pytest tests/ -v
```

51 test files covering parsing, persistence, retrieval, intelligence, continuity, distillation, passport, CLI, and browser integration.

---

## CLI Tools

```bash
# Import conversations
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db

# Query imported conversations
python -m src.importers.query_cli --db instance/soulprint.db list
python -m src.importers.query_cli --db instance/soulprint.db search "trip"

# Federated search
python -m src.retrieval.cli --db instance/soulprint.db "search term"

# Grounded answering
python -m src.answering.cli --db instance/soulprint.db "What do I have about Lisbon?"

# Export Memory Passport
python -m src.passport.cli exports/passports --db instance/soulprint.db

# Validate a passport
python -m src.passport.cli validate exports/passports/memory-passport-v1
```

---

## Project Status

| Component | State |
|-----------|-------|
| Canonical SQLite ledger | ✓ Stable |
| 3-provider import (ChatGPT, Claude, Gemini) | ✓ Stable |
| 16+ web surfaces | ✓ Stable |
| Intelligence layer (summaries, topics, digests) | ✓ Stable |
| Continuity engine (packets, bridges, lineage) | ✓ Stable |
| Multi-conversation distillation | ✓ Stable |
| Memory Passport export + validation | ✓ Stable |
| Grounded answering + audit traces | ✓ Stable |
| Freemium gate (local license key) | ✓ Shipped |
| Landing page | ✓ Shipped |
| Summary/Wrapped page | ✓ Shipped |
| Desktop wrapper | Planned |

---

## Roadmap

See [`ROADMAP.md`](ROADMAP.md) for the sequenced build plan and [`DECISIONS.md`](DECISIONS.md) for frozen architectural decisions.

---

## Docs

- [Getting started](docs/getting-started.md)
- [Product positioning](docs/product/positioning.md)
- [Brand guide](docs/product/brand.md)
- [Memory Passport spec](docs/specs/memory-passport-spec.md)
- [Answering boundary](docs/architecture/answering-boundary.md)
- [Visual direction](docs/product/visual-direction.md)

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The short version: small PRs, tests required, no speculative architecture.

---

## License

Apache-2.0 — [inspect the code yourself](LICENSE).

---

*Built with local-first principles. Your memory, under your custody.*
