# SoulPrint-Canonical
SoulPrint is a local-first memory passport for AI users. It helps users bring, unify, search, inspect, and carry AI conversation history across platforms with clear provenance and exportable continuity.

SoulPrint is **not** a hosted memory SaaS, and it is **not** a replacement for canonical user ownership. The local canonical ledger (SQLite, with exportable markdown continuity) remains authoritative; optional systems are downstream and non-authoritative.


## Product positioning

- **Local-first memory passport:** SoulPrint focuses on user-owned continuity across AI tools.
- **Not hosted memory SaaS:** the core product is local canonical storage and portability, not a managed memory platform.
- **Not a replacement for canonical ownership:** derived layers (including optional adapters) must trace back to canonical IDs/timestamps rather than replace them.

See `POSITIONING.md` for the practical doctrine and boundaries.
See `docs/MEMORY_PASSPORT_SPEC.md` for the formal v1 Memory Passport package contract.

## Current Milestone 1+ importer capability

The repository now includes a provider-agnostic importer contract with concrete imported conversation adapters for:

- ChatGPT bulk exports (`src/importers/chatgpt.py`)
- Claude conversation exports (`src/importers/claude.py`)

Gemini is recognized as a provider slot in the importer runtime, but remains explicitly unsupported until the repo carries a real fixture-backed export shape.

Persistence remains canonical and source-aware in SQLite (`ImportedConversation`, `ImportedMessage`).

See:

- contract: `src/importers/contracts.py`
- ChatGPT adapter: `src/importers/chatgpt.py`
- Claude adapter: `src/importers/claude.py`
- persistence: `src/importers/persistence.py`
- sample fixtures: `sample_data/chatgpt_export_sample.json`, `sample_data/claude_export_sample.json`
- tests: `tests/test_chatgpt_importer.py`, `tests/test_cross_llm_importers.py`, `tests/test_importer_contract.py`

## Duplicate import policy (imported conversation lane)

To prevent accidental re-imports of the same source conversation, the importer applies a minimal duplicate guard during persistence:

- Identity key: `(source, source_conversation_id)`
- Current implemented provider values: `chatgpt`, `claude`
- If that key already exists, the conversation is **skipped** (no duplicate conversation row and no duplicate message rows)
- New source conversation IDs are still imported normally

The import path reports both imported and skipped conversation counts.

## Minimal import CLI (local/dev)

Use the importer CLI to load one supported export fixture or file into SQLite:

```bash
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db
python -m src.importers.cli sample_data/claude_export_sample.json --db instance/soulprint.db
python -m src.importers.cli sample_data/claude_export_sample.json --db instance/soulprint.db --provider claude
```

The CLI auto-detects `chatgpt` and `claude` payloads. Use `--provider` when you want an explicit provider boundary or a clearer malformed/unsupported error.


## Minimal federated retrieval surface (read-only)

SoulPrint now includes a minimal federated retrieval helper that composes both current storage lanes without changing schemas:

- module: `src/retrieval/federated.py`
- function: `federated_search(sqlite_path, keyword='', limit_per_lane=25)`
- lanes returned: `native_memory` + `imported_conversation`
- each result includes explicit lane/source, stable ID, title text, timestamp (if available), and source metadata

Developer CLI for quick local inspection:

```bash
python -m src.retrieval.cli --db instance/soulprint.db
python -m src.retrieval.cli --db instance/soulprint.db "lisbon"
```

A minimal read-only federated browser surface is also available in the web app:

```
/federated
```

It reuses the same `federated_search(...)` behavior and renders mixed lane results with explicit provenance plus lane-specific handoff links when available.

Native memory now also has a small read-only detail surface:

```
/memory/<entry_id>
```

This page renders one canonical `MemoryEntry` with its stable ID (`memory:<id>`), timestamp, role, tags, and content, plus clear navigation back to `/chats` and federated results when opened from `/federated`.


## Minimal local answering prototype (grounded, read-only)

SoulPrint now includes a minimal answering layer built on top of federated retrieval.

