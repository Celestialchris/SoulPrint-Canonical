# Expert Report 06: chore/routing-justification-block

Date: 2026-04-30
Branch: chore/routing-justification-block
PR: (pending)
Template H prompt: inline (Phase 5 recommendation 2, Routing Justification block)

## Routing

Section A expert: Docs/Canon Steward
Section B stance: Senior Engineer

## Reads consumed during drafting

- `context/template-h.md` (project canon, pattern-mirror + edit-target): full file read; confirmed the three target sections (`## Expert and stance routing`, `## Review protocol for generated prompts`, `## Compact skeleton`) and that the strict-order list has exactly 14 numbered subsections, `### 0.` through `### 13.`, which were not modified.
- `context/experts.md` (project canon, read-to-verify): confirmed Section A has eight filled experts plus parked Importer Engineer (post-PR-199), and that no Proof required field exists on any expert (rec 3 ordering preserved).
- `ops/phase-5/audit-phase-5.md` (read-to-verify): Section 3 row 1 (Routing Justification: ACCEPTED, owning expert Docs/Canon Steward + Senior Engineer), Section 5 item 2 (audit's ordering rationale: smallest doctrine change first, sets discipline precedent for the larger one that follows), Section 6 question 1 (audit-20 will check whether the Routing Justification block actually got used and whether Why-not-adjacent reasoning ever caught a routing error).
- `ops/experts/report-05.md` (pattern-mirror + read-to-verify): format reference; confirmed the forward-reference exemption window closed at PR #199 and recorded the two follow-up Steward findings that this branch must not touch.
- `ops/experts/report-04.md` (pattern-mirror): secondary report format reference.
- `ops/learned/typography-self-reference.md` (pattern-mirror): doctrine-self-reference discipline; load-bearing because this branch is doctrine work and the new content references the long-dash glyph rule by U+2014 implication only, never by literal character.

## Reads consumed during execution by Claude Code

- `context/template-h.md` (read, edited): inserted the `### Routing Justification` subsection at the end of `## Expert and stance routing`, added one new bullet to `## Review protocol for generated prompts`, added a `## ROUTING` block to the `## Compact skeleton` template.
- `context/experts.md` (read only): not edited; this is the lock that distinguishes recommendation 2 from recommendation 3.
- `ops/phase-5/audit-phase-5.md` (read only): not edited.
- `ops/experts/report-05.md` (read only): format reference and verified-fact source; not edited.
- `context/soul.md` (read only): context preflight.
- `context/user.md` (read only): context preflight.
- `ops/sessions/2026-04-30-routing-justification-block.md` (created): branch session log.
- `ops/experts/report-06.md` (created): this file.

## Outcome

- Tests: N/A. No Python touched, no test suite run.
- New deps: none.
- Behavior change: `context/template-h.md` now codifies the Routing Justification specification. Three localized changes: the new `### Routing Justification` subsection inside `## Expert and stance routing`, one new bullet in `## Review protocol for generated prompts`, and a new `## ROUTING` block in `## Compact skeleton`. The strict-order list and all other sections are unchanged. From this branch onward, every Template H prompt that names a Section A expert and a Section B stance is required to also include a Routing block with Why-this-expert and Why-not-adjacent-experts sub-blocks (minimum 2 bullets each), or document an explicit exemption citing the authorizing audit or session note.

## Observations

First normal-routed doctrine branch after the Phase 5 forward-reference exemption window closed at PR #199. The Routing block this branch codifies was already used in this very prompt, demonstrating the structural shape that future prompts will follow.

The audit's Section 5 item 2 rationale held in practice: this is "the smallest doctrine change" and was small enough to land cleanly with three localized edits and no strict-order renumbering. The diff is +37 lines on `context/template-h.md` (or thereabouts), all additive, with no deletions and no reflow of surrounding content. The Compact skeleton's bracket-placeholder convention was preserved at insertion; the canonical-shape example in the new subsection used angle-bracket placeholders to match its own purpose as documentation rather than copy-paste template.

The audit-hook line in the new subsection is the explicit cross-reference that closes the loop with audit-20's Section 6 question 1: audit-20 can mechanically count routed prompts that include the Routing block versus those that omit it, and can check whether Why-not-adjacent reasoning ever caught a routing error that the prior structure would have allowed through. The success criterion is countable rather than judgmental.

The Section B default rule in the new subsection codifies a discipline that reports 02, 04, and 05 demonstrated in practice (Senior Engineer as implicit default; non-default stances justified inside the Why-this-expert block when triggered). Codifying it here turns the discipline from agent-instinct into a checklist item the Review Protocol can enforce.

The documented-exemption rule names PR #199 explicitly as the closed forward-reference window. New forward-reference exemptions now require explicit authorization from a future audit; agents cannot self-grant the exemption.

Recommendation 3 (Proof Required field on every Section A expert in `context/experts.md`) is the next queue item and routes normally through Docs/Canon Steward + Senior Engineer. Recommendation 4 (Routing Examples in `experts.md`) follows that, routing through Docs/Canon Steward + Teaching Engineer. This branch did not preempt either.

This branch produced no reusable pattern for `ops/learned/`. Three candidate patterns were noted in the session log for possible future promotion (the four-backtick-wrapped doctrine snippet convention, the bracket-vs-angle-bracket placeholder distinction, the audit-hook closing-the-loop pattern), but Phase 5 audit Section 7 forbids audit-adjacent branches from creating learned-pattern files without empirical pain. None of those patterns has been validated by a second instance yet.
