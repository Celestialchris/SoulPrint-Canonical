# SoulPrint Memory Passport Spec (v1)

## One-line definition
A **Memory Passport** is SoulPrint's portable, inspectable export package that carries user-owned AI memory continuity with provenance, while preserving canonical truth boundaries.

## Why the Memory Passport exists
The Memory Passport defines the smallest contract for taking SoulPrint memory between systems without changing what is authoritative.

It exists to provide:

- **Portability:** a standard package shape that can move across tools.
- **User ownership:** exported memory remains user-controlled, local-first data.
- **Inspectability:** package contents are human-readable and auditable.
- **Exportable continuity:** users can keep context over time without platform lock-in.

## Product promise
SoulPrint's canonical ledger remains authoritative. The Memory Passport is a portability contract over that truth, not a replacement for storage semantics.

The contract is intentionally practical:

- small enough to implement now,
- explicit about provenance,
- honest about current Milestone 1+ capabilities.

## What a Memory Passport is not
A SoulPrint Memory Passport v1 is **not**:

- a hosted SaaS account or cloud identity,
- a replacement for canonical SQLite storage semantics,
- a generic document-QA bundle,
- an opaque derived-memory cache that hides source records.

## v1 package layout (smallest viable shape)
The v1 package is a directory (or zipped directory) with explicit top-level files/folders.

```text
memory-passport-v1/
  manifest.json
  conversations/
    imported/
      <provider-id>/
        conversations.jsonl
        messages.jsonl
  native/
    memory_entries.jsonl
  markdown/
    conversations/
      <conversation-stable-id>.md
    native/
      <entry-stable-id>.md
  provenance/
    index.jsonl
```

Notes:

- `manifest.json` is required.
- `conversations/`, `native/`, `markdown/`, and `provenance/` are included when data exists for that lane/type.
- Imported conversation exports are grouped by provider under `conversations/imported/<provider-id>/`.
- JSON Lines (`.jsonl`) is used for line-addressable records and streaming-friendly export/import.
- Markdown is included for human-readable continuity, not as canonical structured truth.

## Required manifest fields (v1)
`manifest.json` MUST include at least:

- `passport_version` (string, fixed `"1.0"` for this spec)
- `created_at` (ISO 8601 timestamp when package was created)
- `soulprint_export_version` (string; SoulPrint app/exporter version)
- `source_lanes` (array; e.g. `"imported_conversation"`, `"native_memory"`)
- `counts` (object with per-lane conversation/message/entry totals included in the package)
- `source_providers` (array of providers present in package data, e.g. `"chatgpt"`)
- `provenance` (object summarizing provenance/integrity approach used for this export)
- `integrity_notes` (string or array for non-cryptographic integrity notes in v1)

Recommended (optional) fields:

- `export_id` (stable UUID for this export instance)
- `time_range` (min/max record timestamps included when available)
- `markdown_included` (boolean)
- `format_notes` (free text for compatibility notes)

## Canonical vs derived data inside a passport
In v1, SoulPrint draws a strict boundary.

### Canonical-in-passport data
These records represent exported canonical ledger facts:

- imported conversations/messages,
- native memory entries,
- their stable IDs, timestamps (if available), lane/source labels, and source metadata.

### Derived-in-passport data
These records are non-authoritative derivatives:

- markdown renderings,
- summaries,
- answer traces,
- optional future semantic/embedding layers.

Rule: derived data MUST NOT impersonate canonical truth. Any derived unit must point back to canonical stable IDs.

## Provenance rules (all exported units)
Every exported record unit in v1 MUST carry provenance sufficient to trace back to canonical origin.

Required provenance attributes per unit (where available):

- `stable_id` (SoulPrint stable identifier)
- `source_lane` (e.g. `native_memory`, `imported_conversation`)
- `source_provider` (e.g. `chatgpt` for imported lane data)
- `source_record_id` (provider/source identifier if present)
- `timestamp_unix` and/or ISO timestamp fields from canonical records
- `source_metadata` object (structured metadata preserved from canonical/import normalization)

Provenance index expectations:

- `provenance/index.jsonl` should provide one line per exported unit with pointer fields to the unit location and its provenance attributes.
- The index is a navigational integrity map; it does not replace lane files as canonical export content.

## Minimal v1 scope
In scope now:

- imported conversation lane exports (current implemented provider reality),
- native memory lane exports,
- markdown-readable exports for continuity,
- manifest + provenance index.

This scope is intentionally aligned to current SoulPrint capabilities and avoids implementation promises not yet present.

## Explicit non-goals (v1)
Out of scope for this specification version:

- provider sync APIs,
- vector index export,
- mem0 dependency,
- generalized document-ingestion framework,
- encrypted backup/key-management system requirements.

## Relationship to current SoulPrint surfaces
- **Markdown export:** Markdown remains a portability/inspection format; it is derived and non-authoritative relative to canonical records.
- **Federated retrieval:** Retrieval continues to operate over canonical lanes; the passport package format does not alter retrieval runtime behavior.
- **Answering:** Answering remains read-only and grounded in retrieved canonical records; passport spec does not grant derived layers authority.
- **Optional downstream systems (mem0/local RAG):** These are downstream consumers of passport/canonical data and remain optional, non-authoritative integrations.

## Implementation guidance for next step
This spec is a contract for upcoming export/import packaging work. It does not require:

- runtime refactors,
- storage schema changes,
- multi-provider implementation,
- mem0 or RAG integration.

Any future implementation should preserve backwards compatibility with `passport_version` and keep canonical-vs-derived boundaries explicit.
