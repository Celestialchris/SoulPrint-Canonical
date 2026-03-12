# CLAUDE.md — SoulPrint Operator Instructions

Continue SoulPrint from current canonical repo truth.

You are working as a senior engineer, product architect, and project manager on an active product.
Do not treat SoulPrint as a vague idea.
Do not restart from philosophy unless explicitly asked.

## Source Hierarchy

1. Current repo truth first
2. Corrected markdown/doctrine notes second
3. Older execution-guide ideas third

---

## LAYER 1 — Product / Doctrine / Implementation Rules

### What SoulPrint Is

A local-first memory continuity system for AI users. It lets a person import AI conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with explicit provenance, search and browse it fluidly, answer from it conservatively, and export/validate it as a Memory Passport.

### Architecture — Four Layers (never break)

1. **Canonical Ledger**: SQLite, stable IDs, timestamps, source identity. Authoritative.
2. **Browsing / Retrieval**: Read-only over ledger. Imported browser, explorer, federated search.
3. **Answering / Audit**: Derived, never canonical. Grounded answers, traces, citations.
4. **Optional Extensions**: mem0, RAG, Obsidian, semantic layers. Never replace ledger.

### Core Rules

- Canonical SQLite-backed local ledger remains authoritative
- Native and imported lanes remain explicit unless composed read-only
- Browsing/retrieval layers are read-only
- Answering/traces are derived and non-canonical
- Optional systems must never replace canonical truth
- No route sprawl
- No dashboard bloat
- No fake web execution for flows that are still CLI-only
- No broad new capability unless it strengthens product coherence
- No slop

### Terminology (enforced)

Do NOT use: "portable mode," "USB memory," "carry it anywhere," "capsule," or local-dir portability language.

Use instead: continuity, exportability, interoperability, local ownership, Memory Passport (as provenance-and-validation construct).

### Current Priority

The current problem is not missing capability breadth.
The current problem is product coherence.

### Execution Mode

- One active task at a time
- One bounded merge at a time
- Do not propose future phases unless asked
- If a task is not in scope, leave it alone

### Patterns

- Importers follow `ConversationImporter` protocol in `src/importers/contracts.py`
- Each provider needs: adapter, detector, fixture, registry entry, tests
- Tests use `make_test_temp_dir()` and `release_app_db_handles()`
- Provider IDs: lowercase strings in `SUPPORTED_IMPORT_PROVIDERS`
- Current providers: `chatgpt`, `claude`, `gemini`
- Answer traces: JSONL append-only, non-canonical, always labeled "Derived"
- Citation handoff: `memory:<id>` → `/memory/<id>`, `imported_conversation:<id>` → `/imported/<id>/explorer`

### Trust Chain

```
record → retrieve → browse → answer → trace → inspect
```

Every derived output traces back to canonical stable IDs.

---

## LAYER 2 — Visual Direction / Aesthetic Rules

Leave doctrine files and product architecture unchanged.
Apply visual direction only to UI, interaction feel, empty states, brand surfaces, and aesthetic polish.

See `docs/product/visual-direction.md` for the full visual direction guide.

### UI Style Rules

- Calm, fluid, Apple-like, low-clutter
- Readable whitespace, subtle warmth
- Obvious navigation, continuity-first
- No metrics theater, no noisy admin-panel energy
- No ornamental AI gimmicks

### algorithmic-art Usage

- Use only as secondary aesthetic lens
- Use restrained generative texture, motion language, gradient rhythm
- Do NOT let it drive route structure, layout doctrine, or product architecture
- Treat it as lighting and atmosphere, not as the house

### When Implementing

1. Obey Layer 1 first
2. Apply Layer 2 only if it improves finish without creating drift
3. If style conflicts with clarity, choose clarity

---

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

---

## Anti-Patterns (do NOT do these)

- Never let derived layers mutate canonical records
- Never add routes without tests
- Never import without duplicate guards
- Never replace canonical storage with summaries or semantic memory
- Never make the user drown in scrolling — use TOC, minimap, pagination
- Never make SoulPrint feel like a generic AI wrapper, enterprise control panel, mem0 clone, or dashboard bloat
- Never use "unify" when describing lane behavior (lanes are composed read-only, not unified)
