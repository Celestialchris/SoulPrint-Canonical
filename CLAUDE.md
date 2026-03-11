# CLAUDE.md — SoulPrint Canonical Project Intelligence

## What is SoulPrint

A local-first memory passport for AI users. Import conversation history from ChatGPT, Claude, and Gemini into a canonical local ledger. Browse, search, answer from, and export your AI memory with clear provenance.

## Architecture — Four Layers (never break this)

1. **Canonical Ledger** (Layer 1): SQLite with stable IDs, timestamps, source/provider identity. This is the source of truth. Never mutate from derived layers.
2. **Browsing & Retrieval** (Layer 2): Read-only over the ledger. Imported browser, transcript explorer, federated search, native detail pages.
3. **Answering & Audit** (Layer 3): Derived, never canonical. Grounded local answering, citations, answer traces.
4. **Optional Extensions** (Layer 4): mem0, local RAG, semantic search, Obsidian mirror. These never replace the canonical ledger.

## Tech Stack

- Python 3.12, Flask, Flask-SQLAlchemy, SQLite
- Server-rendered Jinja2 templates with vanilla CSS
- No frontend framework yet (planned: React/Tauri for desktop app)
- Tests: unittest, pytest. Run with `python -m pytest tests/ -v`

## Key Patterns to Follow

### Importers
- All importers implement `ConversationImporter` protocol from `src/importers/contracts.py`
- Each provider needs: adapter class, `looks_like_*` detector, fixture in `sample_data/`, registry entry in `registry.py`, tests
- Provider IDs are lowercase strings in `SUPPORTED_IMPORT_PROVIDERS` frozenset
- Auto-detection via `parse_import_file()` in registry. Never hardcode provider assumptions.
- Current providers: `chatgpt`, `claude`, `gemini`

### Persistence
- Normalized conversations persist to `ImportedConversation` + `ImportedMessage` tables
- Duplicate guard on `(source, source_conversation_id)` — re-imports skip existing records
- All persistence in `src/importers/persistence.py`

### Models
- `MemoryEntry` — native memory (user-created)
- `ImportedConversation` + `ImportedMessage` — imported lane
- Both in `src/app/models/__init__.py`

### Routes
- `/` — home
- `/chats` — native memory list
- `/memory/<id>` — native memory detail
- `/imported` — imported conversation list (with search)
- `/imported/<id>/explorer` — transcript explorer with TOC + minimap
- `/federated` — cross-lane search
- `/answer-traces` — derived audit traces
- `/answer-traces/<id>` — trace detail with citation handoff

### Tests
- Use `make_test_temp_dir(self, "label")` from `tests/temp_helpers.py` for temp directories
- Use `release_app_db_handles(app, drop_all=True)` in cleanup
- Every route needs tests. Every importer needs parser + persistence + CLI + browser integration tests.
- Current: 130 tests, all passing.

### Answer Traces
- JSONL append-only derived records in `src/answering/trace.py`
- Non-canonical. Always labeled "Derived / non-canonical" in UI.
- Citation handoff: `memory:<id>` → `/memory/<id>`, `imported_conversation:<id>` → `/imported/<id>/explorer`
- Logic in `src/app/citation_handoff.py`

### Memory Passport
- Export: `src/passport/export.py` → manifest.json + JSONL lanes + markdown + provenance
- Validation: `src/passport/validator.py` → valid / valid_with_warnings / invalid
- CLI: `python -m src.passport.cli`

## CSS / Design Language
- Warm parchment palette: `--bg: #f2f0e9`, `--surface: rgba(255,253,248,0.94)`
- Lane-colored badges: native=blue, imported=green, derived=amber
- Apple-like: calm, readable, low-clutter, no dashboard bloat
- Single stylesheet: `src/app/static/app.css`

## Anti-Patterns (do NOT do these)
- Never let derived layers mutate canonical records
- Never add routes without tests
- Never import without duplicate guards
- Never replace canonical storage with summaries, semantic memory, or graph layers
- Never make the user drown in scrolling — use TOC, minimap, pagination
- Never make SoulPrint feel like: a generic AI wrapper, enterprise control panel, mem0 clone, or "AI dashboard bloat"

## Commands
```bash
# Run the app
python -m src.run

# Run tests
python -m pytest tests/ -v

# Import conversations
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db
python -m src.importers.cli sample_data/gemini_takeout_sample.json --db instance/soulprint.db

# Export passport
python -m src.passport.cli exports/passports --db instance/soulprint.db

# Validate passport
python -m src.passport.cli validate exports/passports/memory-passport-v1

# Federated search CLI
python -m src.retrieval.cli --db instance/soulprint.db "search term"

# Answering CLI
python -m src.answering.cli --db instance/soulprint.db "What do I have about Lisbon?"
```

## Current Phase

Phases 0-3 complete (doctrine, passport, browsing, answering with trust).
Phase 4 (cross-LLM) just completed — three providers with fixture-backed auto-detection.
Next priorities: desktop app packaging (Tauri/PyWebView), UI polish, derived intelligence layer (NotebookLLM-style summaries).

## Trust Chain
```
record → retrieve → browse → answer → trace → inspect
```
This chain must always hold. Every derived output traces back to canonical stable IDs.
