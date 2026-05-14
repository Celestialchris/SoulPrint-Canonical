# CLAUDE.md — SoulPrint Contributor Reference

> **Before starting work:** read `AGENTS.md`, then inspect the current branch, task scope, and relevant public project files.
> **Quality reports:** generated quality reports may still write to `ops/quality/`.

## What SoulPrint Is

A local-first memory continuity system for AI users. Import AI conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with provenance, search and browse it, answer from it conservatively, and export/validate it as a Memory Passport.

## Architecture — Four Layers

1. **Canonical Ledger**: SQLite, stable IDs, timestamps, source identity. Authoritative.
2. **Browsing / Retrieval**: Read-only over ledger. Imported browser, explorer, federated search.
3. **Intelligence / Answering**: Derived, never canonical. Summaries, topics, digests, continuity, grounded answers, traces.
4. **Optional Extensions**: mem0, RAG, semantic layers. Never replace the ledger.

## Private operating material

Internal development history, private operating notes, agent-process records, and session continuity material are maintained outside the public distribution tree.

When executing in this repository, follow:

1. `AGENTS.md`
2. `CLAUDE.md`
3. The current task prompt
4. Current repository files

Do not search this repository for private context directories or private session records. They are not maintained on the public surface. Do not create public session logs in this repository unless the current task explicitly authorizes a release-safe record. Generated quality reports may write to `ops/quality/`.

## Execution Discipline

The root `AGENTS.md` contains the baseline execution harness. In practice, this means:

- make the smallest reversible change that satisfies the task;
- read the nearby implementation, callers, tests, fixtures, and exports before writing new code;
- use deterministic checks whenever code, tests, git, or the filesystem can answer the question;
- surface conflicting project patterns instead of blending them;
- write tests that prove intent, not only output shape;
- checkpoint after significant steps;
- fail loud when verification is partial, skipped, or uncertain.

### Deterministic checks over model guesses

Use code, commands, or file inspection for deterministic facts:

```text
branch state
file existence
dependency presence
test results
schema shape
registered providers
route names
status-code behavior
import/export output
```

Use model judgment for:

```text
classification
summarization
copy drafting
tradeoff explanation
threat modeling
design critique
```

If code can answer, code answers.

### Conflict handling

When two patterns disagree, do not average them. Prefer the pattern that is:

1. local to the touched module;
2. covered by tests;
3. newer and already integrated;
4. explicitly documented in this file or nearby project docs.

Name the conflict in the final report or PR summary if it affected the implementation.

### Topology check for non-trivial work

Before schema, importer, retrieval, answering, export, security, repository-boundary, or app-surface work, identify:

```text
State: where truth is stored.
Feedback: where errors, traces, reports, or verification appear.
Blast radius: what breaks if this file, route, model, or rule changes.
Timing: any ordering, async, retry, import/export, or lifecycle concern.
```

Skip this for tiny copy edits, typo fixes, obvious test-only edits, and isolated style cleanup.

## Patterns

- Importers follow `ConversationImporter` protocol in `src/importers/contracts.py`
- Each provider needs: adapter, detector, fixture, registry entry, tests
- Tests use `make_test_temp_dir()` and `release_app_db_handles()`
- Provider IDs: lowercase strings in `SUPPORTED_IMPORT_PROVIDERS`
- Current providers: `chatgpt`, `claude`, `claude_code`, `gemini`, `grok`
- Answer traces: JSONL append-only, non-canonical, always labeled "Derived"
- Citation handoff: `memory:<id>` → `/memory/<id>`, `imported_conversation:<id>` → `/imported/<id>/explorer`
- Continuity packets: typed artifacts (summary, decisions, open loops, entity map, bridge packet) stored with provenance
- Design token authority: `src/app/static/app.css` is the source of truth for the live design system.

## Trust Chain

```text
record → retrieve → browse → answer → trace → inspect
```

Every derived output traces back to canonical stable IDs.

## Commands

```bash
pip install -e .                    # core: import, browse, search, export
pip install -e ".[intelligence]"    # + Ask, Distill, Themes (requires Ollama or API key)
soulprint                            # run the app
python -m pytest tests/ -v          # run tests (1126 passing as of latest changelog entry)
python -m src.importers.cli sample_data/chatgpt.json --db instance/soulprint.db
python -m src.passport.cli exports/passports --db instance/soulprint.db
python -m src.passport.cli validate exports/passports/memory-passport-v1
python -m src.retrieval.cli --db instance/soulprint.db "search term"
python -m src.answering.cli --db instance/soulprint.db "question"
```

## Anti-Patterns

- Never let derived layers mutate canonical records
- Never add routes without tests
- Never import without duplicate guards
- Never replace canonical storage with summaries or semantic memory
- Never make the user drown in scrolling — use TOC, minimap, pagination
- Never use "unify" when describing lane behavior (lanes are composed read-only, not unified)
- Never hide skipped records, skipped tests, partial migrations, or partial verification behind “completed”
- Never create a second implementation beside an existing one before reading the existing exports, callers, and tests
- Never blend contradictory conventions silently

## Terminology

Do NOT use: "portable mode," "USB memory," "USB stick," "virtual USB," "carry it anywhere," "capsule."
Use instead: continuity, exportability, interoperability, local ownership, Memory Passport.

## Git Workflow

- ALWAYS verify you are on the correct branch before committing. Run `git branch` before every `git add`/`git commit`. NEVER commit directly to main unless explicitly told to.
- If you realize you committed to the wrong branch, STOP and ask the user before attempting recovery.
- When told DO NOT edit a file or given a scope lock, treat it as absolute. No cache busters, no "minor" changes, no touching the file for any reason without asking first.
- After CSS/UI changes, do NOT assume the fix worked. Tell the user to verify visually.
- Always run `pytest` after completing each task before committing. All tests must pass.
- This project uses Python (Flask), Jinja2 templates, HTML/CSS, and Markdown documentation.

## Product Context

Full brand, positioning, and design files live in `docs/product/`:

- `brand.md` — mission, voice, naming rules
- `positioning.md` — what SoulPrint is, what it's not, who it's for
- `visual-direction.md` — design system lineage and authority chain
- `design-doctrine-quiet-archive.md` — full Quiet Archive v3 spec
- `landscape.md` — competitive positioning and structural cousins
