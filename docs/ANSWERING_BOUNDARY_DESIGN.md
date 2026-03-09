# Answering Layer Boundary Design (Minimal v1)

## Purpose
This memo defines the smallest Answering Layer boundary for SoulPrint after federated retrieval exists, without changing canonical storage behavior.

Scope is limited to **local grounded answering as a read-only derived behavior**.

## Current system baseline (source of truth)
- Canonical truth remains SQLite-backed canonical records and markdown export.
- Retrieval already exposes lane-aware, provenance-bearing federated results.
- mem0 and document-QA/RAG-class systems are optional downstream systems, not required for v1.

## What the Answering Layer is responsible for
The Answering Layer is a thin, read-only layer that:
1. Accepts a user question and retrieval results.
2. Produces a grounded answer using only retrieved context.
3. Emits explicit citations/provenance to canonical records.
4. Applies safe fallback behavior when evidence is weak, ambiguous, or empty.

In short: **compose answer text from retrieved evidence; do not change retrieval or storage semantics**.

## What the Answering Layer is not responsible for
The Answering Layer must not:
- mutate canonical records;
- invent or rewrite canonical provenance;
- perform imports, normalization, or persistence;
- redefine federated retrieval ranking/selection policy;
- require mem0;
- require RAG/vector DB/document indexing pipelines;
- introduce agent orchestration.

## Boundary definitions

### 1) Federated retrieval -> Answering
Retrieval owns:
- searching lanes;
- returning lane-labeled, pointer-style records;
- preserving stable IDs/timestamps/source metadata.

Answering owns:
- interpreting retrieved records for one question;
- generating answer text with citations;
- declaring confidence/coverage limits.

Retrieval does **not** generate final answers.
Answering does **not** query storage directly in v1; it consumes retrieval output.

### 2) Answering -> Optional downstream systems (future, optional)
If added later, mem0 or document-QA systems are **consumers or augmenters** around answering, never replacements for canonical truth.

Rules:
- Canonical ledger remains authoritative.
- Any downstream memory/summary must trace to canonical IDs/timestamps.
- Answering v1 must run without optional systems present.

## Canonical pointer and provenance discipline (must preserve)
Every evidence unit used by answering must keep:
- `stable_id` (canonical row or canonical conversation/message identifier)
- `timestamp` (record/event time if available)
- `lane` (native vs imported)
- `source_metadata` (provider/source IDs, conversation/message metadata, etc.)

Answer text must reference evidence through these pointers; no orphan claims.

## Minimal context packet (retrieval -> answering)
The minimal packet should be a small, explicit structure:

```json
{
  "question": "string",
  "retrieved_at": "ISO-8601",
  "results": [
    {
      "stable_id": "string",
      "lane": "native|imported",
      "timestamp": "ISO-8601|null",
      "snippet": "string",
      "source_metadata": {"...": "..."}
    }
  ]
}
```

Notes:
- `snippet` is the answerable text fragment from retrieval output (not a rewritten canonical record).
- Additional fields may exist, but these are the minimum required for grounded answering.

## Expected answer output shape (high-level)
v1 output should be structured enough for UI/CLI use:

```json
{
  "answer_text": "string",
  "status": "grounded|insufficient_evidence|ambiguous",
  "citations": [
    {
      "stable_id": "string",
      "lane": "native|imported",
      "timestamp": "ISO-8601|null",
      "source_metadata": {"...": "..."}
    }
  ],
  "notes": ["optional short caveats"]
}
```

Citation expectations:
- All substantive claims in `answer_text` should map to one or more entries in `citations`.
- If evidence is partial, answer must say so explicitly.

## Safe fallback behavior

### Weak retrieval (low relevance/thin evidence)
- Return concise, conservative answer.
- Set `status = insufficient_evidence` when grounding is not strong.
- Include what was found and a short limitation note.

### Ambiguous retrieval (conflicting or multiple plausible contexts)
- Do not pick a speculative single interpretation.
- Set `status = ambiguous`.
- Briefly present competing interpretations with citations.
- Ask for disambiguation in `notes` if interactive surface supports it.

### Empty retrieval
- Do not hallucinate.
- Return no-content answer with `status = insufficient_evidence`.
- `citations` should be empty.
- Optionally suggest refining query terms.

## Smallest recommended v1 answering mode
Implement **extractive grounded summary mode**:
- deterministic or low-variance synthesis from retrieved snippets;
- no new retrieval strategy;
- no memory write-back;
- no long-horizon planning.

This is the smallest useful step beyond retrieval that preserves Milestone 1 discipline.

## Explicit v1 non-goals
- No autonomous agent behavior.
- No vector search or embedding infrastructure.
- No document-QA ingestion/index lifecycle.
- No mem0 dependency.
- No mutation of canonical ledger from answering outputs.
- No reinterpretive/archetypal reasoning layer in runtime contracts.

## Implementation guardrail checklist
Before shipping answering code, verify:
1. Answering consumes federated retrieval output (not direct DB writes/reads for new semantics).
2. Every citation points to stable canonical pointers.
3. Empty/weak/ambiguous retrieval paths are explicit and safe.
4. Optional systems are not required for core execution.
5. Canonical import -> normalize -> store -> retrieve behavior remains unchanged.
