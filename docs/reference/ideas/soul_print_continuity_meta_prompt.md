# SoulPrint Continuity Meta Prompt

Use this at the start of the next chat.

---

You are continuing the SoulPrint-Canonical project. Treat this prompt as the current operational truth unless the user explicitly overrides it.

## Project identity
SoulPrint is a local-first memory ledger and answering system.
Preserve provenance, stable IDs, portability, deterministic retrieval behavior, and additive change discipline.

## Non-negotiables
- Do not propose cloud-first rewrites unless explicitly requested.
- SQLite is the canonical ledger unless a migration is explicitly approved.
- Provenance matters more than clever abstraction.
- Stable IDs matter more than convenience.
- mem0 or other memory systems are optional downstream layers, never the canonical source.
- Prefer the smallest working implementation over speculative future-proofing.
- Do not duplicate architecture docs unless asked.
- Do not create random markdown files unless there is a clear doc purpose.
- Do not alter canonical schema, import behavior, or retrieval semantics without explaining the impact on provenance, stable IDs, and backward compatibility.
- Prefer additive changes over destructive rewrites.

## Harness state
The project now has a working Claude + Codex baseline.

### Installed structure
- `AGENTS.md` at repo root is SoulPrint-specific and should be obeyed first.
- `.claude/rules/` exists and contains project-local common, python, and typescript rules.
- `.codex/config.toml` exists and is intentionally lean.
- `.codex/agents/` contains `explorer.toml`, `reviewer.toml`, and `docs-researcher.toml`.
- `.agents/skills/` contains a selective baseline rather than the full ECC catalog.
- `ops/sessions/`, `ops/learned/`, and `ops/checkpoints/` exist and are the project-local continuity spine.
- ECC was vendored locally under `tools/ecc`.

### Current Codex config intent
Keep Codex lean:
- `approval_policy = "on-request"`
- `sandbox_mode = "workspace-write"`
- small MCP set only
- `multi_agent = true`
- 3 roles only
- avoid heavier MCPs unless a real need appears

### Tool philosophy
- Claude Code = primary harness
- Codex = secondary disciplined harness
- Project-local over global
- Minimal viable agent stack first, then expand
- Delay hooks until the baseline workflow is stable

## Baseline skills selected
- `search-first`
- `tdd-workflow`
- `verification-loop`
- `security-review`
- `coding-standards`
- `backend-patterns`
- `api-design`
- `frontend-patterns`
- `e2e-testing`
- `strategic-compact`

## Current development chronology
1. ECC baseline was installed locally and adapted for SoulPrint.
2. `AGENTS.md` was rewritten to reflect SoulPrint constraints.
3. Phase 1 completed: baseline harness installation.
4. Phase 2 completed: SoulPrint-specific adaptation.
5. Phase 3 began: operational workflow testing.
6. Answering Layer work started with a safe additive retrieval change (“Phase A”).

## What Phase A did
Phase A improved the retrieval side without changing schema or stable ID semantics.

### Phase A goals
- Improve imported-lane ordering.
- Extend federated retrieval results additively with evidence fields.
- Preserve citation stable IDs as `imported_conversation:<id>`.
- Avoid any schema, canonical storage, or signature changes.

### Phase A implementation summary
- Imported-lane ordering was improved.
- `FederatedReadResult` was extended additively with `evidence_text` and `evidence_stable_ids`.
- Imported hits now preserve message-level evidence when the keyword match came from a message.
- Retrieval changes passed their targeted tests.

### Important verification result
Phase A did not break the answering layer tests. Full pytest surfaced a separate stale test problem in `tests/test_workspace_home.py`, which was then fixed by aligning stale assertions with current UI truth.

## Workspace-home test status
- `tests/test_workspace_home.py` was updated to match the current workspace page.
- This was test alignment only, not app behavior change.
- Remaining full-suite issues after that point were separate environment/setup issues, not evidence-lane regressions.

## Current known architecture fact
The answering layer has one open seam:
Retrieval now provides `evidence_text` and `evidence_stable_ids`, but the answering layer does not yet consume `evidence_text`.

### Claude Code review note for Phase B
Verdict: Architecturally sound, one seam is not yet connected.

What is already true:
- Retrieval populates `evidence_text` and `evidence_stable_ids` on `FederatedReadResult`.
- This preserves provenance and keeps answering as a consumer, not a writer.
- Stable ID guarantees remain intact.
- Citation handoff routes are unaffected.
- The canonical ledger is never written to by the answering path.

### Risks identified
1. Evidence text is ignored in ranking.
   Imported conversations with generic titles can score lower than they should, even when a message matched strongly.
2. Evidence text is ignored in display.
   Users see a title like “Weekly standup notes” instead of the actual matched sentence.
3. Fallback asymmetry.
   `evidence_text` can be `None`, especially for native memory hits or imported hits without message-level evidence.
4. Ambiguity thresholds may later need recalibration once evidence text participates in overlap scoring.
5. No excerpt truncation boundary yet.
   Raw evidence could bloat traces or UI if surfaced directly.

## Safe next implementation step: Phase B
Implement only the smallest additive seam-closure in the answering layer.

### Phase B goal
Consume `evidence_text` safely in the answering layer with a None-safe fallback.

### Files likely involved
- `src/answering/local.py`
- `tests/test_answering.py`

### Exact change scope
1. In `_evidence_text_for_hit(hit)`:
   - prepend `hit.evidence_text` when present
   - truncate it to roughly 300 chars
   - keep existing title + metadata fragments as fallback
   - if `evidence_text` is `None`, preserve current behavior exactly

2. In `_evidence_summary_for_hit(hit)`:
   - prefer a truncated `hit.evidence_text[:200]` when available
   - otherwise fall back to `hit.title`

### What must not change during Phase B
- `FederatedReadResult` dataclass shape
- `GroundedAnswer` dataclass shape
- `AnswerCitation` dataclass shape
- `answer_from_federated_hits` function signature
- federated search query logic or sort order
- SQLite schema
- JSONL trace format
- citation handoff routes

## Operational instructions for the next assistant
- Do not restart from scratch.
- Assume the harness baseline is already installed and adapted.
- Do not propose re-copying ECC files unless the user explicitly says the repo was reset.
- Continue from the current Answering Layer seam.
- Prefer Codex for tightly scoped code changes.
- Prefer Claude for planning, review, and narrow architectural critique.
- Keep changes additive and minimal.
- Keep the session spine updated in `ops/sessions/`.
- If tests fail, first separate target-scope failures from pre-existing or environment-specific failures.
- Do not mislabel assertion failures as implementation regressions without isolating them.

## Suggested next-task prompt
Use this when resuming implementation:

"Read AGENTS.md and obey the project constraints strictly.
Implement only Phase B of the Answering Layer plan.
Scope:
- In `src/answering/local.py`, wire `evidence_text` into `_evidence_text_for_hit(hit)` and `_evidence_summary_for_hit(hit)` with truncation and None-safe fallback.
- In `tests/test_answering.py`, add or update regression coverage for both evidence-present and evidence-absent paths.
Constraints:
- No schema changes
- No canonical ledger changes
- No stable ID changes
- No signature changes
- No federated retrieval changes
Before editing, briefly state the exact files you will touch.
After editing, show a concise diff summary and report test results."

## Session continuity reminder
If there is any uncertainty, trust these principles in order:
1. local-first
2. provenance-first
3. stable IDs
4. smallest safe additive step
5. test alignment before speculative architecture

---

End of continuity prompt.

