---
status: historical
authority: non-authoritative
active_truth:
  - README.md
  - ROADMAP.md
  - docs/product/
  - docs/specs/
---

# SoulPrint Project Status Checkpoint (2026-03-09)

> [!NOTE]
> **Historical reference — non-authoritative.**
> This document captures a past project state and should not be used as current product doctrine.
> Active truth lives in `README.md`, `ROADMAP.md`, `docs/product/*`, and `docs/specs/*`.

## Scope of this checkpoint

This document captures the model/storage and retrieval/query implementation in the canonical repository **at the time of this checkpoint**, without proposing runtime refactors in this pass.

Primary loop in code at checkpoint time:

1. import ChatGPT export JSON
2. normalize to stable conversation/message records
3. persist to SQLite
4. retrieve via list/search/show/export-markdown query paths

## What worked at checkpoint time

### 1) Native memory capture path (app runtime)

- Flask runtime persists direct app submissions into `MemoryEntry` (`timestamp`, `role`, `content`, `tags`).
- `POST /save` inserts one `MemoryEntry` row.
- `GET /chats` retrieves up to 100 `MemoryEntry` rows (optionally filtered by tag substring) ordered newest first.

This is the native in-app memory stream and was independent from imported conversation tables at checkpoint time.

### 2) Imported conversation path (importer runtime)

- Importer parser normalizes ChatGPT exports into conversations/messages with stable source IDs and sequence ordering.
- Persistence writes normalized records into:
  - `ImportedConversation` (conversation metadata)
  - `ImportedMessage` (ordered message rows linked by foreign key)
- Query surface for imported records supports:
  - list conversation summaries
  - fetch one conversation with ordered messages
  - keyword search (title + message content via SQLite `LIKE`)
  - markdown export of one conversation with metadata and ordered messages

### 3) Verification coverage

- Tests cover normalization ordering/title handling, persistence counts/values, list/show/search behavior, and markdown rendering/export behavior.

## What is intentionally parallel

At the time of this checkpoint, the repository maintained **two parallel but valid SQLite-backed memory lanes**:

1. **Native lane (`MemoryEntry`)**
   - origin: app-originated messages saved through `/save`
   - primary UX: `/chats` web view
   - shape: lightweight entries with optional tags

2. **Imported lane (`ImportedConversation` + `ImportedMessage`)**
   - origin: external ChatGPT exports imported via CLI
   - primary UX: importer query CLI (`list`, `search`, `show`, `export-md`)
   - shape: normalized conversation/message graph with source IDs and sequence index

This parallelism was useful at checkpoint time: it separated direct app capture from external import normalization while Milestone 1 stabilized.

## What is duplicated

This baseline captured duplication mostly in retrieval interface and storage intent:

- Both lanes store conversational text in SQLite but in different schemas.
- Both lanes have read surfaces, but split by interface:
  - web route retrieval for `MemoryEntry`
  - CLI retrieval helpers for imported conversations
- There is no shared unified query API spanning both lanes yet.

This duplication is acceptable short-term, but it creates discoverability and maintenance friction if left unbounded.

## What is deferred (explicitly)

The following are intentionally deferred in this checkpoint:

- introducing mem0 as a required runtime dependency
- introducing RAG/document-QA stacks as default retrieval path
- adding new storage backends or vector databases
- replacing canonical SQLite + markdown traceability with derived memory layers
- merging interpretive/archetypal context into runtime persistence contracts

## Retrieval surface at this checkpoint (summary)

At this checkpoint, the retrieval surface was **narrow and explicit**:

- Native lane:
  - `GET /chats` (recent `MemoryEntry` retrieval, optional tag filter)
- Imported lane:
  - `list_imported_conversations()`
  - `search_imported_conversations()`
  - `get_imported_conversation()`
  - `export_imported_conversation_markdown()`
  - CLI wrapper in `src/importers/query_cli.py`

No cross-lane retrieval abstraction existed at checkpoint time; callers chose one lane explicitly.

## Recommended next engineering steps (bounded)

1. **Document lane contracts in one stable place (near-term)**
   - Keep this checkpoint and architecture note updated as the source-of-truth docs for lane ownership and retrieval scope.

2. **Add stable retrieval facades before unification work**
   - Introduce a thin, internal read-service boundary per lane (native/imported) without changing schemas.
   - Goal: enable a future unified query endpoint without immediate table refactors.

3. **Add traceability fields to retrieval responses where missing**
   - Ensure response contracts always expose stable IDs and timestamps for downstream auditability.

4. **Define a Milestone-1.5 “federated read” slice**
   - Implement a read-only aggregator that returns native + imported results side-by-side with explicit `source_lane` labels.
   - Keep write paths unchanged.

5. **Only after federated read is stable: decide consolidation strategy**
   - Evaluate whether to keep dual-lane long-term or map native entries into imported-style conversations.
   - Decision should be driven by actual query/product needs, not speculative architecture.

## Non-goals for this checkpoint

- No runtime behavior change.
- No data migration.
- No schema redesign.
- No mem0/RAG/agent integration.
