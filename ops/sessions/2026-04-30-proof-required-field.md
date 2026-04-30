# Proof Required Field (Phase 5 recommendation 3)

Date: 2026-04-30
Branch: chore/proof-required-field
PR: (pending)

## Scope

Second normal-routed doctrine branch after the Phase 5 forward-reference exemption window closed at PR #199, and the first branch whose Routing block was required by `context/template-h.md` (PR #200's Routing Justification deliverable applied downstream). Routing remained Docs/Canon Steward (Section A) plus Senior Engineer (Section B, implicit default). The prompt's ROUTING block satisfied the Why-this-expert plus Why-not-adjacent-experts requirement codified by PR #200, demonstrating that the structural pressure point shipped on the prior branch survives contact with its first downstream consumer.

Added a `**Proof required.**` field to every filled Section A expert in `context/experts.md`, codifying expert-specific evidence standards as a structural pressure point. Each block is 5 bullets, inserted between the existing `**Triggers.**` and `**Out of scope.**` blocks. The field set per filled stanza grew from seven fields to eight; the count of filled experts is unchanged at eight.

## Files created

- `ops/sessions/2026-04-30-proof-required-field.md`: this file.
- `ops/experts/report-07.md`: routed expert report.

## Files edited

- `context/experts.md`: eight localized insertions, one per filled Section A expert. Insertion point in every stanza was immediately after the closing line of the `**Triggers.**` block and immediately before the `**Out of scope.**` heading. No other content touched. No deletions. No reordering. No content change to existing fields. The Phase 3A status note at the top of the file remains accurate (eight filled experts plus one parked placeholder; the count of filled experts is unchanged).

## Files intentionally not edited

Per scope lock:

- `context/template-h.md`: recommendation 4 (Routing Examples) lives in `experts.md`, not `template-h.md`. Future cadence-codification work may touch `template-h.md`, but not this branch.
- The Importer Engineer placeholder in `context/experts.md`: parked is parked. The placeholder has no `**Triggers.**` or `**Out of scope.**` blocks, and the new field is conceptually anchored to those two blocks. Adding Proof required to a parked, unfilled expert would smuggle expert-shape into a non-expert.
- The Phase 3A status note in `context/experts.md`: count of filled experts is unchanged.
- The mini-review checklist at the end of Section A in `context/experts.md` (the Phase 3A integration gate block).
- The Section B stances in `context/experts.md`: stances do not gain a Proof required field; only Section A experts do, per audit Section 3 row 3.
- The Flask App Engineer stanza's `Learned patterns` description of `typography-self-reference.md` (recorded canon-drift finding from `report-05.md`). Reserved for a follow-up Steward branch.
- The Stack docs `(none for v1)` placeholder shape from `report-05.md` Observations: codify only after a second instance.
- `CLAUDE.md`, `DECISIONS.md`, `ROADMAP.md`, `README.md`, `SECURITY.md`, `CHANGELOG.md`.
- `ops/learned/`: Phase 5 audit Section 7 forbids audit-adjacent branches from updating it. Three pattern candidates recorded in `report-06.md` Observations remain unpromoted because none has been validated by a second instance.
- `ops/phase-5/`, `ops/phase-5-input/`, all existing `ops/experts/report-*.md`, all existing `ops/sessions/*.md`.
- `pyproject.toml`, `src/app/static/app.css`, `src/`, `tests/`, `.github/`, `docs/`, `landing/`, `site/`.
- All lockfiles.

## Verified Facts confirmed during preflight

- PR #199 and PR #200 were both confirmed merged (`gh pr list --state all` shows both with state MERGED). Local `main` was fast-forwarded by 1 commit (`f0eed37`, the PR #200 squash) before the new branch was cut.
- `context/template-h.md` still contains the `### Routing Justification` subsection inside `## Expert and stance routing`. Confirmed; PR #200 has not been reverted.
- `context/experts.md` Section A had eight filled stanzas plus one parked Importer Engineer placeholder. Confirmed by full file read.
- Baseline counts before the edits: `**Triggers.**` 8, `**Proof required.**` 0, `**Out of scope.**` standalone format 8. Confirmed by grep.
- Importer Engineer placeholder had no `**Triggers.**` or `**Out of scope.**` blocks. Confirmed by full read of the stanza body.
- `ls ops/experts/` showed `report-01.md`, `report-02.md`, `report-04.md`, `report-05.md`, `report-06.md`. Next sequential is 07. Gap at 03 remains intentional per audit Section 4b.
- `### Routing Examples` heading does not exist in `context/experts.md`. Recommendation 4 ordering preserved.

## Trust gate

All checks passed:

- Symmetry canary (the load-bearing check): `**Triggers.**` 8, `**Proof required.**` 8, `**Out of scope.**` standalone 8. Three counts equal; field shape consistent across all eight filled stanzas.
- Per-expert content variety: 40 unique added bullets across the diff (5 bullets times 8 experts, no boilerplate sharing).
- Importer Engineer untouched: zero occurrences of "Proof required" inside the placeholder body.
- Field order: every filled stanza shows `**Triggers.**` then `**Proof required.**` then `**Out of scope.**` at lines 60/67/74, 106/113/120, 149/156/163, 192/200/207, 236/243/250, 276/283/290, 318/326/333, 362/372/379.
- Em-dash sweep across all three touched files (`context/experts.md`, this session log, `ops/experts/report-07.md`): zero matches for U+2014.
- `### Routing Examples` heading absent (rec 4 ordering preserved).
- `git diff --check` clean.

## Tests

None run. No Python touched. No pytest invoked per scope lock.

## Next branch

Recommendation 4 from the Phase 5 audit Section 5 ordering: add a Routing Examples section to `context/experts.md`. Routing changes from Docs/Canon Steward plus Senior Engineer to Docs/Canon Steward plus Teaching Engineer, because examples are pedagogy per audit Section 3 row 6. Recommendation 4 will pull precedent from reports 01, 02, and 04 plus three to four hypothetical-but-grounded cases, capped at 8 to 12 examples per pass-2's guidance.

After recommendation 4 lands, the Phase 5 implementation order ends. Recommendation 5 (Importer Engineer fill) remains DEFERRED until empirical importer friction surfaces. Recommendation 6 (Release/Ops Engineer) remains REJECTED for now per pass-2's threshold.

If a generalizable pattern emerged from this branch (the per-expert symmetry technique, the count-equivalence canary that converts a structural invariant into a single grep-able check, or the field-anchoring discipline that prevents the parked Importer Engineer placeholder from being filled by accident), it should be promoted to `ops/learned/` only on a separate follow-up branch. The audit-cadence codification suggested in `report-05.md` and the trust-gate-as-skill candidate from `report-06.md` remain queued behind recommendation 4. Phase 5 audit Section 7 still forbids audit-adjacent branches from creating learned-pattern files without empirical pain, and no second-instance validation has occurred for any of the candidates.
