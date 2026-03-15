# Changelog

All notable changes to SoulPrint are documented here, backfilled from git history.

## Packaging Infrastructure (2026-03-15)
- Added `src/runtime.py` for centralized resource-path resolution (dev, editable install, frozen build)
- Added `src/main.py` as production launcher with browser auto-open
- Updated `src/config.py` and `src/app/__init__.py` to use runtime path resolution
- Full `pyproject.toml` with build-system, optional dependencies, and `soulprint` entry point
- Added `tests/conftest.py` and `pytest.ini` for stable test imports
- PyInstaller spec file (`SoulPrint.spec`) and Windows build script (`scripts/build_windows.bat`)
- Added `docs/executable-packaging-overview.md`
- Fixed ROADMAP.md dead references to gitignored files
- Fixed docs/getting-started.md test command (unittest → pytest)

## Coherence Pass (2026-03-15)
- Fixed `src/run.py` entrypoint: `python -m src.run` now actually starts the server
- Added `roadmap/` directory with 30-day vision and continuity architecture docs
- Updated ROADMAP.md to reflect completed continuity phases and fix broken references
- Removed phantom `chromadb` and `sentence-transformers` from requirements.txt
- Aligned CI to pytest (matching README, CONTRIBUTING, CLAUDE.md)

## Lineage Suggestions (2026-03-14)
- Implemented inspectable lineage suggestions: continuation, fork, revisit, supersede
- Lineage links are derived and non-authoritative — canonical ledger never mutated
- Added lineage surface in conversation detail views

## Bridge Assembly (2026-03-14)
- Bridge assembly for next-chat handoff from continuity packets and cited canonical snippets
- Bounded handoff payload size for real chat restarts
- Copy-to-clipboard workflow for pasting into next conversation

## Continuity Packet MVP (2026-03-13)
- Typed continuity artifacts: summary, decisions, open loops, entity map, bridge packet
- JSONL append-only persistence with full provenance metadata
- Generation through existing intelligence/provider boundary (BYOK)
- Continuity service with store, models, and generation pipeline
- POST endpoint for generation + GET for inspection + copy handoff

## Continuity Surface (2026-03-13)
- Added continuity detail page at conversation level
- Generation trigger, artifact inspection, and clipboard handoff

## Landing Page (2026-03-13)
- Static landing page in `landing/` directory
- Hero section, product loop visual, positioning sections
- GitHub Pages / Netlify ready

## CSS Restyle (2026-03-12)
- Full UI restyle: "Torchlit Vault" design system
- Dark warm palette, Forum/Cormorant Garamond/JetBrains Mono typography
- Hierarchy through opacity, wine and gold accents
- All 10 surfaces covered

## Repo Governance (2026-03-12)
- Added DECISIONS.md with frozen architectural, engineering, design, and product decisions
- Design system specification locked

## Intelligence Layer (2026-03-11)
- Per-conversation summaries via BYOK LLM provider
- Cross-conversation topic detection with keyword fallback
- Multi-conversation digest synthesis
- Intelligence routes and CLI tools

## Two-Layer Doctrine (2026-03-11)
- Rewrote CLAUDE.md with two-layer operator instructions (product/doctrine + visual direction)
- Added execution guide and visual direction docs

## Visual Summary Dashboard (2026-03-11)
- Added visual summary dashboard to home page with lane stats and recent activity

## CONTEXT.md (2026-03-11)
- Added project history and architectural decisions document

## Cross-LLM Importers (2026-03-10)
- Added Gemini importer with Google Takeout and Chrome extension support
- Three-provider story complete: ChatGPT, Claude, Gemini
- Provider-agnostic importer contract with auto-detection registry

## Memory Passport Validation (2026-03-10)
- Implemented passport validation logic with manifest, lane, and provenance checks
- Validation reports: `valid`, `valid_with_warnings`, `invalid`

## Citation Handoff (2026-03-10)
- Added Answer Trace citation handoff links to canonical views
- `memory:<id>` resolves to `/memory/<id>`, `imported_conversation:<id>` to `/imported/<id>/explorer`
- Hardened trace citation handoff mapping

## Answer Trace Browser (2026-03-10)
- Added read-only web answer trace browser at `/answer-traces`
- Per-trace detail view at `/answer-traces/<trace_id>` with derived labeling

## Browsing Layer (2026-03-10)
- Native memory detail page at `/memory/<id>` with federated handoff
- Read-only federated browser at `/federated` composing both lanes
- Imported conversation list at `/imported` with explorer handoff
- Transcript explorer at `/imported/<id>/explorer` with TOC and minimap

## Answering Layer (2026-03-09)
- Local grounded answering over federated retrieval
- Answer statuses: `grounded`, `ambiguous`, `insufficient_evidence`
- Compact lexical query term extraction
- CLI with `--emit-trace` and `--list-traces`

## Memory Passport Export (2026-03-09)
- v1 Memory Passport specification
- Export CLI producing manifest, JSONL lanes, provenance index
- Product positioning document

## mem0 Adapter Boundary (2026-03-09)
- Optional mem0 adapter with no-op defaults (`SOULPRINT_MEM0_ENABLED=false`)
- Boundary design memo

## Federated Retrieval (2026-03-09)
- Minimal federated retrieval composing native + imported lanes read-only
- Developer CLI for local inspection

## ChatGPT Importer (2026-03-09)
- ChatGPT export importer with normalized SQLite persistence
- Duplicate guard on `(source, source_conversation_id)`
- Query CLI: list, search, show, export-md
- Keyword search for imported conversations

## Milestone 1 Baseline (2026-03-08)
- Initial Flask app with SQLite canonical ledger
- Routes: `/`, `/save`, `/chats`
- `MemoryEntry` model with stable IDs
- Minimal requirements and setup docs
- Repo audit and smoke tests
