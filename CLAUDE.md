# CLAUDE.md — SoulPrint Contributor Reference

> **Before starting work:** read `context/soul.md` and `context/user.md`.
> **Before UI/design work:** read `docs/product/design-doctrine-quiet-archive.md`.
> **Before intelligence features:** read `context/llm-config.md`.
> **Before resuming after a gap:** read the latest file in `ops/sessions/`.
> **Before revisiting a settled question:** check `DECISIONS.md`.
> **Extended rules:** `.claude/rules/`

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
- Current providers: `chatgpt`, `claude`, `claude_code`, `gemini`, `grok`
- Answer traces: JSONL append-only, non-canonical, always labeled "Derived"
- Citation handoff: `memory:<id>` → `/memory/<id>`, `imported_conversation:<id>` → `/imported/<id>/explorer`
- Continuity packets: typed artifacts (summary, decisions, open loops, entity map, bridge packet) stored with provenance
- Design token authority: `src/app/static/app.css` is the source of truth for the live design system.

## Trust Chain

```
record → retrieve → browse → answer → trace → inspect
```

Every derived output traces back to canonical stable IDs.

## Commands

```bash
pip install -e .                    # core: import, browse, search, export
pip install -e ".[intelligence]"    # + Ask, Distill, Themes (requires Ollama or API key)
python -m src.main                  # run the app
python -m pytest tests/ -v          # run tests (700+, all must pass before commit)
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
