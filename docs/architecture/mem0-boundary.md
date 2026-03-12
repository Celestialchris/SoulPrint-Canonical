# MEM0 Boundary Design (SoulPrint Canonical)

## Scope and non-goals

This memo defines the **integration boundary** for a future mem0 adapter in the current SoulPrint architecture.

Non-goals for this document:
- Implement mem0.
- Change storage models.
- Add dependencies.
- Redesign Milestone 1 retrieval/storage flow.

The source of truth remains SoulPrint's canonical loop:
**import -> normalize -> store -> retrieve**.

---

## 1) Architectural role

### SoulPrint owns (authoritative)

SoulPrint remains the canonical system for:
- Persistent ledger storage in SQLite (`MemoryEntry`, `ImportedConversation`, `ImportedMessage`).
- Lane-aware retrieval, including federated read composition.
- Stable record identifiers and source metadata needed to trace any item to raw canonical records.
- Human-auditable exports (markdown and structured retrieval outputs).

### mem0 owns (derived, optional)

mem0 should be treated as:
- A downstream, derived working-memory index built from selected retrieval results.
- A performance/usability aid for shortlisting or prioritizing context.
- A non-authoritative cache/abstraction that can be rebuilt from canonical SoulPrint data.

### Why mem0 is optional and downstream

mem0 must remain optional because:
- Canonical correctness must not depend on third-party availability or behavior.
- SoulPrint already has direct retrieval over canonical lanes.
- Any mem0 drift, partial ingest, or outage must not alter canonical data integrity.

**Boundary rule:** SoulPrint writes canonical data first; mem0 ingestion happens only after canonical persistence and through read contracts, never by bypassing them.

---

## 2) Input contract

Future mem0 ingestion should consume the existing federated retrieval shape as its primary contract.

### Eligible fields for ingestion

From each federated record:
- `source_lane` (required)
- `stable_id` (required)
- `title` (required content surface; may be truncated/normalized by adapter policy)
- `timestamp_unix` (nullable)
- `source_metadata` (required object; adapter may whitelist keys per lane)

### Preservation requirements

For every memory item sent to mem0, the adapter must preserve and forward:
- `source_lane` exactly as emitted by SoulPrint.
- `stable_id` exactly as emitted by SoulPrint.
- `timestamp_unix` as received (or explicit null marker).
- `source_metadata` keys required to re-locate canonical records.

### Lane-specific metadata minimums

- `native_memory` lane:
  - Preserve `source_metadata.role`.
  - Preserve `source_metadata.tags` when present.
- `imported_conversation` lane:
  - Preserve `source_metadata.source`.
  - Preserve `source_metadata.source_conversation_id`.

Adapter implementations may attach additional mem0-local attributes, but must not rewrite SoulPrint identifiers.

---

## 3) Memory selection policy

mem0 ingestion should be selective and reversible.

### Good candidates

Send items that improve short-horizon retrieval utility, such as:
- Repeated user preferences/signals appearing across sessions.
- High-salience imported conversation summaries derived from canonical rows.
- Recency-weighted conversation anchors with clear provenance.

### Exclusions (should not be sent directly)

Avoid sending:
- Entire raw conversation transcripts as-is (overly heavy, duplicates canonical lane).
- Low-signal boilerplate/system noise.
- Sensitive data unless explicitly policy-approved and redacted/minimized.
- Any item lacking a stable canonical reference (`source_lane` + `stable_id`).

### Canonical truth protection

Never store facts **only** in mem0.

Operational rule:
- If information is important enough to persist as truth, it must exist in canonical SoulPrint storage first.
- mem0 may store summaries/embeddings/derived notes, but these must reference canonical records and be reconstructible from them.

---

## 4) Provenance and hydration

### Provenance contract

Each mem0 memory must include a canonical pointer payload:
- `canonical.source_lane`
- `canonical.stable_id`
- `canonical.timestamp_unix`
- `canonical.source_metadata` (required subset)

This payload is immutable from SoulPrint's perspective once ingested.

### Future `hydrate()` behavior

A future `hydrate()` step should:
1. Read mem0 result(s) with canonical pointer payload.
2. Resolve each pointer back through SoulPrint lane readers.
3. Reconstruct canonical context (record body, neighboring messages if needed, timestamps, and source fields).
4. Return hydrated results that are explicitly marked as canonical-backed.

If pointer resolution fails, hydration returns a structured miss and does not fabricate content.

---

## 5) Failure and isolation rules

mem0 failures must be isolated from canonical app behavior.

### Required behavior when mem0 is unavailable

- Import, normalize, persistence, canonical retrieval, and export continue normally.
- mem0 ingest attempts fail closed (log + metric/event) without breaking request success for canonical flows.
- Read paths fall back to canonical federated retrieval only.

### Isolation requirements

- No synchronous hard dependency on mem0 for Milestone 1 endpoints/CLI.
- No schema migrations or write-path coupling tied to mem0 health.
- Any mem0 adapter timeout/error budget must be bounded and non-blocking for core flows.

---

## 6) Minimal future implementation plan

This is the smallest safe implementation sequence for later work.

### Step 1: Add adapter interface (no dependency)

Add a thin internal boundary module (e.g., `src/retrieval/mem0_adapter.py`) defining:
- `ingest_federated_items(items: list[FederatedReadResult]) -> IngestReport`
- `query_mem0(...) -> list[Mem0Hit]` (optional placeholder)
- `hydrate_mem0_hits(hits) -> list[HydratedResult]`

Initial implementation should be a no-op stub when mem0 is disabled.

### Step 2: Add config/env boundary

Introduce explicit feature gating (no new packages):
- `SOULPRINT_MEM0_ENABLED=false` (default)
- `SOULPRINT_MEM0_TIMEOUT_MS` (small bounded default)
- `SOULPRINT_MEM0_WRITE_MODE=best_effort` (default)

If disabled, code paths skip mem0 entirely.

### Step 3: Wire ingestion after canonical retrieval/persistence

- Trigger best-effort ingestion from existing read surfaces (or post-persist hooks) using federated-contract payloads.
- Do not alter existing DB models or importer schemas.
- Do not block canonical response completion on mem0 success.

### Step 4: Add tests for boundary guarantees

Minimal tests to add when adapter work begins:
- Contract test: federated record -> mem0 payload preserves `source_lane`, `stable_id`, timestamps, metadata.
- Failure test: simulated mem0 outage still returns canonical retrieval results.
- Hydration test: mem0 hit with canonical pointers rehydrates to canonical records.
- Safety test: adapter refuses ingestion for items missing canonical pointers.

---

## Acceptance criteria for future mem0 adapter work

A mem0 adapter is acceptable only if:
- Canonical SoulPrint storage remains authoritative.
- mem0 can be fully disabled with no loss of baseline app behavior.
- Every mem0-derived result is traceable to canonical lane records via stable IDs and metadata.
- Hydration can reconstruct canonical context without relying on mem0 as the sole truth store.
