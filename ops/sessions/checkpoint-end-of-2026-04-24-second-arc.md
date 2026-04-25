# Checkpoint — end of 2026-04-24 (second arc)

Compact rollup. The first checkpoint of the day captured Observable Archive v0 close (PRs #153–#156). This one covers the four PRs that shipped after, plus the Phase 1 observation it was waiting on.

Read `session-handoff-end-of-2026-04-24-second-arc.md` for full narrative and calibration notes.

---

## Shipped this arc (in ship order)

Four PRs. One real fix surfaced by Phase 1 observation, one provider-coverage gap, one docs hygiene pass, one feature audit that turned into a UX normalization, plus one trivial cleanup followup.

- [x] **PR #158** — `chore/archived-tabs-five-providers` — `/imported/archived` tab row gained Claude Code and Grok. Was missed in PR #145's centralization pass. Template-only; tabs use `provider_display_name` filter, not hardcoded strings. CSS classes use hyphens (`provider-tab--claude-code`); query params use underscores (`?provider=claude_code`). `+5 tests → 1040.`

- [x] **PR #159** — `chore/readme-roadmap-hygiene` — Docs-only truth pass.
  - **README:** four provider-mention locations updated to all five providers in canonical order. Tagline, "What it does" Import bullet, "Why this exists" opening, Providers table. Claude Code row was missing from the Providers table entirely.
  - **ROADMAP:** "Current Milestone / Phase 11 — Soft launch" replaced with a "Parked" section. Launch pressure removed per 2026-04-23 context. Observable Archive v0 added to Completed.
  - No code, no tests. Suite stayed at 1040.

- [x] **PR #160** — `feat/copy-ux-normalization` (CP4 audit) — Pre-flight discovery changed CP4's premise: two of three target surfaces already had copy infrastructure. Reframed from "build Continue-in-X from scratch" to "normalize existing copy UX."
  - `/continuity/<id>` gained a 2-second "Copied ✓" confirm matching `/digest/result`.
  - `/imported/<id>/explorer` gained a Copy transcript button reading `#transcriptPane.innerText` directly. No backend serialization invented.
  - `/digest/result` untouched (it already had the right UX).
  - One shared `.copy-confirm` class added (CC's design improvement over the prompt's per-surface namespacing).
  - "Continue in ChatGPT" / "Continue in Claude" labeling parked under launch polish.
  - `+2 tests → 1042.`

- [x] **PR #161** — `chore/explorer-copy-btn-class-promotion` — In-branch deviation from #160: the explorer Copy button shipped with seven inline style declarations. Promoted to a `.page-action-copy` CSS class. Reformatted `.copy-confirm` from single-line to multi-line block matching house style. No behavior or visual change. `1042 passing` (no test changes).

## State

- **Branch:** main (all four PRs merged)
- **Tests:** 1042 passing
- **Version:** v0.7.0-alpha.2 (no bumps this arc)
- **Observable Archive v0:** complete and merged (since first arc earlier today)
- **CP4 audit:** complete, with launch-polish labeling parked

---

## Phase 1 observation results

Three-question pass logged from the running app:

1. **Tags sufficient as organizational primitive?** Yes, fine. Starred conversations landing in `/chats` under notes covers the gap tags don't fill.
2. **Chip/action-row mismatch on `/imported` looks wrong?** No, not visually bothering. Row-action CSS promotion parks indefinitely.
3. **Starring still feels destination-less?** No. PR #152 closed it (starred imports render at `/chats`).

**Surface findings beyond the three questions** (these drove the second arc's PRs):

- `/imported/archived` showed only 3 of 5 provider tabs → fixed in #158.
- `/archive/health` showed "Never imported" for all 5 providers despite 1526 conversations in the archive (`ImportRun` only tracks post-#154 imports) → was originally Prompt 1 in the second-arc plan, but ended up consolidated into the work that shipped.
- README / ROADMAP truth gaps → fixed in #159.
- `/distill` route name vs "Create a digest" label mismatch → deferred. Renaming touches too many call sites for the value; reconsider with a redirect instead.

---

## What exists now that didn't before

- `/imported/archived` shows all five provider tabs in canonical `SUPPORTED_IMPORT_PROVIDERS` order.
- README accurately lists five providers in every mention location, including Claude Code in the Providers table.
- ROADMAP frames launch work as Parked, not Current Milestone.
- `/continuity/<id>` and `/imported/<id>/explorer` both have copy buttons with 2-second "Copied ✓" confirm.
- Shared `.copy-confirm` CSS class for confirm-state styling across handoff surfaces.
- `.page-action-copy` CSS class for ghost-style buttons in `page_actions` blocks.
- `context/template-h.md` (Context Layer Edition) is settled: no version suffix, no v2/v2.1 references. Memory updated to reflect this.

---

## Calibration notes from this arc

Five practices that held; one bias that needs correcting.

**Held:**

1. **Pre-flight against the zip before drafting.** Resolved the `verify_archive()` shape, the `provider-tab--<slug>` hyphen convention, the existing copy infrastructure on digest and continuity, and the explorer `#transcriptPane.innerText` viability — all before any prompt was written. Saved at least one round-trip per PR.

2. **Discovery-first when scope is uncertain.** CP4's preflight surfaced that the original scope ("build Continue-in-X from scratch") was wrong: two surfaces already had what was being asked for. Reframing to "audit / normalize" before drafting prevented a half-day PR built on a wrong premise.

3. **Pre-draft design decisions in chat, before the .md.** Caught the shared-CSS-class question on Prompt 5 (which CC then cleanly overrode with a better answer), the route-rename scope question on Prompt 3 (which led to deferring it), and the tabs-source question on Prompt 2.

4. **Surgical diffs on review edits.** Prompt 1 went through three edit rounds without ever re-pasting the whole prompt body. Each round was a labeled list of replacements.

5. **Read-to-verify tagging.** Once Template H locked in the tag, prompts that referenced shapes from prior PRs in the same milestone (PRs next-1, next-2, #145) auto-named the read-to-verify file. Caught no actual drift this session, but the discipline is forming.

**Bias to correct:**

When a PR review surfaces a deviation that is genuinely cheap to fix in-branch and the fix is *already known* (translation work, not design work), the default is **block-and-fix in-branch, not merge-and-followup**. Inline-styles-to-class on PR #160 met that bar and I framed merge-as-is as defensible. It wasn't. The followup PR #161 was avoidable. Logged for next time: if the fix is mechanical and small, push for in-branch.

---

## Next-session parked menu

Aggregate Open Loops is the next real feature; everything else is doc hygiene or trigger-gated.

**Near-term candidates:**

- [ ] **Aggregate Open Loops.** `/continuity/open-loops` command center pulling from existing continuity surfaces. No new data model, no schema change. Frontend + one new route. Medium scope, shippable in a session.
- [ ] **First-run wizard.** Guided onboarding: provider pick → import → stats → search. Skip until onboarding is reported as a friction point.
- [ ] **Tag/query composition.** `tag:X provider:Y` FTS prefix tokens. Gated behind CP3/P5 per spec.

**Doc / housekeeping:**

- [ ] **Workspace screenshot refresh.** `docs/screenshots/workspace.png` in README likely predates the health badge in the right panel. Small standalone PR.
- [ ] **CSS one-liner audit.** Prompt 6 surfaced one stylistic inconsistency (`.copy-confirm` shipped as one line). Unknown if others lurk. Cheap to scan, unknown remediation scope.

**Trigger-gated:**

- [ ] **Landing refresh.** Parked until a launch window is on the calendar. Handoff at `docs/product/landing-refresh-handoff.md`.
- [ ] **Continue-in-ChatGPT / Continue-in-Claude relabeling.** Worth doing for Reddit-demo narrative when launch is real. Cosmetic until then.

**Frozen per `DECISIONS.md` (do not re-propose):**

- Cloud-first rewrites, vector DBs, semantic memory replacements, mem0 activation.
- Normalized tag table.
- Cross-user shared taxonomies, semantic tag clustering.
- `/distill` → `/digest` route rename without a redirect.
