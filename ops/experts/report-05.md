# Expert Report 05: chore/docs-canon-steward

Date: 2026-04-30
Branch: chore/docs-canon-steward
PR: (pending)
Template H prompt: inline (Phase 5 recommendation 1, Docs/Canon Steward fill, forward-reference exemption)

## Routing

Section A expert: Docs/Canon Steward (forward reference; stanza added by this branch)
Section B stance: Senior Engineer

The Section A reference resolves forward: Docs/Canon Steward did not exist on `main` until this branch landed. The forward-reference workaround was authorized for this single branch by the Phase 5 audit (`ops/phase-5/audit-phase-5.md` Section 5 item 1) and the Phase 5 session log (`ops/sessions/2026-04-30-phase-5-audit.md`). This is the final branch entitled to that workaround.

## Reads consumed during drafting

- `context/experts.md` (project canon, pattern-mirror): full Section A stanzas read top to bottom to confirm field structure (Lens / Owns / Stack docs / Project canon / Learned patterns / Triggers / Out of scope) and to confirm that no filled expert carried a Proof required field. Phase 3A status note at line 21 confirmed.
- `context/template-h.md` (project canon, read-to-verify): confirmed the Review Protocol's canon-existence check is present (line 404 area) and that the Routing Justification block is not yet codified. Verified that this branch should not edit this file.
- `ops/phase-5/audit-phase-5.md` (read-to-verify): Section 3 row 5 (Docs/Canon Steward disposition: ACCEPTED), Section 4b (no-stub numbering rule), Section 5 item 1 (forward-reference exemption boundary).
- `ops/phase-5-input/chatgpt-13-pass2.md` (pattern-mirror, lines 510-549): pass-2 narrow proposal as the source of truth for the role's scope and original five-field shape.
- `ops/sessions/2026-04-30-phase-5-audit.md` (read-to-verify): confirmed Phase 5 verified facts and that the queued next branch is this one.
- `ops/experts/report-04.md` (pattern-mirror): report format reference for this file.
- `ops/learned/typography-self-reference.md` (pattern-mirror): doctrine-self-reference discipline. Load-bearing for any doctrine work, including this branch's own session log and report.

## Reads consumed during execution by Claude Code

- `context/experts.md` (read, edited): inserted the Docs/Canon Steward stanza between the Intelligence/Answering Engineer separator and the Importer Engineer placeholder. Refreshed the Phase 3A status note body.
- `context/template-h.md` (read only): confirmed scope lock holds; not edited.
- `ops/phase-5/audit-phase-5.md` (read only): not edited.
- `ops/phase-5-input/chatgpt-13-pass2.md` (read only, lines 510-549): not edited.
- `ops/sessions/2026-04-30-phase-5-audit.md` (read only): not edited.
- `ops/experts/report-04.md` (read only): format reference; not edited.
- `ops/learned/typography-self-reference.md` (read only): not edited; `ops/learned/` is intentionally untouched per audit Section 7.
- `context/soul.md` (read only): context preflight.
- `context/user.md` (read only): context preflight.
- `ops/sessions/2026-04-30-docs-canon-steward.md` (created): branch session log.
- `ops/experts/report-05.md` (created): this file.

## Outcome

- Tests: N/A. No Python touched, no test suite run.
- New deps: none.
- Behavior change: `context/experts.md` Section A now lists eight filled experts (Code Quality, Flask App, Marketing Site, Data and Storage, Security Reviewer, Test Engineer, Intelligence/Answering, Docs/Canon Steward) plus the parked Importer Engineer placeholder. Docs/Canon Steward exists as a routable target for future doctrine-integrity work and the audit-NN.md series. The Phase 3A status note body reflects post-audit reality. No code, no tests, no product surface, no user-visible behavior changed.

## Observations

This is the final branch requiring the forward-reference workaround. Per audit Section 5 item 1, the next doctrine branch (recommendation 2: Routing Justification block in `context/template-h.md`) routes normally through Docs/Canon Steward + Senior Engineer. From that branch onward the routing reference resolves backward into existing canon, not forward into a not-yet-existing role.

The pass-2 stanza shape in `chatgpt-13-pass2.md` named five fields (Lens, Owns, Triggers, Proof required, Out of scope). This branch kept four of those (Lens, Owns, Triggers, Out of scope) and added Stack docs, Project canon, and Learned patterns to keep field parity with the seven sibling Section A experts. Proof required is intentionally omitted here because it is being added uniformly across all Section A experts in a separate branch (audit recommendation 3); adding it on this branch alone would break the parity invariant the next branch depends on.

Stack docs is a single italicized parenthetical noting that Docs/Canon Steward has no external technology stack: the role is project-canon integrity, not a framework or runtime. This is the first Section A expert with an empty Stack docs list; the parenthetical preserves the field shape without inventing a fake link.

The Learned patterns list cites only `ops/learned/typography-self-reference.md`. That pattern is load-bearing for every doctrine branch, including this one, because the canonical risk in doctrine work is silently reproducing in the rule-enforcing document the very artifact the rule prohibits. This branch took explicit care to avoid the long-dash glyph (U+2014) in the new stanza, the session log, and this report.

The numbering at 05 (skipping 03) follows audit Section 4b: no stub for unrouted work, no retroactive entry. The directory taxonomy continues to hold.

Section A stanzas exhibit a documented drift that this branch did not fix: the Flask App Engineer entry at line 97 cites `ops/learned/typography-self-reference.md` as "design-token discipline for CSS work," which mismatches the actual content of that file. The mismatch is a candidate for a follow-up Steward branch and is recorded here without action, per the prompt's scope lock.

This branch produced no reusable pattern for `ops/learned/`. Phase 5 audit Section 7 forbids audit-adjacent branches from creating learned-pattern files without empirical pain. The forward-reference workaround was the audit's own anticipated case; the branch executing it does not produce a new pattern.
