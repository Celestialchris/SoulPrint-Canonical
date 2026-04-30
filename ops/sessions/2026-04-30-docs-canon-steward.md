# Docs/Canon Steward Fill (Phase 5 recommendation 1)

Date: 2026-04-30
Branch: chore/docs-canon-steward
PR: (pending)

## Scope

Filled the Docs/Canon Steward expert in `context/experts.md` per the pass-2 narrow proposal at `ops/phase-5-input/chatgpt-13-pass2.md` lines 516-549 and the Phase 5 audit Section 3 row 5 disposition. Refreshed the Phase 3A status note body to reflect post-audit reality (eight filled experts plus parked Importer Engineer; routed reports 01, 02, 04 plus Phase 5 self-audit). Used the one-time forward-reference routing workaround documented in audit Section 5 item 1: this branch routes through Senior Engineer (Section B) with the Section A reference resolving forward, because the expert it names did not exist on `main` until this branch lands.

This is the last branch entitled to the forward-reference exemption. From the next doctrine branch onward (recommendation 2: Routing Justification block in `context/template-h.md`), every doctrine-touch branch routes normally through Docs/Canon Steward + Senior Engineer, or Docs/Canon Steward + Teaching Engineer when the work is pedagogical.

## Files created

- `ops/sessions/2026-04-30-docs-canon-steward.md`: this file.
- `ops/experts/report-05.md`: routed expert report. Numbering follows audit Section 4b (no stub at 03; next sequential is 05).

## Files edited

- `context/experts.md`: inserted the Docs/Canon Steward stanza between the Intelligence/Answering Engineer separator and the Importer Engineer placeholder. Refreshed the Phase 3A status note body. Field shape (Lens, Owns, Stack docs, Project canon, Learned patterns, Triggers, Out of scope) mirrors the seven sibling experts. No Proof required field; that arrives uniformly across all Section A experts in recommendation 3 on a separate branch.

## Files intentionally not edited

Per scope lock:

- `context/template-h.md`: recommendation 2 (Routing Justification block) belongs to the next branch.
- All other Section A expert stanzas in `context/experts.md`: must not gain a Proof required field on this branch; that is recommendation 3, a uniform edit on a separate branch.
- Section B stances in `context/experts.md`: no changes from this branch.
- Mini-review checklist (Phase 3A integration gate) and Expert reports section in `context/experts.md`: historical, not edited by this branch.
- `CLAUDE.md`, `DECISIONS.md`, `ROADMAP.md`, `README.md`, `SECURITY.md`, `CHANGELOG.md`.
- `ops/learned/`: Phase 5 audit Section 7 forbids audit-adjacent branches from updating `ops/learned/`. Patterns earn entry through real failures; this branch produced no such failure.
- `ops/phase-5/`, `ops/phase-5-input/`, all existing `ops/experts/report-*.md`, all existing `ops/sessions/*.md`.
- `pyproject.toml`, `src/app/static/app.css`, `src/`, `tests/`, `.github/`, `docs/`, `landing/`, `site/`.
- All lockfiles.

## Verified Facts confirmed during preflight

- `context/experts.md` Section A had seven filled experts plus the parked Importer Engineer placeholder. Confirmed by reading the file top to bottom.
- All seven filled experts shared the field shape Lens / Owns / Stack docs / Project canon / Learned patterns / Triggers / Out of scope (Code Quality Engineer additionally has Internal dependencies). No filled expert carried a Proof required field. Confirmed by file read; the new stanza matches sibling shape.
- The pass-2 narrow Docs/Canon Steward proposal at `ops/phase-5-input/chatgpt-13-pass2.md` lines 516-549 specified five fields (Lens, Owns, Triggers, Proof required, Out of scope). This branch kept four of those (Lens, Owns, Triggers, Out of scope) and added Stack docs, Project canon, and Learned patterns to maintain field parity with sibling experts.
- The audit document at `ops/phase-5/audit-phase-5.md` Section 5 item 1 named the forward-reference exemption explicitly, and Section 4b ratified the no-stub numbering rule.
- `ls ops/experts/` showed report-01.md, report-02.md, report-04.md only. No stub at 03. The next sequential routed report is 05.
- The pre-Phase-5 doctrine cleanup PR (canon-existence check in `template-h.md` Review Protocol; path-injection canonical shape inlined at the top of `ops/learned/codeql-taint-vs-relative-to.md`) had landed on `main`. Confirmed by reading `context/template-h.md`'s Review Protocol section.

## Tests

None run. No Python touched. No pytest invoked per scope lock.

## Next branch

Recommendation 2 from the Phase 5 audit Section 5 ordering: add the Routing Justification block (Why-this-expert, Why-not-adjacent) to `context/template-h.md`. Routes through Docs/Canon Steward + Senior Engineer, normally, with no forward-reference exemption. The exemption window closes with this branch.

If a generalizable doctrine-integrity pattern emerges from future Steward branches (a portability friction, an unexpected scope-leak class, a self-reference pitfall), promote it to `ops/learned/` on a separate follow-up branch. Not on this one.
