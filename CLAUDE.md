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
# Install
pip install -e .                    # core: import, browse, search, export
pip install -e ".[intelligence]"    # + Ask, Distill, Themes (requires Ollama or API key)

# Run the app
python -m src.main

# Run tests
python -m pytest tests/ -v

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

Design system: **Magenta Sanctum v2** (since v0.6.0).
See `docs/product/design-doctrine-magenta-sanctum.md`.

Shell is editorial (pink brand accent, flat dark canvas with rail and sidebar lifted, display serif for personality, magenta wordmark on gradient chip). Data is flat (rows, hairline dividers, mono labels, tabular nums, no decoration on row data). Cards live only for navigation surfaces (stat cards, action cards on workspace). Supersedes the pre-v0.6.0 "USB Drive" doctrine.

Lane palette (vibrant, restored Phase 5.6):

- ChatGPT: `#4ade80` (green)
- Claude:  `#c9a84c` (gold)
- Gemini:  `#60a5fa` (blue)
- Grok:    `#e879f9` (magenta, dormant)

Magenta is the brand accent; green is the import CTA color only (scoped under `--cta-alive-*` tokens — see `.cta-primary`). No icons in nav. No font-weight above 500. No box-shadows on containers.

`src/app/static/app.css` is always authoritative over any doc file.

## Git Workflow

- ALWAYS verify you are on the correct branch before committing. Run `git branch` before every `git add`/`git commit`. NEVER commit directly to main unless explicitly told to. If you realize you committed to the wrong branch, STOP and ask the user before attempting recovery.

- When told DO NOT edit a file or given a scope lock, treat it as absolute. Do not add cache busters, do not make 'minor' changes, do not touch the file for any reason without asking first.

- After making CSS/UI changes, do NOT assume the fix worked. Tell the user to verify visually. If the user reports the fix didn't work, reconsider the approach rather than blaming browser caching.

- Always run the full test suite (`pytest`) after completing each task before committing. All tests must pass before any git commit.

- This project uses Python (Flask), Jinja2 templates, HTML/CSS, and Markdown documentation. The test suite uses pytest. There are 500+ tests. Run `pytest` from the repo root.

## Feedback Loop

When the user corrects my approach, I must:
1. Fix the immediate issue
2. Propose a specific addition to the relevant `.claude/rules/` file or a new memory entry — quote the exact line(s) I would add
3. Wait for approval before writing it

Do not skip step 2. Every correction is a potential rule.

## Extended Rules

See `.claude/rules/` for modular instruction files.

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review