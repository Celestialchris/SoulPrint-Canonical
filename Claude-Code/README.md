# SoulPrint

[![Tests](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml/badge.svg)](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**Your AI conversations are scattered everywhere. SoulPrint brings them home.**

A local-first app that imports your conversation history from ChatGPT, Claude, and Gemini into one canonical archive on your machine. Browse it, search it, ask questions from it, discover themes across it, distill it into handoffs for new chats, and export a verifiable Memory Passport. No cloud. No accounts. Everything stays local.

![SoulPrint workspace](docs/screenshots/workspace.png)

## Quick Start

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
python -m src.run
# → http://127.0.0.1:5678
```

Drop a ChatGPT `.zip`, Claude `.json`, or Gemini Takeout on the Import page. Your conversations appear in seconds.

Or install as a package:

```bash
pip install -e .
soulprint
```

## What It Does

**Import** — Drop your export file. Provider is auto-detected. Normalized into a canonical SQLite ledger with duplicate guards.

**Browse** — Workspace dashboard, imported conversation list, transcript explorer with prompt-level TOC, native notes, federated cross-provider view.

**Search** — Full-text across all conversations from all providers in one place.

**Ask** — Grounded answering from your own conversation record. Every answer cites specific conversations. Every answer has an auditable trace. Returns `insufficient_evidence` rather than guessing.

**Distill** — Select any set of conversations and condense them into a single paste-ready handoff. Drop it into a new AI chat so the model has your full context. The core differentiator.

**Discover** — Cross-conversation topic detection, per-conversation summaries, multi-conversation digests. All derived, all traceable to source.

**Continue** — Generate continuity packets from any conversation. Copy a structured handoff into your next chat.

**Export** — Memory Passport with manifest, JSONL lanes, provenance index, and checksums. Validate any export against the canonical contract.

**Obsidian Bridge** — One-way export to an Obsidian vault. Conversations become markdown notes with frontmatter, wiki-links, theme notes, and daily-note anchors.

**Wrapped** — A cinematic summary of your entire AI history. Total conversations, provider breakdown, top themes, unfinished threads. Screenshot it, share it.

## Providers

| Provider | Format | Status |
|----------|--------|--------|
| ChatGPT | `.zip` export from OpenAI | ✓ Supported |
| Claude | `.json` export from Anthropic | ✓ Supported |
| Gemini | Google Takeout | ✓ Supported |

Adding a provider is bounded work: adapter implementing `ConversationImporter`, detector, registry entry, fixture, tests. The architecture supports unlimited providers.

## Intelligence (BYOK)

Intelligence features use your own API key:

```bash
export SOULPRINT_LLM_PROVIDER=openai      # or: anthropic
export SOULPRINT_LLM_API_KEY=sk-...
```

Without a key, import, browse, search, and export all work fully. Summaries, topics, digests, ask, continuity, and distill require a configured provider.

## Architecture

```
Truth         → Canonical SQLite ledger. Explicit lanes. Stable provenance.
Legibility    → Browse, search, inspect, trace, export. Read-only over truth.
Intelligence  → Summaries, topics, digests, continuity, distill. Derived. Traceable.
Distribution  → Web app, CLI, desktop exe, freemium gate.
```

Every derived artifact stores source conversation IDs, generation timestamp, LLM provider, and prompt template version. Derived never impersonates canonical.

## Why I Built This

I've been using ChatGPT, Claude, and Gemini daily for over a year. My conversation history — ideas, decisions, research, creative work — is scattered across three platforms that don't talk to each other. Their exports are barely usable zip files sitting dead on disk.

Nobody was building a tool to bring all of that together locally, with provenance, intelligence, and real exportability. So I built one.

## Freemium

**Free** (no key needed): all imports, browsing, search, export, passport, answer traces, wrapped summary, native notes.

**Pro** (local license key at `instance/license.key`): ask, intelligence, distill, continuity packets.

No accounts. No server auth. No network calls for licensing.

## Repo Map

```
src/
├── app/            Flask app, templates, static, viewmodels
├── importers/      Provider adapters, auto-detection, persistence
├── retrieval/      Federated retrieval across storage lanes
├── answering/      Grounded answering and trace audit
├── intelligence/   Summaries, topics, digests, distill, continuity
├── passport/       Memory Passport export and validation
├── obsidian/       Obsidian vault bridge (one-way export)
└── tools/          CLI utilities

tests/              47 test files, 492 methods
sample_data/        Synthetic provider fixtures (ChatGPT, Claude, Gemini)
docs/               Architecture, specs, brand guide
landing/            Static landing page
```

## Tests

```bash
pytest
```

47 test files, 492 methods covering parsing, persistence, retrieval, intelligence, continuity, distillation, passport, Obsidian bridge, licensing, CLI, and browser integration.

## CLI

```bash
# Import
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db

# Federated search
python -m src.retrieval.cli --db instance/soulprint.db "search term"

# Grounded answering
python -m src.answering.cli --db instance/soulprint.db "What do I have about Lisbon?"

# Export Memory Passport
python -m src.passport.cli exports/passports --db instance/soulprint.db

# Validate a passport
python -m src.passport.cli validate exports/passports/memory-passport-v1

# Export to Obsidian
python -m src.obsidian.cli --db instance/soulprint.db --vault ~/my-obsidian-vault
```

## Windows Executable

```powershell
cmd /c "scripts\build_windows.bat"
```

Runs tests, then packages with PyInstaller. Output: `dist/SoulPrint/SoulPrint.exe` — double-click to launch.

## Surfaces

| Route | Purpose |
|-------|---------|
| `/` | Workspace — overview, provider coverage, recent activity |
| `/import` | Import from any supported provider |
| `/imported` | Browse imported conversations by provider |
| `/imported/<id>/explorer` | Transcript explorer with TOC and minimap |
| `/chats` | Native notes created in SoulPrint |
| `/federated` | Cross-provider search with provenance |
| `/ask` | Grounded answering with citations |
| `/distill` | Multi-conversation distillation |
| `/intelligence` | Summaries, topic scans, digests |
| `/summary` | Your AI Memory Wrapped |
| `/passport` | Memory Passport export and validation |
| `/answer-traces` | Audit trail for generated answers |

## Project Status

| Component | State |
|-----------|-------|
| Canonical SQLite ledger | ✓ Stable |
| 3-provider import (ChatGPT, Claude, Gemini) | ✓ Stable |
| 15+ web surfaces | ✓ Stable |
| Intelligence layer | ✓ Stable |
| Continuity engine | ✓ Stable |
| Multi-conversation distillation | ✓ Stable |
| Memory Passport export + validation | ✓ Stable |
| Grounded answering + audit traces | ✓ Stable |
| Obsidian Bridge | ✓ Stable |
| Wrapped summary page | ✓ Shipped |
| Freemium gate | ✓ Shipped |
| Desktop exe (PyInstaller) | ✓ Shipped |

## Docs

- [Getting started](docs/getting-started.md)
- [Product positioning](docs/product/positioning.md)
- [Memory Passport spec](docs/specs/memory-passport-spec.md)
- [Obsidian Bridge spec](docs/specs/obsidian-bridge-spec.md)
- [Answering boundary](docs/architecture/answering-boundary.md)
- [Brand guide](docs/product/brand.md)

## Security

Local-first by design. No telemetry, no analytics, no outbound calls from the core app. The only network traffic is opt-in BYOK intelligence. See [`SECURITY.md`](SECURITY.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Small PRs, tests required, no speculative architecture.

## License

Apache-2.0 — [LICENSE](LICENSE)

---

*Your memory, under your custody.*
