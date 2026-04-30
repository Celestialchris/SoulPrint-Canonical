# Expert Report 07: chore/proof-required-field

Date: 2026-04-30
Branch: chore/proof-required-field
PR: (pending)
Template H prompt: inline (Phase 5 recommendation 3, Proof Required field on every filled Section A expert)

## Routing

Section A expert: Docs/Canon Steward
Section B stance: Senior Engineer

## Reads consumed during drafting

- `context/experts.md` (project canon, pattern-mirror plus edit-target): full Section A read top to bottom; confirmed the eight filled experts in the order Code Quality / Flask App / Marketing Site / Data and Storage / Security Reviewer / Test Engineer / Intelligence/Answering / Docs/Canon Steward, the field set per stanza (Lens / Owns / Stack docs / Project canon / optional Internal dependencies / Learned patterns / Triggers / Out of scope), the Importer Engineer placeholder lacking `**Triggers.**` or `**Out of scope.**` blocks, and the absence of any `**Proof required.**` field in the baseline file.
- `context/template-h.md` (project canon, read-to-verify): confirmed PR #200's `### Routing Justification` subsection inside `## Expert and stance routing` is still present.
- `ops/phase-5/audit-phase-5.md` (read-to-verify): Section 3 row 3 (Proof Required field: ACCEPTED, owning expert Docs/Canon Steward plus Senior Engineer), Section 5 item 3 (audit's ordering rationale: codifies expert-specific evidence standards into a structural pressure point), Section 6 question 2 (audit-20 will check whether the Proof Required field caused Outcome sections to become more uniform).
- `ops/phase-5-input/chatgpt-13-pass2.md` (pattern-mirror, lines 198-220): pass-2 narrow proposal for Proof Required, with the Code Quality Engineer 5-bullet shape used as the canonical reference for the per-expert blocks pre-authored in this branch's prompt.
- `ops/experts/report-06.md` (pattern-mirror plus read-to-verify): most recent routed report, used as report format reference; also confirmed PR #200 merged via squash to `f0eed37` and that the trust-gate-as-skill discipline applied on the prior branch should mirror to this one.
- `ops/experts/report-05.md` (pattern-mirror): secondary report format reference (Docs/Canon Steward fill, PR #199).
- `ops/learned/typography-self-reference.md` (pattern-mirror): doctrine-self-reference discipline; load-bearing for this branch because the work is itself doctrine work and the new content references the long-dash glyph rule by Unicode code point implication only, never by literal character.
- `ops/sessions/2026-04-30-routing-justification-block.md` (pattern-mirror): session log format reference for the prior branch (PR #200), used as the structural template for this branch's session log.

## Reads consumed during execution by Claude Code

- `context/experts.md` (read, edited): inserted eight `**Proof required.**` blocks, one per filled Section A expert, between the existing `**Triggers.**` and `**Out of scope.**` blocks in each stanza. No other content touched.
- `context/template-h.md` (read only): not edited; this file is the lock that distinguishes recommendation 3 from any future cadence-codification work.
- `ops/phase-5/audit-phase-5.md` (read only): not edited.
- `ops/phase-5-input/chatgpt-13-pass2.md` (read only): not edited.
- `ops/experts/report-06.md` (read only): format reference and verified-fact source; not edited.
- `ops/experts/report-05.md` (read only): format reference; not edited.
- `ops/learned/typography-self-reference.md` (read only): not edited; `ops/learned/` is intentionally untouched per audit Section 7.
- `ops/sessions/2026-04-30-routing-justification-block.md` (read only): format reference; not edited.
- `context/soul.md` (read only): context preflight.
- `context/user.md` (read only): context preflight.
- `ops/sessions/2026-04-30-proof-required-field.md` (created): branch session log.
- `ops/experts/report-07.md` (created): this file.

## Outcome

- Tests: N/A. No Python touched, no test suite run.
- New deps: none.
- Behavior change: `context/experts.md` Section A now carries a `**Proof required.**` field in every filled stanza. The eight new blocks are 5 bullets each, per-expert, with no boilerplate sharing across stanzas. Each block sits between the existing `**Triggers.**` and `**Out of scope.**` blocks. The field set per filled stanza grew from seven to eight fields; the count of filled experts is unchanged at eight. The Importer Engineer placeholder is unchanged. The Phase 3A status note is unchanged. `context/template-h.md` is unchanged. From this branch onward, every routed prompt that names a Section A expert is judged against that expert's specific evidence standard; Outcome sections in future routed reports inherit a concrete target rather than inventing proof shape per branch.

## Observations

Second normal-routed doctrine branch after the Phase 5 forward-reference exemption window closed at PR #199. First branch whose Routing block was required by `context/template-h.md` (PR #200's Routing Justification deliverable applied downstream); the prompt's ROUTING block satisfied the Why-this-expert and Why-not-adjacent-experts requirement codified by PR #200. The structural pressure point shipped on the prior branch survived contact with its first downstream consumer without friction.

The audit's Section 5 item 3 rationale held in practice: this is the larger doctrine diff, codifying expert-specific evidence standards. The diff is +60 lines on `context/experts.md` (8 stanzas times 7.5 lines each on average, all additive, no deletions, no reflow of surrounding content). The Routing Justification block from the prior branch made the Why-not-adjacent reasoning structural; the Proof Required field on this branch makes the success-criterion-per-expert structural. The two pressure points compose: future audits can check both routing rigor (was the choice justified?) and proof rigor (did the work meet the expert's evidence standard?) mechanically rather than judgmentally.

The symmetry canary (count equivalence across `**Triggers.**`, `**Proof required.**`, `**Out of scope.**` headings, all expected to equal 8) was the single load-bearing trust-gate check on this branch. It catches every plausible failure mode with one grep: a skipped stanza drops one count below 8, an accidental Importer Engineer fill pushes one count to 9, a typo in any heading drops the matching count, a stray duplicate insertion pushes one count up. The check passed at 8 / 8 / 8 across all three counts. The structural property that makes this work is the format asymmetry between Section A and Section B: Section A renders these field names on their own line (matched by `^...\s*$`), Section B renders the same field name inline as the start of a paragraph (not matched). The canary works precisely because it exploits this format asymmetry; in a future doctrine port to another project, the canary either travels with the format or has to be re-derived against the new format.

The per-expert content variety check (at least 35 unique added bullet lines across the diff) confirmed no boilerplate sharing across stanzas. The actual count was 40, equal to 5 bullets times 8 experts with zero overlaps; each expert's evidence standard is genuinely expert-specific. This is the empirical answer to pass-2's framing that Proof Required converts each expert from "a role" into "a standard of evidence": a uniform standard would have collapsed bullets across stanzas, an expert-specific standard does not.

The Importer Engineer placeholder was untouched. The placeholder's lack of `**Triggers.**` and `**Out of scope.**` blocks is the structural reason: the Proof Required field is conceptually anchored to those two blocks (it sits between them in every filled stanza), and a parked stanza without those anchors cannot accept the new field without becoming filled by accident. The audit-Section-5-item-5 deferral is preserved by this structural anchoring discipline rather than by an explicit branch instruction.

The two follow-up Steward findings recorded in `report-05.md` Observations remain unaddressed (the Flask App Engineer typography-self-reference description drift, and the Stack docs `(none for v1)` placeholder pattern). The three additional pattern candidates recorded in `report-06.md` Observations also remain unpromoted (four-backtick-wrapped doctrine snippets, bracket-vs-angle-bracket placeholder convention, audit-hook closing-the-loop pattern). Phase 5 audit Section 7 forbids audit-adjacent branches from updating `ops/learned/` without empirical pain; none of these candidates has been validated by a second instance.

Recommendation 4 (Routing Examples in `context/experts.md`) is the next queue item and routes through Docs/Canon Steward plus Teaching Engineer because examples are pedagogy per audit Section 3 row 6. After recommendation 4 lands, the Phase 5 implementation order ends; recommendation 5 (Importer Engineer fill) remains DEFERRED, recommendation 6 (Release/Ops Engineer) remains REJECTED for now.

This branch produced no reusable pattern for `ops/learned/` directly. Two candidate patterns surfaced and are noted here for possible future promotion if a second instance occurs: the per-expert symmetry technique (insert the same field shape into N parallel stanzas, verify with count-equivalence across surrounding fields), and the field-anchoring discipline that uses an existing field's presence as the structural prerequisite for accepting a new field, preventing accidental fills of parked placeholders. Neither has been validated by a second instance yet, so neither is promoted on this branch.
