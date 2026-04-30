# Routing Justification Block (Phase 5 recommendation 2)

Date: 2026-04-30
Branch: chore/routing-justification-block
PR: (pending)

## Scope

First normal-routed doctrine branch after the Phase 5 forward-reference exemption window closed at PR #199. Routing was standard: Docs/Canon Steward (Section A, now active in `context/experts.md`) plus Senior Engineer (Section B, implicit default). No forward-reference framing applies; the routing reference resolves backward into existing canon.

Added the Routing Justification specification to `context/template-h.md` via three localized edits, codifying the Why-this-expert / Why-not-adjacent-experts discipline that PR #199's prompt body already practiced ad hoc:

1. Inserted a new `### Routing Justification` subsection at the end of the existing `## Expert and stance routing` section. The subsection specifies the canonical block shape, the 2-bullet minimum, the soft 6-bullet ceiling, the Section B default rule, the documented-exemption rule (with PR #199 named as the closed-exemption window), and the audit-20 hook.
2. Added one new bullet to the `## Review protocol for generated prompts` checklist: "the prompt's ROUTING block exists with Why-this-expert and Why-not-adjacent-experts sub-blocks (minimum 2 bullets each), OR an explicit exemption is documented citing the authorizing audit or session note;". Placed immediately after the canon-existence bullet to group the structural-block checks.
3. Added a `## ROUTING` block to the `## Compact skeleton` template, positioned between `## CONTEXT PREFLIGHT` and `## MANDATORY READS`. Used bracket-placeholder style (`[name]`, `[bullet]`, `[expert]`, `[reason]`) to match the rest of the skeleton.

The strict-order list (`### 0. Context preflight` through `### 13. Session log and learned pattern update`) was not modified. No subsections renumbered or restructured. The new `### Routing Justification` is unnumbered and lives outside that list, inside its semantic parent section.

## Files created

- `ops/sessions/2026-04-30-routing-justification-block.md`: this file.
- `ops/experts/report-06.md`: routed expert report.

## Files edited

- `context/template-h.md`: three localized edits as described above. No other content touched.

## Files intentionally not edited

Per scope lock:

- `context/experts.md`: this is the lock that distinguishes recommendation 2 from recommendation 3. Proof Required field (rec 3) and Routing Examples (rec 4) are separate branches that will edit `experts.md`. Touching `experts.md` here would conflate the recommendations.
- The strict-order list in `context/template-h.md`: no subsections inserted, removed, or renumbered. The Routing Justification specification belongs in the existing `## Expert and stance routing` section, not in the strict-order list.
- The Flask App Engineer stanza in `experts.md`: the typography-self-reference description drift recorded in `report-05.md` Observations is reserved for a follow-up Steward branch.
- The `(none for v1)` Stack docs placeholder shape from `report-05.md` Observations: codify only after a second instance of stanza-shape preservation without an external link.
- `CLAUDE.md`, `DECISIONS.md`, `ROADMAP.md`, `README.md`, `SECURITY.md`, `CHANGELOG.md`.
- `ops/learned/`: Phase 5 audit Section 7 forbids audit-adjacent branches from updating it. Patterns earn entry through real failures; this branch produced no such failure.
- `ops/phase-5/`, `ops/phase-5-input/`, all existing `ops/experts/report-*.md`, all existing `ops/sessions/*.md`.
- `pyproject.toml`, `src/app/static/app.css`, `src/`, `tests/`, `.github/`, `docs/`, `landing/`, `site/`.
- All lockfiles.

## Verified Facts confirmed during preflight

- PR #199 was confirmed merged (state MERGED, mergedAt 2026-04-30T14:55:44Z) before branching. `main` was fast-forwarded by 1 commit (3 files, +156 / -1) to absorb the Docs/Canon Steward stanza and `report-05.md` before the new branch was cut.
- `context/template-h.md` `## Expert and stance routing` section ended with the line "Do not duplicate expert or stance content inside the prompt. The picks are a pointer; \`context/experts.md\` is the canon." with no `### Routing Justification` subsection beneath. Confirmed by full file read.
- `## Template H structure, strict order` had exactly 14 numbered subsections, `### 0. Context preflight` through `### 13. Session log and learned pattern update`. Confirmed; this list is unchanged after the edits.
- `## Review protocol for generated prompts` had 9 bullets ending with the canon-existence-style content. The new bullet brings the list to 10. Position is immediately after the canon-existence bullet, before the assumptions-separated-from-facts bullet, grouping the structural-block checks.
- `## Compact skeleton` fenced markdown block had no `## ROUTING` section. The new block sits between `## CONTEXT PREFLIGHT` description and `## MANDATORY READS` heading, mirroring the canonical position the new Routing Justification subsection requires for prompts.
- `context/template-h.md` contained zero em-dash characters before the edits. Confirmed by grep. The edits introduced none; the new content uses commas, colons, semicolons, and hyphens only.
- `ls ops/experts/` showed `report-01.md`, `report-02.md`, `report-04.md`, `report-05.md`. Next sequential is 06.

## Tests

None run. No Python touched. No pytest invoked per scope lock.

## Next branch

Recommendation 3 from the Phase 5 audit Section 5 ordering: add the Proof Required field to every Section A expert in `context/experts.md`. Routing remains Docs/Canon Steward + Senior Engineer. The new Routing Justification block this branch shipped sets the precedent for "structural pressure point" doctrine additions; the Proof Required field is the next instance of the same pattern, codifying expert-specific evidence standards into a structural pressure point that future audits can mechanically check.

If a generalizable pattern emerged from this branch (the four-backtick-wrapped doctrine snippet with one inner three-backtick example that gets unwrapped at insertion time, the bracket-vs-angle-bracket placeholder distinction between canonical-shape examples and copy-paste skeletons, or the audit-hook line that closes the loop between a doctrine deliverable and the next audit's measurable success criterion), it should be promoted to `ops/learned/` only on a separate follow-up branch, not on this one. Phase 5 audit Section 7 holds.
