# SoulPrint

**Your AI conversations are scattered everywhere. SoulPrint brings them home.**

A local-first memory continuity system. Import your AI conversation history from ChatGPT, Claude, and Gemini. Browse, search, discover themes, ask questions, and export a verifiable Memory Passport. Everything stays on your machine. Nothing is hosted. The canonical ledger is yours.

---

## What SoulPrint Does

**Import** — Drop your ChatGPT `.zip`, Claude `.json`, or Gemini Takeout. Auto-detected. Normalized into one canonical ledger.

**Browse** — Workspace, imported conversations, native notes, federated view across all providers. Every record carries stable IDs, timestamps, and provenance.

**Search** — Full-text across all conversations, all providers. Lane-aware retrieval (imported, native, federated).

**Ask** — Grounded answering from your own conversation record. Every answer cites specific conversations. Every answer has an auditable trace.

**Discover** — Cross-conversation topic detection. Per-conversation summaries. Multi-conversation digests. All derived, all traceable.

**Export** — Memory Passport with checksums and provenance. Verifiable against the canonical record.

## What SoulPrint Is Not

- **Not a hosted SaaS** — your data never leaves your machine
- **Not a mem0 clone** — SoulPrint is for users, not developer infrastructure
- **Not an AI dashboard** — no metrics theater, no admin-panel energy
- **Not a generic wrapper** — SoulPrint has its own canonical ledger and trust chain

## Quick Start

```bash
# Clone
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical

# Install
pip install -r requirements-minimal.txt

# Run
python -m src.app.run

# Open
http://127.0.0.1:5678
```

Drop an export file on the Import page. Your conversations appear in seconds.

## Architecture

```
Layer A — Truth         Canonical SQLite ledger. Explicit lanes. Stable provenance.
Layer B — Legibility    Browse, search, inspect, trace, export. Read-only over truth.
Layer C — Intelligence  Summaries, topics, digests, continuity. All derived. All traceable.
Layer D — Distribution  Desktop app, landing page, freemium gate.
```

Every derived artifact stores: source conversation IDs, generation timestamp, LLM provider used, and prompt template version. Derived never impersonates canonical.

## Intelligence (BYOK)

SoulPrint's intelligence layer uses your own API key. Configure once:

```bash
export SOULPRINT_LLM_PROVIDER=openai      # or: anthropic
export SOULPRINT_LLM_API_KEY=sk-...
```

Without a key, import/browse/search/export all work. Intelligence features (summaries, topics, digests, ask) require a configured provider.

## Providers

| Provider | Format | Status |
|----------|--------|--------|
| ChatGPT | `.zip` export from OpenAI | Supported |
| Claude | `.json` export from Anthropic | Supported |
| Gemini | Google Takeout | Supported |

Adding a provider is bounded work: adapter, detector, registry entry, fixture, tests. The architecture supports unlimited providers.

## Tests

```bash
pytest
```

216 passing. Covers parsing, persistence, retrieval, intelligence, passport, CLI, and browser integration.

## Project Status

| Component | State |
|-----------|-------|
| Canonical ledger | Stable |
| 3-provider import | Stable |
| 9 web surfaces | Stable |
| Intelligence layer | Stable |
| Memory Passport | Stable |
| Grounded answering | Stable |
| Answer traces | Stable |
| Continuity packets | Next milestone |
| Desktop wrapper | Planned |
| Landing page | Planned |
| Freemium gate | Planned |

## Roadmap

See [`ROADMAP.md`](ROADMAP.md) for the sequenced build plan.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines. The short version: small PRs, tests required, no speculative architecture.

## License

Apache-2.0 — inspect the code yourself.

---

*Built with local-first principles. Your memory, under your custody.*
