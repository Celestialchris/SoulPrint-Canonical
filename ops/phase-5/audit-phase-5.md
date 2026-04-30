# Phase 5: Routing-System Self-Audit

Date: 2026-04-30
Reports audited: 01, 02, 04 (gap at 03 is intentional; documented in `ops/sessions/2026-04-30-netlify-to-cloudflare-pivot.md`)
Doctrine artifacts audited: `context/experts.md`, `context/template-h.md`, the `CLAUDE.md` session-start trigger, `DECISIONS.md` (referential)
Input agenda: `ops/phase-5-input/chatgpt-13-pass2.md` (pass-2 only; pass-1 is fossil record)

This audit is exempt from the numbered-report protocol. The exemption is itself a Phase 5 finding (see Section 4). The next routing-system audit will be `ops/phase-5/audit-20.md` and will route normally if Docs/Canon Steward has been promoted by then.

---

## 1. Evidence Summary (per report)

### Report 01: `feat/quality-toolchain-mvp` (Code Quality Engineer + Senior Engineer)

The first run after the routing doctrine landed. Routing was clean: a CRAP-scoring toolchain MVP belongs to the expert who owns `src/quality/`. The branch shipped exactly the named scope (toolchain code, deps, README, 12 new tests, one learned pattern, one session log, one report) with no surface-feature smuggling. Every drafting read in the report's Reads list was actually consumed during execution. The report's load-bearing finding was a refutation of one Verified Fact: `coverage.py` was named in the Code Quality Engineer's "Internal dependencies" list as if installed, but `pyproject.toml` had no entry and CI did not invoke it. The drafter mistook routing-doctrine *intent* for installed *reality*. This refutation later landed in Template H's Review Protocol (PR #197) as the canon-existence check. No compounding learned-pattern drift; one new pattern (`per-function-coverage-from-line-data.md`) emerged organically from the work.

### Report 02: `fix/codeql-path-injection-assets` (Security Reviewer + Senior Engineer)

Textbook fit. Two doctrine documents (`static-analyzer-shape-matching.md` plus `codeql-taint-vs-relative-to.md`) and one live-code pattern-mirror (`claude_code_discovery.py:42-55`) drove the fix. The branch touched exactly one production file and added exactly one test file; +3 tests precisely matching the new file. The Out of Scope list visibly held. No coverage hardening, no test-ergonomics work, no schema changes leaked in. The report explicitly notes that "any other stance would have been pretense," which is the cleanest evidence so far that Senior-Engineer-as-implicit-default actually works as designed when no surface, copy, or multi-step-path concern exists. One soft observation: the path-injection canonical shape lived only as a code reference inside `claude_code_discovery.py`, not inlined in the learned doc. PR #197 absorbed this finding by promoting the path-injection shape to the top of `ops/learned/codeql-taint-vs-relative-to.md`. So report 02 produced both a clean execution and a small canon-improvement loop.

### Report 04: `chore/claude-review-skip-bots` (Test Engineer + Senior Engineer)

Tight pairing. The failure mode was a CI workflow misbehaving on bot PRs, which is workflow-reliability work, which is Test Engineer's domain. The Senior Engineer stance supplied the instinct to choose `user.type` (general, self-maintaining) over a hardcoded login allowlist (point-in-time, manual). The Template H assumption-verification step was load-bearing: a `gh api` check for branch protection was the go/no-go gate before any file was touched. Not Python; no test suite run, which the report acknowledges explicitly. One structural observation in the report itself: "report-03.md does not yet exist," recorded as a finding without action, deferred to Phase 5. Phase 5 takes the action below.

### The report-03 gap (subsection)

No routed report exists at the 03 slot. The branch that would have produced it (Netlify deployment fix) was obsoleted by the vendor pivot to Cloudflare Pages before any Section A + Section B prompt was written. The work-arc is recorded at `ops/sessions/2026-04-30-netlify-to-cloudflare-pivot.md` (PR #196). The gap proves the directory taxonomy works under stress: routed evidence lives in `ops/experts/`, unrouted work-arcs live in `ops/sessions/`, and a vendor pivot that never produced a routed prompt correctly produces no `report-NN.md` file rather than a stub. A stub at 03 would either lie (claiming routed evidence that does not exist) or duplicate the session note. The taxonomy refused both options and held the line.

The numbering itself is a small risk surface for future readers. See Section 7 (Drift Watch) for the recommended mitigation.

---

## 2. Doctrine Question Audit

**Q1. Did the routing in routed reports 01, 02, and 04 produce work that stayed in scope?**
Yes, all three. Report 01 delivered the toolchain scope without feature smuggling. Report 02 touched exactly one production file plus its dedicated test file. Report 04 stayed inside CI workflow scope and explicitly declined to touch Python. Test counts in each report match the new test files exactly (+12, +3, N/A). Evidence: `ops/experts/report-01.md:39-41`, `report-02.md:35-37`, `report-04.md:31-33`.

**Q2. Did the named drafting reads actually get consumed in execution?**
Yes. Each report enumerates drafting reads and execution reads as separate sections, and the executed-read list is a strict subset or extension of the drafted-read list, never a divergence. The strongest case is report 02, where `static-analyzer-shape-matching.md` and `codeql-taint-vs-relative-to.md` were both drafting canon and the actual sources for the fix shape. The notable case is report 01, where `pyproject.toml` was both drafted *and* turned into a Verified-Fact refutation source. That is proof that "pattern-mirror" plus "read-to-verify" labels load-bear when used.

**Q3. Did any report flag a doctrine drift, gap, or contradiction?**
Yes, three findings of varying severity. Report 01 produced a hard refutation: the Code Quality Engineer's Internal Dependencies list named `coverage.py` as if installed when no `pyproject.toml` entry existed. Severity: routing doctrine implied installed reality; reality disagreed. Absorbed into Template H's Review Protocol via PR #197. Report 02 produced a soft finding: path-injection canonical shape was not inlined in its natural learned-pattern home. Severity: doctrine completeness gap, not contradiction. Absorbed by PR #197 (path-injection section now first in the learned doc). Report 04 produced a structural observation: `report-03.md` missing. Severity: numbering taxonomy question; addressed by this Phase 5 audit (Section 4b).

**Q4. Did the Drafter Checklist in template-h.md catch what it was designed to catch?**
Mostly yes, by absence rather than active block. The canon-existence check (Review Protocol bullet on the canon/learned/report/spec/context citation rule) was added to Template H by PR #197 to absorb report-01's refutation. Reports 02 and 04, drafted after that fix landed, did not produce similar Verified-Fact-vs-installed-reality drift. This is weak evidence; three reports cannot prove the checklist works in general. But the trajectory is the right shape: the checklist absorbed a lesson from the first run and the next two runs did not repeat the failure. Audit-20 should stress-test this harder.

**Q5. Did Section B stance picks accurately match the work? Or did Senior-Engineer-default underfire?**
All three picks were Senior Engineer; all three were correct. Report 02's report explicitly explains why: no user-facing surface (would have been Lead Product Designer), no copy (Brand Guardian), no multi-step path (UX Strategist), no community-channel adaptation (Community-Voice Writer), no language the user does not yet read fluently (Teaching Engineer). Senior Engineer was the implicit default and correctly fired as the implicit default. There is no evidence yet of underfiring, but also no evidence yet of *over-firing* of non-default stances, because no non-default stance has been used in any of the three routed reports. The non-default stances remain unproven empirically; their first real test is still ahead.

**Q6. Did Out-of-Scope boundaries hold, or did scope leak between adjacent experts?**
Boundaries held. Report 02 is the strongest evidence: the Security Reviewer's Out-of-Scope list explicitly named Code Quality Engineer as the neighbor that owns coverage hardening and test ergonomics, and the report notes that boundary made the branch shape obvious "from the start." Report 04 stayed within Test Engineer's CI ownership without bleeding into Flask App Engineer or Security Reviewer. Report 01 stayed inside the toolchain scope without smuggling feature work. The Out-of-Scope sections are doing work, not decorating the file.

---

## 3. Pass-2 Agenda Disposition

| Recommendation | Status | Evidence | Owning expert (when implemented) |
|---|---|---|---|
| Routing Justification block in `template-h.md` (Why-this-expert / Why-not-adjacent) | ACCEPTED | Report 01's "drafter mistook routing-doctrine intent for installed reality" gap could have been caught earlier by an explicit forcing function naming the adjacent experts. Reports 02 and 04 implicitly justified routing in the body, proving the discipline lives in agents' heads but is not codified. Codifying it converts implicit discipline into a structural pressure point. | Docs/Canon Steward + Senior Engineer |
| Proof Required field per Section A expert in `experts.md` | ACCEPTED | Each report's Outcome section already enumerates expert-specific proof: CRAP scores and coverage in 01, alert closure plus regression test in 02, CI behavior change in 04. Codifying it pushes verification from voluntary to mandatory and shapes future Outcome sections without requiring agents to invent proof shape per branch. | Docs/Canon Steward + Senior Engineer |
| Expert Report Audit cadence (Option 1 / 2 / 3) | ACCEPTED, see Section 4 | Phase 5 itself proves the cadence is necessary: three reports produced one canon refutation, one canon completeness gap, and one numbering observation. Without scheduled audits these would accumulate without integration. | Audits route through Docs/Canon Steward + Senior Engineer once that expert is filled (audit-20 onward); Phase 5 is the only permanent exemption |
| Importer Engineer fill | DEFERRED | Pass-2 itself names this as the cleanest missing expert, but the empirical case requires three real branches that did not route cleanly. Phase 5 has zero importer reports yet, because no importer branch has run since the routing doctrine landed. The pain has not arrived. Defer until the next importer branch surfaces or until audit-20 sees three importer-shaped branches forced through Data + Flask + Test. | Importer Engineer when filled, via Docs/Canon Steward + Senior Engineer for the fill itself |
| Docs/Canon Steward (narrow doctrine-integrity scope, not "documentation writer") | ACCEPTED | Phase 5 exists *because* no Docs/Canon Steward exists; the routing exemption is the gap-shaped evidence. Promoting it from "candidate" to "active" gives a routing target for every Phase 5 follow-up branch (Routing Justification block, Proof Required field, Routing Examples, Importer Engineer fill when triggered). Without it, every doctrine-touch branch faces the same self-reference problem. The pass-2 narrow scope (no marketing, no product strategy, no implementation) prevents the role from absorbing everything. | Docs/Canon Steward (defining the role is itself the role's first job; fill via current Senior Engineer stance plus the narrow proposal in pass-2) |
| Routing Examples in `experts.md` | ACCEPTED | Reports 01, 02, 04 implicitly create the first three examples already. A dedicated section codifies precedent. Pass-2's phrase "precedent beats vibes" is exactly right. Reduces hallucinated routing for future drafters by giving them concrete prior decisions to imitate or contrast. | Docs/Canon Steward + Teaching Engineer (the stance that legitimizes example-as-pedagogy) |

Pass-2 also retracts Verification Judge, Conflict Protocol, Expert Lifecycle, and No-Expert-Needed Cases. These retractions stand. None reappear in Phase 5's accepted list.

Release/Ops Engineer remains in pass-2's parked-candidate state. Phase 5 does not promote it. Evidence threshold per pass-2 is "2-3 real reports show the same friction." We have zero. REJECTED for now (but note: rejection here means "do not add yet," not "never"). Revisit at audit-20.

---

## 4. Governance Position: Audit Cadence

**Position: Option 1 with auto-narrowing breaker clause.**

Phase 5 is a permanent exemption from numbered-report routing. This audit and any future audit of the routing system itself cannot route through the routing system without recursion. That part of Option 1 is unconditional.

The breaker clause: **once Docs/Canon Steward is promoted to an active Section A expert** (recommendation 5 above, ACCEPTED), the exemption auto-narrows. Audit-20.md, audit-40.md, and onward route through Docs/Canon Steward + Senior Engineer (or Docs/Canon Steward + Teaching Engineer when an audit is also pedagogical). The exemption stops being "all routing-system audits in perpetuity" and becomes "Phase 5 specifically, plus any future audit run before Docs/Canon Steward exists."

Evidence supporting this position:

- Pace: three routed reports landed in 48 hours (April 29-30). At even half that pace, twenty reports take roughly six to eight weeks. That is a workable cycle length.
- Phase 5 demonstrates the self-audit-exemption produces concrete output (this document) without infinite regress.
- The breaker clause prevents the exemption from becoming permanent doctrine bloat. Once the role exists that *can* route the audit, the audit *should* route through it. Otherwise the exemption itself becomes drift.

Refutation considered: Option 2 ("audit always self-exempt") rejected because it makes the exemption immortal and disconnects routing-system audits from the routing system they audit, which is exactly the structural fragility audits are supposed to surface. Option 3 ("audit always routed through some current expert") rejected because no current expert can audit the routing doctrine without recursion or fake authority. Phase 5 would have had to launder itself through Code Quality Engineer or Test Engineer or Security Reviewer, none of which own routing doctrine.

## 4b. Governance Position: Directory Taxonomy

**Position: ratify the taxonomy as canonical.**

- `ops/experts/report-NN.md` = routed Expert + Stance + Template H execution evidence only. Numbered. Immutable history once committed.
- `ops/sessions/` = work-arc records, including unrouted work like vendor-driven pivots, debugging campaigns that did not produce a routed branch, and any session that needs continuity but did not name a Section A expert and Section B stance.
- `ops/learned/` = reusable patterns extracted *after* pain proves itself. Patterns earn their entry through a real failure or a real shape-completeness gap; they are not pre-emptive.

The report-03 gap is the first empirical test case. The Netlify-fix work-arc was real, was nontrivial, but never produced a routed Section A + Section B prompt, because the work was obsoleted by the vendor pivot before any expert routing occurred. A stub `report-03.md` in `ops/experts/` would either fabricate routed evidence (lying) or duplicate the session note (rotting). The taxonomy correctly refused both options. The session note (`ops/sessions/2026-04-30-netlify-to-cloudflare-pivot.md`) absorbed the work-arc honestly. The numbering gap at 03 is the visible cost of structural honesty, and that is the right cost.

This taxonomy is canonical. Future audits inherit it. Future numbering gaps follow the same rule: an `ops/experts/report-NN.md` file exists if and only if a Template H prompt named a Section A expert and a Section B stance and the branch produced execution evidence. No stubs. No retroactive entries for unrouted work.

---

## 5. Recommended Implementation Order

The accepted recommendations from Section 3 must land in this order. Each entry names the routing for the implementing branch.

1. **Fill Docs/Canon Steward** in `context/experts.md`. Routing for the implementing branch: this is the single self-reference moment. The branch that adds Docs/Canon Steward cannot route through Docs/Canon Steward, so it routes through the current Senior Engineer stance with explicit acknowledgment in the prompt body that the routing reference is forward (this expert exists once the branch lands). All subsequent doctrine branches route through it.
2. **Add Routing Justification block** to `context/template-h.md`. Routing: Docs/Canon Steward + Senior Engineer. Smallest doctrine change; sets the discipline precedent for the larger one that follows.
3. **Add Proof Required field** to each Section A expert in `context/experts.md`. Routing: Docs/Canon Steward + Senior Engineer. Larger diff; codifies expert-specific evidence standards. Order matters: Routing Justification first because it is smaller and lower-risk; Proof Required second because once Routing Justification is mandatory, Proof Required gives the Verification step its concrete target.
4. **Add Routing Examples** section to `context/experts.md`. Routing: Docs/Canon Steward + Teaching Engineer. Teaching Engineer fits because examples are pedagogy. Pulls precedent from reports 01, 02, 04 plus three to four hypothetical-but-grounded cases. Caps the section at 8-12 examples per pass-2's guidance.
5. **Importer Engineer fill** is DEFERRED until either an importer branch surfaces or audit-20 confirms three branches did not route cleanly. Do not pre-fill on the strength of pass-2's argument alone; pass-2's own retraction discipline says wait for the pain.
6. **Release/Ops Engineer** is REJECTED for now per pass-2's threshold. Revisit at audit-20.

The Phase 5 exemption ends with the last accepted recommendation. The branch implementing recommendation 1 is the last branch to need any forward-reference workaround; from recommendation 2 onward, every doctrine branch routes normally through Docs/Canon Steward.

---

## 6. Open Questions for Audit-20

- Did the Routing Justification block actually get used in subsequent Template H prompts, and did it catch a routing error that the previous structure would have allowed through?
- Did the Proof Required field cause Outcome sections to become more uniform and rigorous, or did agents continue producing free-form Outcome sections with the field as decoration?
- Did the Routing Examples section change drafting behavior measurably (faster routing decisions, fewer hallucinated routings, fewer ambiguous picks)?
- Has any importer branch surfaced enough cross-expert friction to justify filling Importer Engineer, or did the existing Data + Flask + Test routing absorb importer work cleanly?
- Did any pairing produce scope creep that the current Out of Scope language failed to prevent?
- Has Docs/Canon Steward been used outside of audit-20 itself? If it is used only for audits, the role is closer to "audit gatekeeper" than "doctrine integrity expert," and the Lens needs a rewrite.
- Did Senior Engineer remain the dominant Section B stance? If so, did any branch arrive that *should* have used a non-default stance but defaulted? Underfiring is harder to detect than overfiring; audit-20 must look for it explicitly.

---

## 7. Drift Watch

Track these between Phase 5 and audit-20. Each becomes an agenda item for audit-20.

- **Lifecycle violations.** New experts added to Section A without three-real-branches evidence of cross-expert friction. Pass-2 retracted its own lifecycle rules from pass-1, but the spirit (do not add experts pre-emptively) must hold. Watch especially for Release/Ops Engineer or any new "X Steward" addition that lacks empirical pain.
- **Senior Engineer reflex.** Branches that name Senior Engineer as the stance when a non-default stance should have applied. Specific watch: any UI/CSS branch that does not name Lead Product Designer; any nav or flow branch that does not name UX Strategist; any public-copy branch that does not name Brand Guardian or Community-Voice Writer.
- **Observation-section attrition.** The "Observations" section in reports 01, 02, 04 was where the strongest signal lived (the Verified Fact refutation, the canonical-shape promotion candidate, the report-03 numbering note). If future reports trim Observations to formalities, the feedback loop weakens. Audit-20 should compare Observation density across reports.
- **`ops/learned/` updated by audit branches.** Phase 5 explicitly forbids this; the rule must hold at audit-20 and audit-40. Audits identify candidate patterns; implementation branches that follow audits produce them.
- **Numbering gap proliferation.** The report-03 gap is documented in this audit and in the session note. Future gaps must be similarly documented. Recommended mitigation if a second gap appears: each report adds a one-line "Previous routed report: report-NN.md" header, making gaps visible without requiring `ls` archaeology. Do not implement this preemptively; only if a second gap actually appears.
- **Pass-1-as-live-recommendation drift.** Future agenda files (chatgpt-14, chatgpt-15) that follow the pass-1/pass-2 review pattern must keep the pass-1 fossil-record header that `chatgpt-13-pass2.md` carries. Citing pass-1 conclusions as live recommendations after pass-2 exists is a fossil-record discipline failure.
- **Template H bloat.** Pass-2 explicitly warns "do not bloat Template H." Any future doctrine PR that adds more than the Routing Justification block to Template H needs strong justification. Watch for sections being added because they "feel useful" without naming a specific failure mode they prevent.

---

End of Phase 5 audit. The next routing-system audit is `ops/phase-5/audit-20.md` (or whatever path Docs/Canon Steward decides at fill time), produced after report-20 lands.
