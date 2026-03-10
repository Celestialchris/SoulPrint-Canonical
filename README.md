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

The repository now includes a first importer path for ChatGPT exports:

- parse ChatGPT `conversations.json`-style data
- normalize into stable conversation/message records
- persist normalized records into SQLite (`ImportedConversation`, `ImportedMessage`)

See:

- parser: `src/importers/chatgpt.py`
- persistence: `src/importers/persistence.py`
- sample fixture: `sample_data/chatgpt_export_sample.json`
- tests: `tests/test_chatgpt_importer.py`

## Duplicate import policy (ChatGPT lane)

To prevent accidental re-imports of the same source conversation, the importer applies a minimal duplicate guard during persistence:

- Identity key: `(source, source_conversation_id)`
- Current source value for this lane: `chatgpt`
- If that key already exists, the conversation is **skipped** (no duplicate conversation row and no duplicate message rows)
- New source conversation IDs are still imported normally

The import path reports both imported and skipped conversation counts.

## Minimal ChatGPT import CLI (local/dev)

Use the importer CLI to load one ChatGPT export fixture or file into SQLite:

```bash
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db
```


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
