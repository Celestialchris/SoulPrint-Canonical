# CONTEXT.md — SoulPrint Project History & Decisions

This file is project history and architectural rationale. For commands and coding conventions, see `CLAUDE.md`.

---

## Project Timeline

### Phase 0 — Doctrine
Defined SoulPrint's identity: a **local-first memory passport for AI users**. Explicitly not SaaS, not a mem0 clone, not generic RAG, not an enterprise AI dashboard. The core insight: users own their AI conversation history; SoulPrint makes it portable, browsable, and auditable without cloud dependency.

### Phase 1 — Memory Passport
Defined the export contract in `docs/specs/memory-passport-spec.md`. A memory passport is:
- `manifest.json` — schema version, export metadata, lane inventory
- JSONL lanes — one file per lane (native, imported)
- Markdown — human-readable snapshot
- Provenance — full audit trail back to canonical stable IDs

Key decision: the passport is a **portability contract**, not a replacement for the SQLite ledger. Export = snapshot. Canonical truth stays local.

### Phase 2 — Browsing & Navigation
Built the read-only browsing layer:
- `/imported` — imported conversation list with search
- `/imported/<id>/explorer` — transcript explorer with TOC + minimap rail
- `/federated` — cross-lane search composing native + imported read-only
- `/memory/<id>` — native memory detail page

UI doctrine: Apple-like calm, warm parchment palette, low-clutter, no scrolling walls. Lane-colored badges (native=blue, imported=green, derived=amber).

### Phase 3 — Answering with Trust
Added grounded local answering with full audit residue:
- Answer Trace JSONL — append-only derived records, never canonical
- `/answer-traces` + `/answer-traces/<id>` detail with citation handoff
- Status enums: `grounded`, `ambiguous`, `insufficient_evidence` (not probability scores)
- Citations resolve via `memory:<id>` → `/memory/<id>` and `imported_conversation:<id>` → `/imported/<id>/explorer`

Core rule: derived output is always labeled "Derived / non-canonical." It never mutates Layer 1.

### Phase 4 — Cross-LLM Providers
Made the importer layer provider-agnostic:
- `ConversationImporter` protocol in `src/importers/contracts.py`
- Auto-detection via `parse_import_file()` in `registry.py`
- Providers: `chatgpt`, `claude`, `gemini`
- Each provider has: adapter, `looks_like_*` detector, fixture in `sample_data/`, registry entry, tests
- Duplicate guard on `(source, source_conversation_id)` prevents re-import corruption

---

## Major Repairs & Pivots

### mem0 Boundary Redesign
Risk identified: mem0 summarization and graph storage could silently replace or corrupt canonical truth. Resolution:
- mem0 is downstream-only, optional, feature-gated via `SOULPRINT_MEM0_ENABLED=false`
- Never authoritative — all mem0 items carry pointers back to canonical stable IDs
- Layer 4 (Optional Extensions) can never write to Layer 1

### Lane Separation Discipline
Resisted early pressure to merge native and imported schema into a single unified table. Decision: keep lanes separate, compose federated retrieval read-only via `FederatedReadResult`. This preserves provenance and makes each lane independently auditable.

### Answering Layer Precision
Strict lexical matching only. No semantic inference that could over-claim. Safe fallbacks return `insufficient_evidence` rather than hallucinating from partial matches. Grounded-only = the answer cites specific records or says so.

---

## Architectural Decisions

### Four Layers (never break)
```
Layer 1 — Canonical Ledger:     SQLite, stable IDs, source truth. Read-only from above.
Layer 2 — Browsing/Retrieval:   Read-only views. No writes to Layer 1.
Layer 3 — Answering/Audit:      Derived. JSONL traces. Never canonical.
Layer 4 — Optional Extensions:  mem0, RAG, Obsidian mirror. Never replace Layer 1.
```

### Trust Chain
```
record → retrieve → browse → answer → trace → inspect
```
Every derived output must trace back to a canonical stable ID. No orphan answers.

### Stable Record Shape
Every canonical record carries: `stable_id`, `source_lane`, `timestamp_unix`, `source_metadata`. This shape is immutable once written.

### Federated Retrieval Contract
Single `FederatedReadResult` shape across all lanes. Retrieval composes lanes; it never merges them structurally.

### Minimal Dependencies
Python 3.12, Flask, Flask-SQLAlchemy, SQLite, Jinja2, vanilla CSS. No vector DBs, no heavy RAG pipeline, no cloud services. Complexity is introduced only when the feature requires it.

---

## Operating Rules (from prompts and repair logs)

These rules governed every implementation decision:
- **Smallest working implementation** over speculative architecture
- **Preserve existing behavior** unless the task explicitly changes it
- **Flag uncertainty** instead of inventing hidden structure
- **Keep lanes separate** unless the task explicitly composes read-only
- **No route without tests** — every new route requires browser integration tests
- **No import without duplicate guards** — re-imports must be idempotent

---

## Next Priorities

From archive planning notes, in rough priority order:
1. **Desktop app packaging** — Tauri or PyWebView wrapper for local-first UX without a browser tab
2. **UI polish pass** — spacing, typography, mobile-friendliness
3. **Derived intelligence layer** — NotebookLLM-style summaries, topic clustering, "what have I explored?" views
4. **Passport validation / integrity checks** — `validator.py` hardening, checksum verification