- module: `src/answering/local.py`
- boundary functions: `build_answer_context(...)`, `answer_from_federated_hits(...)`, `format_grounded_answer(...)`
- behavior: local-only, extractive/lightly synthesized output with citation provenance
- statuses: `grounded`, `ambiguous`, or conservative `insufficient_evidence`
- retrieval query path: natural-language questions are reduced to compact lexical terms before federated search
- fallback: returns `insufficient_evidence` for weak, empty, or short/acronym-only question terms
- ambiguity path: returns `ambiguous` when multiple top lexical matches are plausible without a dominant hit

Developer CLI:

```bash
python -m src.answering.cli --db instance/soulprint.db "What do I have about Lisbon?"
```

Optional derived Answer Trace audit residue (JSONL, non-canonical):

```bash
# Generate an answer and append a derived trace entry
python -m src.answering.cli --db instance/soulprint.db "What do I have about Lisbon?" --emit-trace

# Inspect recent derived traces
python -m src.answering.cli --db instance/soulprint.db --list-traces 5
```

Answer Traces are append-only derived records that capture question, retrieval terms, answer status, answer text, citations/stable IDs, source lanes, and fallback notes. They are audit residue only and do **not** replace or mutate canonical records.

A minimal read-only web inspection surface is also available:

```
/answer-traces
/answer-traces/<trace_id>
```

These routes render recent derived traces and per-trace details with explicit "Derived / non-canonical" labeling.

When a citation stable ID maps to an existing canonical record surface, the trace detail page includes a direct handoff link (for example, `memory:<id> -> /memory/<id>` and `imported_conversation:<id> -> /imported/<id>/explorer`).
If a citation does not map cleanly to an existing surface, SoulPrint keeps it as readable, non-clickable inspection text with explicit "no direct handoff view yet" labeling.


## Minimal Memory Passport export CLI (v1 surface)

You can export an inspectable package from canonical SQLite data:

```bash
python -m src.passport.cli exports/passports --db instance/soulprint.db
```

This writes `memory-passport-v1/` under the output directory with:

- `manifest.json`
- canonical lane exports (`conversations/imported/<provider-id>/*.jsonl`, `native/memory_entries.jsonl` when data exists)
- derived markdown continuity files (when enabled)
- `provenance/index.jsonl`

Use `--no-markdown` to export canonical JSONL + provenance only.

## Optional mem0 adapter boundary (disabled by default)

A minimal internal mem0 adapter boundary now exists for future integration without changing canonical storage behavior:

- module: `src/retrieval/mem0_adapter.py`
- boundary functions: `ingest_federated_items(...)`, `query_mem0(...)`, `hydrate_mem0_hits(...)`
- canonical pointer payload preserved for each candidate item (`source_lane`, `stable_id`, `timestamp_unix`, `source_metadata`)

Feature flags (safe defaults):

- `SOULPRINT_MEM0_ENABLED=false`
- `SOULPRINT_MEM0_TIMEOUT_MS=250`
- `SOULPRINT_MEM0_WRITE_MODE=best_effort`

With defaults, baseline retrieval remains canonical-only and mem0 behavior is a no-op.


## Imported conversation browser + transcript explorer (read-only, imported lane)

A minimal imported conversation browser UI is available at:

```
/imported
```

This list is server-rendered and read-only. It shows canonical imported conversations in descending canonical ID order, with lightweight metadata and links into the transcript explorer.

One-conversation transcript explorer route:

```
/imported/<conversation_id>/explorer
```

The explorer page is server-rendered and read-only, with:

- prompt-level TOC entries derived from user turns
- ordered transcript rendering from canonical `ImportedMessage.sequence_index`
- a lightweight overview/minimap rail for fast scrubbing

## Minimal imported conversation query CLI (local/dev)

After importing, you can inspect imported conversations and view one conversation with ordered messages:

```bash
python -m src.importers.query_cli --db instance/soulprint.db list
python -m src.importers.query_cli --db instance/soulprint.db search "trip"
python -m src.importers.query_cli --db instance/soulprint.db show 1
python -m src.importers.query_cli --db instance/soulprint.db export-md 1 exports/conversation-1.md
```

You can verify imported rows with SQLite:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect('instance/soulprint.db')
print('conversations:', conn.execute('select count(*) from imported_conversation').fetchone()[0])
print('messages:', conn.execute('select count(*) from imported_message').fetchone()[0])
PY
```
