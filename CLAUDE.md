# CLAUDE.md — SoulPrint Contributor Reference

## What SoulPrint Is

A local-first memory continuity system for AI users. Import AI conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with provenance, search and browse it, answer from it conservatively, and export/validate it as a Memory Passport.

## Architecture — Four Layers

1. **Canonical Ledger**: SQLite, stable IDs, timestamps, source identity. Authoritative.
2. **Browsing / Retrieval**: Read-only over ledger. Imported browser, explorer, federated search.
3. **Intelligence / Answering**: Derived, never canonical. Summaries, topics, digests, continuity, grounded answers, traces.
4. **Optional Extensions**: mem0, RAG, semantic layers. Never replace the ledger.

## Patterns

- Importers follow `ConversationImporter` protocol in `src/importers/contracts.py`
- Each provider needs: adapter, detector, fixture, registry entry, tests
- Tests use `make_test_temp_dir()` and `release_app_db_handles()`
- Provider IDs: lowercase strings in `SUPPORTED_IMPORT_PROVIDERS`
- Current providers: `chatgpt`, `claude`, `gemini`
- Answer traces: JSONL append-only, non-canonical, always labeled "Derived"
- Citation handoff: `memory:<id>` → `/memory/<id>`, `imported_conversation:<id>` → `/imported/<id>/explorer`
- Continuity packets: typed artifacts (summary, decisions, open loops, entity map, bridge packet) stored with provenance
- Design token authority: `src/app/static/app.css` is always the source of truth for the live design system. Repo docs (brand.md, visual-direction.md) describe the system but the CSS is authoritative if they ever diverge.

## Trust Chain

```
record → retrieve → browse → answer → trace → inspect
```

Every derived output traces back to canonical stable IDs.

## Commands

```bash
# Run the app
python -m src.run

# Run tests
python -m pytest tests/ -v

# Import conversations
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db

# Export passport
python -m src.passport.cli exports/passports --db instance/soulprint.db

# Validate passport
python -m src.passport.cli validate exports/passports/memory-passport-v1

# Federated search
python -m src.retrieval.cli --db instance/soulprint.db "search term"

# Answering
python -m src.answering.cli --db instance/soulprint.db "question"
```

## Anti-Patterns

- Never let derived layers mutate canonical records
- Never add routes without tests
- Never import without duplicate guards
- Never replace canonical storage with summaries or semantic memory
- Never make the user drown in scrolling — use TOC, minimap, pagination
- Never use "unify" when describing lane behavior (lanes are composed read-only, not unified)

## Terminology

Do NOT use: "portable mode," "USB memory," "USB stick," "virtual USB," "carry it anywhere," "capsule."
Use instead: continuity, exportability, interoperability, local ownership, Memory Passport.

## Visual Direction

Design system: "USB Drive." See `docs/product/brand.md` and `docs/product/visual-direction.md`.

- Near-black background (#0e0f11), green (#4ade80) as trust accent, system sans-serif body, Forum wordmark, JetBrains Mono labels
- Green is a deliberate trust signal — not decoration
- Calm, fluid, low-clutter. Typography carries hierarchy.
- No metrics theater, no noisy admin-panel energy
- No ornamental AI gimmicks
- If style conflicts with clarity, choose clarity
- The live `app.css` is always authoritative over any doc file

## Git Workflow

- ALWAYS verify you are on the correct branch before committing. Run `git branch` before every `git add`/`git commit`. NEVER commit directly to main unless explicitly told to. If you realize you committed to the wrong branch, STOP and ask the user before attempting recovery.

- When told DO NOT edit a file or given a scope lock, treat it as absolute. Do not add cache busters, do not make 'minor' changes, do not touch the file for any reason without asking first.

- After making CSS/UI changes, do NOT assume the fix worked. Tell the user to verify visually. If the user reports the fix didn't work, reconsider the approach rather than blaming browser caching.

- Always run the full test suite (`pytest`) after completing each task before committing. All tests must pass before any git commit.

- This project uses Python (Flask), Jinja2 templates, HTML/CSS, and Markdown documentation. The test suite uses pytest. There are 500+ tests. Run `pytest` from the repo root.

## Extended Rules

See `.claude/rules/` for modular instruction files.