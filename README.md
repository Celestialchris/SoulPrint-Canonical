# SoulPrint

[![Tests](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml/badge.svg)](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**Your AI conversations are scattered everywhere. SoulPrint brings them home.**

Import your conversation history from ChatGPT, Claude, and Gemini into one
local archive. Browse, search, discover themes, ask questions with citations,
and export a verifiable Memory Passport. Everything stays on your machine.

## Screenshots

![Workspace](docs/screenshots/workspace.png)

![Import](docs/screenshots/import.png)

---

## Quick Start

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical
pip install -r requirements.txt
python -m src.run
# → http://127.0.0.1:5678
```

Drop an export file on the Import page. Your conversations appear in seconds.

---

## Why This Exists

I use ChatGPT, Claude, and Gemini every day. My conversation history —
research, decisions, creative work — is scattered across three platforms
that don't talk to each other. Their exports sit dead on disk as unusable
zip files.

In March 2026, Google and Anthropic both launched features to import your
AI conversations — into *their* silos. SoulPrint does the opposite: it
gives you a local file you own, with provenance you can verify, and
intelligence you can export.

---

## What It Does

**Import** — Drop a ChatGPT `.zip`, Claude `.json`, or Gemini Takeout.
Auto-detected. Deduplicated.

**Browse** — Workspace dashboard, conversation list by provider, transcript
explorer with TOC and minimap, personal notes, cross-provider view.

**Search** — Full-text across all providers. Message-level hits with
highlighted snippets.

**Ask** — Answers grounded in your own conversations. Every answer cites
sources. Every answer has an audit trace.

**Discover** — Cross-conversation themes. Summaries. Multi-conversation
distillation. Continuity handoffs for new AI chats.

**Export** — Memory Passport with manifest, canonical JSONL, provenance
index. Validate any passport against the contract.

---

## What It's Not

SoulPrint is not a hosted service — your data never leaves your machine.
Not a developer SDK — this is for people, not infrastructure. Not a
browser extension — it's a local app with a canonical file you own.

---

## Providers

| Provider | Format | Status |
|----------|--------|--------|
| ChatGPT | `.zip` from OpenAI | ✓ Supported |
| Claude | `.json` from Anthropic | ✓ Supported |
| Gemini | Google Takeout or extension JSON | ✓ Supported |

---

## Architecture

```
Layer A — Truth         SQLite ledger. Explicit lanes. Stable provenance.
Layer B — Legibility    Browse, search, inspect, trace, export. Read-only.
Layer C — Intelligence  Summaries, themes, distill, continuity. All derived.
Layer D — Distribution  Web app, CLI, landing page, freemium gate.
```

Every derived output traces back to canonical IDs and timestamps.
Derived never impersonates canonical.

---

## Surfaces

| Route | What it does |
|-------|-------------|
| `/` | Workspace — stats, provider coverage, quick actions |
| `/import` | Bring conversations home |
| `/imported` | What you've discussed — browse by provider |
| `/imported/<id>/explorer` | Transcript with TOC and minimap |
| `/chats` | Your own notes |
| `/federated` | Everything, together — cross-provider search |
| `/ask` | Ask your memory (Pro) |
| `/intelligence` | Themes & patterns (Pro) |
| `/distill` | Multi-conversation distillation (Pro) |
| `/answer-traces` | How answers were found |
| `/passport` | Take it with you — export and validate |
| `/summary` | Your AI memory, wrapped |

---

## Repo Map

```
src/
├── app/            Flask web app, templates, static
├── importers/      Provider adapters, auto-detection, persistence
├── retrieval/      Federated retrieval across storage lanes
├── answering/      Grounded answering, trace audit
├── intelligence/   Summaries, themes, distill, continuity
├── obsidian/       Obsidian vault export bridge
└── passport/       Memory Passport export and validation

tests/              56 test files, 586 test methods
sample_data/        Provider fixtures (ChatGPT, Claude, Gemini)
docs/               Architecture, specs, product docs
landing/            Static landing page (soulprint.dev)
```

---

## Tests

```bash
python -m pytest tests/ -v
```

56 test files covering import, persistence, retrieval, intelligence,
continuity, passport, CLI, and browser integration. CI runs on every push.

---

## CLI

```bash
# Import
python -m src.importers.cli sample_data/chatgpt_export_sample.json

# Search
python -m src.retrieval.cli --db instance/soulprint.db "search term"

# Ask
python -m src.answering.cli --db instance/soulprint.db "What about Lisbon?"

# Export passport
python -m src.passport.cli exports/passports
```

---

## Freemium Model

**Free** (no key needed): Import, browse, search, export, passport,
notes, answer traces, summary.

**Pro** (local license key): Ask, Themes & patterns, Distill.

License validation is local-only. No server. No accounts.

---

## Project Status

| Component | State |
|-----------|-------|
| Canonical SQLite ledger | ✓ Stable |
| 3-provider import | ✓ Stable |
| 16 web surfaces | ✓ Stable |
| Intelligence layer | ✓ Stable |
| Memory Passport export + validation | ✓ Stable |
| Grounded answering + audit traces | ✓ Stable |
| Freemium gate | ✓ Shipped |
| Design system (USB Drive) | ✓ Frozen |
| Landing page | ✓ Shipped |
| Desktop packaging | Planned |

---

## Docs

- [Getting started](docs/getting-started.md)
- [Positioning](docs/product/positioning.md)
- [Brand guide](docs/product/brand.md)
- [Memory Passport spec](docs/specs/memory-passport-spec.md)
- [Answering boundary](docs/architecture/answering-boundary.md)
- [Visual direction](docs/product/visual-direction.md)

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## License

Apache-2.0 — [inspect the code yourself](LICENSE).

---

*Your memory, on your machine, under your custody.*
