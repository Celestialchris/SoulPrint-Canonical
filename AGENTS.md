# SoulPrint — Agent Instructions

> For the full contributor reference, including design system, terminology, git workflow, and LLM configuration, see [CLAUDE.md](CLAUDE.md).

## Project Identity
SoulPrint is a local-first memory ledger and answering system.
Preserve provenance, stable IDs, portability, and deterministic retrieval behavior.

## Non-Negotiables
- Do not propose cloud-first rewrites unless explicitly requested.
- SQLite remains the canonical ledger unless a migration is explicitly approved.
- Provenance matters more than clever abstraction.
- Stable IDs matter more than convenience.
- mem0 or other memory systems are optional downstream layers, never the canonical source.
- Prefer the smallest working implementation over speculative future-proofing.
- Do not duplicate architecture docs unless asked.
- Do not create random markdown files unless there is a clear doc purpose.

## Working Method
1. Search first.
2. Plan before major edits.
3. Write tests before implementation when practical; for migrations and refactors, add or update regression coverage before changing behavior.
4. Review code after implementation.
5. Verify behavior with build, tests, lint, and security checks.
6. Store session state in `ops/sessions/`.
7. Store learned reusable patterns in `ops/learned/`.


## Architecture Priorities
- local-first
- provenance-first
- deterministic retrieval
- stable import/export
- small focused files
- backward compatibility when reasonable

## Preferred Delegation
- planner -> feature breakdown and migration plans
- reviewer -> correctness, regressions, missing tests
- docs_researcher -> framework and API verification
- security-reviewer -> secret handling, injection risks, unsafe config


## Migration Safety
- Do not alter canonical schema, import behavior, or retrieval semantics without explaining the impact on provenance, stable IDs, and backward compatibility.
- Prefer additive changes over destructive rewrites.
- When behavior changes, update the relevant session log and verification notes.