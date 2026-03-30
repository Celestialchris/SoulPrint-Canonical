# Contributing to SoulPrint

## Getting started

See [docs/getting-started.md](docs/getting-started.md) for setup instructions.

## Running tests

All tests must pass before submitting a PR:

```bash
python -m pytest tests/ -v
```

CI uses the same command in `.github/workflows/tests.yml`.

## Rules

### Test coverage
- Every route needs tests
- Every importer needs tests (adapter, detector, fixture, registry entry)
- No route without tests, no import without duplicate guards

### PR discipline
- One bounded task per PR — reviewable and self-contained
- No route sprawl, no dashboard bloat
- Derived layers must never mutate canonical records
- Keep lanes separate — compose federated retrieval read-only, never merge structurally

### Truth-surface hygiene (required)
When behavior or product surfaces change, update active truth docs in the same PR:
- `README.md`
- `ROADMAP.md`
- `CONTRIBUTING.md` (if expectations changed)

### Review checklist (required)
Every PR description should confirm:
- Canonical ledger remains authoritative
- Native/imported lane boundaries remain explicit
- Derived outputs remain non-canonical and provenance-bound
- Test command run locally matches CI command

### Code style
- Smallest working implementation over speculative architecture
- Preserve existing behavior unless the task explicitly calls for refactor
- Flag uncertainty instead of inventing hidden structure

## Out of bounds

The following are explicitly out of scope for contributions:

- Product framing that treats SoulPrint as hosted memory instead of a canonical local ledger
- mem0 activation (adapter exists but is gated off by design)
- Desktop packaging beyond the current PyInstaller setup (no Tauri, no Electron)
- Mobile apps
- Cloud/hosted deployment

## Reporting issues

Use the [GitHub issue templates](.github/ISSUE_TEMPLATE/) for bug reports and feature requests.

---

## Reference

### Architecture

```
Layer A — Truth         SQLite ledger. Explicit lanes. Stable provenance.
Layer B — Legibility    Browse, search, inspect, trace, export. Read-only.
Layer C — Intelligence  Summaries, themes, distill, continuity. All derived.
Layer D — Distribution  Desktop app, CLI, landing page, freemium gate.
```

Every derived output traces back to canonical IDs and timestamps.
Derived never impersonates canonical.

### Repo Map

```
src/
├── app/            Flask web app, templates, static
├── importers/      Provider adapters, auto-detection, persistence
├── retrieval/      Federated retrieval, FTS5 search
├── answering/      Grounded answering, trace audit
├── intelligence/   Summaries, themes, distill, continuity
├── obsidian/       Obsidian vault export bridge
└── passport/       Memory Passport export and validation

scripts/            PyInstaller spec, Inno Setup installer, build script
tests/              55 test files, 618 test methods
sample_data/        Provider fixtures (ChatGPT, Claude, Gemini)
docs/               Architecture, specs, product docs
landing/            Static landing page (soulprint.dev)
```

### Surfaces

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

### Running Tests

```bash
python -m pytest tests/ -v
```

55 test files covering import, persistence, retrieval, search, intelligence,
distillation, continuity, passport, freemium gate, CLI, and browser integration.
CI runs on every push.

### CLI Reference

```bash
# Import conversations
python -m src.importers.cli sample_data/chatgpt.json --db instance/soulprint.db

# Export passport
python -m src.passport.cli exports/passports --db instance/soulprint.db

# Validate passport
python -m src.passport.cli validate exports/passports/memory-passport-v1

# Federated search
python -m src.retrieval.cli --db instance/soulprint.db "search term"

# Answering
python -m src.answering.cli --db instance/soulprint.db "question"
```

### Intelligence (BYOK)

**Free** (no key needed): Import, browse, search, export, passport,
notes, answer traces, summary.

**Pro** (local license key): Ask, Themes & patterns, Distill.

License validation is local-only. No server. No accounts.
