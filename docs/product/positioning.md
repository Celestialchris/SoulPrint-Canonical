# SoulPrint Positioning

## One-Sentence Definition

SoulPrint is local-first continuity infrastructure for AI users: it brings conversation history from multiple providers into a canonical ledger you can inspect, search, answer from conservatively, and export with provenance.

## Why SoulPrint Exists

AI users now build valuable context across multiple assistants, but that context is fragmented by provider boundaries and weak export paths. SoulPrint exists to preserve continuity without handing ownership of that memory back to another platform.

## What SoulPrint Does Today

- Imports user-authorized conversation exports from ChatGPT, Claude, and Gemini with provider auto-detection
- Normalizes those records into a canonical SQLite ledger with explicit native and imported lanes
- Provides transcript exploration for imported conversations, including prompt-level navigation and a minimap rail
- Composes federated retrieval across lanes without collapsing their provenance boundaries
- Supports grounded local answering with explicit citations and derived answer traces
- Exports a Memory Passport package from canonical records and validates that package against the current contract

## What SoulPrint Is Not

- Not a hosted SaaS
- Not a mem0 clone
- Not an AI dashboard or general memory platform
- Not a system that hides canonical records behind opaque derived memory

## Product Priorities

SoulPrint is optimized for:

- Continuity across providers, tools, and time
- Local ownership of canonical records
- Provenance that stays attached to every retrieval and export path
- Inspectability at the record, transcript, and trace level
- Exportability and interoperability without cloud dependency

## Product Principles

1. The canonical ledger is authoritative.
2. Native and imported lanes stay explicit unless composed read-only.
3. Grounded answering is read-only and must cite source records.
4. Derived traces, summaries, and exports never overwrite canonical truth.
5. Export and validation matter because continuity is only useful when it can be inspected and moved without losing provenance.

## Relationship to Optional Systems

- `mem0` remains an optional downstream adapter boundary and is disabled by default.
- Document-QA or RAG-style systems remain separate from canonical ingestion and storage.
- Visual-direction guidance lives in `docs/product/visual-direction.md`; it does not redefine product architecture or storage truth.
