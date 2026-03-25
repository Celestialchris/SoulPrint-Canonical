# CLAUDE.md — SoulPrint Operator Instructions

## What SoulPrint Is

A local-first memory continuity system for AI users. Import AI conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with provenance, search and browse it, answer from it conservatively, and export/validate it as a Memory Passport.

## Architecture — Four Layers

1. **Canonical Ledger**: SQLite, stable IDs, timestamps, source identity. Authoritative.
2. **Browsing / Retrieval**: Read-only over ledger. Imported browser, explorer, federated search.
3. **Intelligence / Answering**: Derived, never canonical. Summaries, topics, digests, continuity, grounded answers, traces.
4. **Optional Extensions**: mem0, RAG, semantic layers. Never replace the ledger.

## Trust Chain

```
record → retrieve → browse → answer → trace → inspect
```

Every derived output traces back to canonical stable IDs.

---

## Task Execution Protocol

Every task follows this structure. No exceptions.

### 1. Starting State

Before writing any code, state what exists right now:
- Which files will be touched
- Current behavior of those files
- What tests currently pass

### 2. Target State

State what should exist when done:
- Exact files created or modified
- New behavior, described in one sentence per file
- What tests should pass after the change

### 3. Scope Lock

Explicitly declare boundaries:
- **Only edit** files named in the starting state, plus new files stated in target
- **Do not touch**: any file not listed, `instance/`, `docs/archive/`, sample fixtures (unless task is fixture work)
- **Do not add**: dependencies not in `requirements.txt` or `requirements-minimal.txt` without explicit approval
- **Do not change**: database schema, import return signatures, or route paths unless the task explicitly calls for it

### 4. Stop Conditions

Pause and ask before proceeding when:
- Two valid implementation approaches exist and the choice affects architecture
- A file would be deleted
- A new dependency is required
- The change would alter canonical ledger behavior
- An error cannot be resolved in 2 attempts
- The task scope needs to expand beyond what was stated

### 5. Checkpoint Output

After each meaningful step, output one line:
```
✅ [what was completed]
```
At the end, output a summary of every file created or modified.

### 6. Clarification Budget

Ask a maximum of 3 clarifying questions before producing work. If the task is still ambiguous after 3 questions, state assumptions explicitly and proceed with the smallest safe interpretation.

---

## Diagnostic Checklist — Run Before Every Task

Before starting work, silently check for these failure patterns:

| Pattern | Fix |
|---------|-----|
| Vague task ("fix the UI") | Extract the specific file, function, and behavior change |
| Two tasks in one request | Split into sequential bounded tasks |
| No success criteria stated | Derive a binary pass/fail: what test should pass? |
| Missing file path | Always anchor to exact files in `src/` or `tests/` |
| Scope is "the whole thing" | Decompose into the smallest first step |
| Contradicts a frozen decision in DECISIONS.md | Flag the conflict, do not override |
| Would mutate canonical records from a derived layer | Refuse — this violates architecture |

---

## Patterns

- Importers follow `ConversationImporter` protocol in `src/importers/contracts.py`
- Each provider needs: adapter, detector, fixture, registry entry, tests
- Tests use `make_test_temp_dir()` and `release_app_db_handles()`
- Provider IDs: lowercase strings in `SUPPORTED_IMPORT_PROVIDERS`
- Current providers: `chatgpt`, `claude`, `gemini`
- Answer traces: JSONL append-only, non-canonical, always labeled "Derived"
- Citation handoff: `memory:<id>` → `/memory/<id>`, `imported_conversation:<id>` → `/imported/<id>/explorer`
- Continuity packets: typed artifacts (summary, decisions, open loops, entity map, bridge packet) stored with provenance
- Obsidian bridge: one-way derived export in `src/obsidian/`. Exporter, renderer, config, CLI. Same authority rules as Memory Passport — SoulPrint stays canonical, Obsidian is the thinking interface.
- Distillation: multi-conversation condensation in `src/intelligence/distill.py`. Select N conversations → one paste-ready markdown handoff. JSONL store, Pro-gated, derived/non-canonical.
- Design reference: `src/app/static/app-mock.html` is the canonical visual reference for all UI work

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

# Export to Obsidian vault
python -m src.obsidian.cli --db instance/soulprint.db --vault ~/my-obsidian-vault
```

## Anti-Patterns

- Never let derived layers mutate canonical records
- Never add routes without tests
- Never import without duplicate guards
- Never replace canonical storage with summaries or semantic memory
- Never make the user drown in scrolling — use TOC, minimap, pagination
- Never use "unify" when describing lane behavior (lanes are composed read-only, not unified)
- Never edit files outside the stated scope lock
- Never proceed past a stop condition without human approval
- Never pad output with explanations that were not requested
- Never propose roadmap expansions — execute the bounded task

## Terminology

Do NOT use: "portable mode," "capsule," "vault," "torchlit," "ember."
Use instead: USB stick, plug in, local archive, your machine, Memory Passport.
Product metaphor: "A virtual USB stick for your AI life."
Trust language: "Everything stays on your machine. Nothing is sent anywhere."

## Visual Direction

Design system: "USB Drive." See `docs/product/brand.md`.

Identity: "A virtual USB stick for your AI life." Green = safe, verified, yours.

- System sans-serif body, JetBrains Mono for labels and metadata
- Single accent color: `#4ade80` (USB LED green). No second accent.
- Background: `#0e0f11` (cool neutral black, not warm brown-black)
- Hierarchy through opacity: `--t1` 88%, `--t2` 55%, `--t3` 35%, `--t4` 15%
- Filled green CTA buttons with 6px radius. No ghost/outline CTAs for primary actions.
- No grain overlay, no vignette, no ember glow, no radial gradients on body
- No serif fonts in the app UI (JetBrains Mono for mono, system sans for everything else)
- Minimum font size: 11px. Body text: 14-15px.
- Lane colors: ChatGPT `#4ade80`, Claude `#a78bfa`, Gemini `#60a5fa`
- Badges use 1px border + 4px radius, not background fills
- Trust-first design: green accent next to privacy language reinforces safety
- If style conflicts with clarity or trust, choose clarity

## Two-Layer Principle

**Layer 1** (doctrine, architecture, execution) always wins.
**Layer 2** (visual direction, aesthetic polish) may only enhance finish without creating drift.

Frozen decisions in `DECISIONS.md` override any task instruction that contradicts them.

## Extended Rules
See `.claude/rules/` for modular instruction files.
