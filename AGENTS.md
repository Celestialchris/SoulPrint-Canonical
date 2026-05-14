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
- Do not commit private session state, agent journals, prompt-routing doctrine, or learned-pattern notes to the public distribution tree.
- Generated quality reports may live under `ops/quality/`.

## Execution Harness

These rules apply to every non-trivial task unless the current prompt explicitly overrides them.

1. **Think before editing.** State assumptions, success criteria, and uncertainty before making substantial changes.
2. **Smallest reversible change.** Prefer the minimum implementation that solves the task. No speculative abstractions.
3. **Surgical scope.** Touch only files required by the task. Do not improve adjacent code while passing through.
4. **Goal-driven execution.** Define what “done” means, then verify against that definition.
5. **If code can answer, code answers.** Use deterministic checks for file existence, tests, branch state, status codes, schema shape, dependency presence, and import/export behavior. Use the model for judgment, summarization, classification, and drafting.
6. **Context budgets are real.** If the task starts drifting or the same error recurs, stop, summarize current state, and ask for a fresh scope rather than re-looping silently.
7. **Surface conflicts.** If two project patterns disagree, do not average them. Pick the more recent, more tested, or more local pattern, explain why, and flag the other for cleanup.
8. **Read before writing.** Before adding or changing code, inspect the nearest callers, exports, shared utilities, fixtures, and existing patterns.
9. **Tests verify intent.** Tests should encode why behavior matters, not only that a function returns something.
10. **Checkpoint significant steps.** After a meaningful edit or refactor phase, state what changed, what was verified, and what remains.
11. **Match conventions.** Conformance beats taste inside this codebase. If a convention is harmful, surface it instead of silently forking it.
12. **Fail loud.** Do not call work complete if records were skipped, tests were skipped, verification was partial, or uncertainty remains.
13. **Map topology for risky work.** For schema, importers, retrieval, answering, exports, security, or repo-boundary work, identify state, feedback, blast radius, and timing before implementation.
14. **Treat user material as entrusted.** Private files, prompts, logs, exports, and repo history are not inventory. Handle them with restraint and only inside the requested scope.

## Working Method

1. Inspect the current task, branch, and relevant files before editing.
2. Search or read the existing implementation before creating new code.
3. Plan before major edits.
4. Write tests before implementation when practical; for migrations and refactors, add or update regression coverage before changing behavior.
5. Review code after implementation.
6. Verify behavior with build, tests, lint, and security checks appropriate to the task.
7. Do not commit private session state, agent journals, prompt-routing doctrine, or learned-pattern notes to the public distribution tree. See `CLAUDE.md` → `Private operating material` for the public-surface boundary.
8. Generated quality reports may live under `ops/quality/`.

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
- When behavior changes, update release-safe verification notes only if the current task explicitly allows a public record.
