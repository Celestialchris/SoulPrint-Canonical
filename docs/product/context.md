# CONTEXT.md — SoulPrint Project History & Decisions

This file records project history and architectural rationale. For commands and contribution rules, see `CONTRIBUTING.md` and `docs/getting-started.md`.

---

## Project Timeline

### Phase 0 — Doctrine
SoulPrint began as a local-first memory continuity system for AI users. It was defined against a clear set of negatives: not SaaS, not a mem0 clone, not generic RAG, and not an AI dashboard. The central premise was user ownership of conversation history, with continuity preserved through canonical storage, provenance, and export.

### Phase 1 — Memory Passport
The Memory Passport contract was defined in `docs/specs/memory-passport-spec.md`. A passport is:
- `manifest.json` for package metadata and lane inventory
- JSONL lane exports for canonical records
- markdown snapshots for human-readable continuity
- provenance records that point back to stable IDs and timestamps

Key decision: the passport is a provenance-and-validation export contract layered over canonical truth. Export is a snapshot of the ledger, not a replacement for the ledger.

### Phase 2 — Browsing & Navigation
The first read surfaces focused on inspection rather than transformation:
- `/imported` for imported conversation listing and search
- `/imported/<id>/explorer` for transcript exploration with prompt-level TOC and minimap rail
- `/federated` for cross-lane retrieval over native and imported records
- `/memory/<id>` for native memory detail

The app shell and visual treatment are documented separately in `docs/product/visual-direction.md` so visual guidance does not redefine Layer 1 product truth.

### Phase 3 — Answering With Trust
Grounded local answering was added on top of federated retrieval:
- Answer Trace JSONL as append-only derived audit residue
- `/answer-traces` and `/answer-traces/<id>` for trace inspection
- status values of `grounded`, `ambiguous`, and `insufficient_evidence`
- citation handoff from trace records back to canonical views

Core rule: derived output is always labeled non-canonical and never mutates Layer 1.

### Phase 4 — Cross-Provider Imports
The importer layer was generalized into a provider-aware boundary:
- `ConversationImporter` protocol in `src/importers/contracts.py`
- auto-detection through `parse_import_file()` in `src/importers/registry.py`
- supported providers: `chatgpt`, `claude`, `gemini`
- duplicate protection on `(source, source_conversation_id)` during persistence

This completed the current three-provider continuity baseline without collapsing lane boundaries.

---

## Current State

SoulPrint currently has:

- a canonical SQLite ledger with explicit native and imported lanes
- three-provider import with sample fixtures and test coverage
- transcript exploration for imported conversations
- federated retrieval across explicit lanes
- grounded local answering with derived trace inspection
- Memory Passport export and validation

The product already supports continuity, inspection, and provenance-preserving export without requiring hosted infrastructure.

---

## Major Repairs & Pivots

### mem0 Boundary Redesign
Risk identified: a future working-memory adapter could drift into hidden authority. Resolution:
- `mem0` remains downstream-only and feature-gated via `SOULPRINT_MEM0_ENABLED=false`
- all adapter payloads preserve pointers back to canonical stable IDs
- optional extensions cannot replace Layer 1 truth

### Lane Separation Discipline
There was early pressure to merge native and imported records into a single structural lane. The project kept them separate and composed them read-only through federated retrieval instead. That decision preserves provenance, source semantics, and independent auditability.

### Answering Layer Precision
Grounded answering stays deliberately conservative. Weak or ambiguous evidence returns `insufficient_evidence` or `ambiguous` instead of over-claiming from partial matches.

### Docs Split Clarification
The docs were split into Layer 1 product/doctrine/implementation truth and Layer 2 visual-direction guidance. This prevents aesthetic guidance from being treated as architecture and keeps historical/product docs aligned with runtime reality.

---

## Architectural Decisions

### Four Layers (never break)
```text
Layer 1 — Canonical Ledger:     SQLite, stable IDs, source truth. Read-only from above.
Layer 2 — Browsing/Retrieval:   Read-only views and retrieval over explicit lanes.
Layer 3 — Answering/Audit:      Derived traces and grounded responses. Never canonical.
Layer 4 — Optional Extensions:  Working-memory or document-QA adapters. Never replace Layer 1.
```

### Trust Chain
```text
record -> retrieve -> browse -> answer -> trace -> inspect
```
Every derived output must trace back to a canonical stable ID. No orphan answers.

### Stable Record Shape
Every canonical record carries `stable_id`, `source_lane`, `timestamp_unix`, and `source_metadata`. Derived layers depend on that shape; they do not redefine it.

### Federated Retrieval Contract
Retrieval composes lanes through a single read result shape. It does not merge lane schemas or erase source boundaries.

### Minimal Dependencies
Python 3.12, Flask, Flask-SQLAlchemy, SQLite, Jinja2, and a small optional set of downstream packages. Complexity is added only when a current feature requires it.

---

## Operating Rules

These rules continue to shape implementation:

- Smallest working implementation over speculative architecture
- Preserve existing behavior unless the task explicitly changes it
- Flag uncertainty instead of inventing hidden structure
- Keep lanes separate unless a task explicitly composes them read-only
- No route without tests
- No import without duplicate guards

---

## Current Active Sequence

1. README and docs truth alignment
2. Canonical Workspace on `/`
3. Import lifecycle UI
4. In-app Ask
5. Passport surface

## Deferred

- Derived intelligence
- Product polish
- Growth experiments

## Explicitly Deferred From Current Implementation

- `mem0` activation
- Hosted sync
- Vector database expansion or broad RAG build-out
- Mobile app development
- Directory-packaged distribution concepts
- Desktop packaging as a current priority
