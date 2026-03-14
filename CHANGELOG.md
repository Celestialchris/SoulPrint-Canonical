# Changelog

All notable changes to SoulPrint are documented here, backfilled from git history.

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
