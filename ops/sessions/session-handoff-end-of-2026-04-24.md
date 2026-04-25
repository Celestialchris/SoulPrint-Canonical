# Session Handoff — End of April 24, 2026

Session campaign: **Observable Archive v0** — completed in four PRs.

Read this first. The zip uploaded at the start of this session (974 tests, v0.7.0a2) is stale. Four PRs have shipped since. Main as of session end is at ~1032 tests expected after PR #156 merges.

---

## Shipped this session

In ship order:

- [x] **PR #153 — `soulprint verify` CLI + reusable verify module** (Observable Archive v0, 1/4)
  - New `src/verify.py` with `verify_archive(db_path) -> dict` returning a five-check structure (`db_exists`, `integrity`, `core_tables`, `fts_tables`, `orphans`) + counts.
  - New `soulprint verify` CLI subcommand mirroring `_cmd_info` structurally. Flags: `--db`, `--json`. Exit codes: 0 healthy / 1 check failed / 2 DB missing.
  - Intentional exit-code divergence from `_cmd_info` (which exits 1 for DB missing) — the three-state distinction enables PR next-4's badge mapping.

- [x] **PR #154 — ImportRun table + instrumentation** (Observable Archive v0, 2/4, +27 tests → 1014 total)
  - New `ImportRun` model appended to `src/app/models/__init__.py`; created via `db.create_all()`, no migration.
  - New `src/app/import_runs.py` service module mirroring `src/app/tags.py` shape: `classify_import_outcome` (pure), `record_import_run` (writer), `latest_import_runs` (display helper). Four statuses: `success` / `duplicate_only` / `partial` / `failed`.
  - Both import routes (`/import` and `/imported/scan-claude-code`) wrapped in outer try/finally so exactly one row is written per POST, including pre-importer validation failures and unexpected exceptions (broad `except Exception` + re-raise so unexpected failures still produce audit rows).
  - "Recent imports" table on `/import` below the upload form, plain semantic markup, no new CSS classes.

- [x] **PR #155 — `/archive/health` read-only page** (Observable Archive v0, 3/4, +10 tests → 1024 total)
  - New `archive_health()` route between `home()` and `passport_surface()`.
  - New `src/app/templates/archive_health.html` mirroring `passport.html` idioms. Three sections: verify checks, last-import-per-provider, archive-path footer. All five providers always render, with "Never imported" for zero-history rows. `app.css` untouched.
  - New `last_import_run_per_provider()` in `src/app/import_runs.py`. Plain ordered query + single-pass Python grouping (no `func.max` subquery). Null-provider rows excluded.
  - Sanctum sidebar gained a third entry: Workspace, Ask, Archive health.

- [ ] **PR #156 — Workspace health badge** (Observable Archive v0, 4/4, open at session end)
  - New `quick_health_summary()` in `src/verify.py` — lightweight three-state check (`healthy` / `needs_attention` / `unknown`) skipping integrity check and orphan scan. Badge pays glance-cost, `/archive/health` pays full-truth cost.
  - Badge at top of Workspace `{% block right_panel %}`, above Archive status. Text: "Archive available" / "Needs attention" / "No archive yet". All three states link to `/archive/health`.
  - Scoped CSS block (~25 lines) appended to `app.css` — only PR in this milestone that edits `app.css`. Three BEM state modifiers, all resolving existing tokens (`--green`, `--accent`, `--t3`). Partial-lock enforced: no token changes, no existing rule edits.
  - **Pending:** Codex review finding on #156 (see below). Fix in progress as of session end.

---

## Codex review finding on PR #156 (DatabaseError handling)

GitHub's ChatGPT/Codex connector left an automated review on `src/verify.py` lines 212-214. Summary:

> **[P1] Handle invalid SQLite files in quick health check.** If the configured DB path exists but is not a valid SQLite database (corrupted archive or accidental non-DB file), `conn.execute(...)` raises `sqlite3.DatabaseError` and propagates to `home()`, returning a 500 for `/` instead of showing a badge state. This is a regression from the full verifier path, which guards these query failures; the badge path should similarly catch `DatabaseError` and return a non-healthy state/detail.

**Assessment.** The finding is real. `verify_archive` has a defensive `try/except sqlite3.DatabaseError` around its integrity check (baked into PR next-1's prompt explicitly as belt-and-suspenders). The PR next-4 prompt did not include the equivalent defensive wrap for `quick_health_summary`, and Codex caught it. CC is applying the fix at session end.

**Calibration signal for future prompts.** When a function is added alongside an existing defensive-catch pattern in the same module, the new function should get the same catch unless there's a reason to diverge. The PR next-4 prompt's Verified Facts block named the integrity-check defensive catch from verify_archive but didn't propagate the pattern to `quick_health_summary`'s spec. Worth remembering: if `X_defensive_pattern` is explicit in module M, and new function Y is added to M, default Y to the same pattern.

Expected fix shape: wrap the `sqlite_master` lookup and table-existence queries in `try / except sqlite3.DatabaseError`; on catch, return state `needs_attention` (or `unknown` — CC's judgment, both are defensible) with a `detail` naming the corruption. Do not swallow the exception silently.

---

## Template H v2 updated

`context/template-h.md` has a refreshed version at `/mnt/user-data/outputs/template-h.md` (as of end of session). Drop in when ready — it's additive, no existing structure removed. Five additions earned by this milestone's calibration moments:

1. **Mandatory Reads tagged with purpose.** Each entry marked as *pattern-mirror* (agent reads to imitate) or *read-to-verify* (agent confirms a shape locked by a prior PR before trusting Verified Facts). Emerged from PR next-3's required edit after the stale-zip problem surfaced.

2. **Structural anchors preferred over line numbers.** When prior PRs in the same milestone have shipped, line numbers from the drafter's working copy drift. "Between `home()` and `passport_surface()`" survives a merge; "line 392" doesn't.

3. **Template-helper exposure verification.** Before any helper appears in a Jinja snippet, state whether it's exposed as a filter (pipe syntax), function (call syntax), or global. This caught `format_timestamp` being misused as a filter during next-2.

4. **Drafter authoring practices — pre-draft design decisions.** Formalizes the 2-3 committed-decisions block in chat before drafting the .md file. Names the practice.

5. **Drafter authoring practices — milestone-internal calibration.** "Read PR N-1's session log before drafting PR N; fold corrections into the next prompt as explicit Verified Facts, read-to-verify Mandatory Reads, or stop conditions." How this milestone actually got tighter PR to PR.

Drafter checklist extended with four new items covering these.

---

## Observable Archive v0 — complete (pending #156 merge)

All four checkpoints shipped or open. The milestone provides:

- A reliable health-check primitive (`verify_archive`) consumable from CLI, page, and badge.
- Durable import history (`ImportRun`) with exactly-one-row-per-POST semantics, classified into four outcomes.
- A read-only `/archive/health` page showing full verify output + last-import-per-provider for all five providers.
- A Workspace badge giving glance-signal with a lightweight check, linking to the full page.

The vault is now observable. Re-import blindness is fixed. Trust chain is visible.

---

## Deferred / parked menu (post Observable Archive v0)

Not prescriptive — just what the menu looks like now that v0 is done.

**Near-term candidates** (each would ship as its own campaign with Template H v2 prompts):

- **CP4 Continue-in-X** — Copy-for-ChatGPT / Copy-for-Claude / Copy bridge packet buttons on explorer, distill, continuity surfaces. Emotionally differentiated, demo-ready.
- **First-run wizard** — guided onboarding: provider selection → import → stats → search.
- **Aggregate Open Loops** — `/continuity/open-loops` as command center.
- **Tag/query composition** — `tag:X provider:Y` FTS prefix tokens (spec deferred behind CP3/P5 in tagging-spec v2 §9, but unblocked now that tags have shipped).
- **Landing page refresh** — fully specced in `docs/product/landing-refresh-handoff.md`. Parked until a real launch window is on the calendar. Do not unpark speculatively.

**Doc hygiene (small, standalone):**

- **ROADMAP.md cleanup** — Phase 11 "soft launch" still listed as Current Milestone. Retire it; reframe around the three-shapes taxonomy already present.
- **README text** (not image — image was fixed 2026-04-24) — "release v0.6.0" badge and the "ChatGPT, Claude, and Gemini" tagline both predate Claude Code and Grok importers.

**Frozen (do not re-propose):**

- Cloud-first rewrites, vector DBs, semantic memory replacements, mem0 activation.
- Normalized tag table (tagging-spec v2 §4).
- Cross-user shared taxonomies, semantic tag clustering.

---

## Session rhythm — what worked

Five practices that held up across four PRs in one long session:

1. **One prompt, one branch, one merge, fresh Claude Code session per PR.** Preserved scope lock discipline; no bundling drift.
2. **Pre-draft decisions in chat before the .md.** Gave the human reviewer a cheap checkpoint on design choices before they hardened into prompt text. Caught two design issues before draft (next-3 helper implementation approach, next-4 CSS partial-lock).
3. **Surgical diffs on review edits.** "Replace X with Y" and "insert sentence Z" instead of re-pasting full prompts for two-line changes.
4. **Verified Facts cite a baseline.** "Confirmed against main at PR #154 merge" or similar. Makes stop conditions enforceable.
5. **Read the PR N-1 session log before drafting PR N.** Two real errors (`format_timestamp` as filter, missing render_template count) surfaced in CC output and were folded into the next prompt as explicit Verified Facts. Prompts got tighter over the milestone.

## Session rhythm — what missed

Two patterns worth watching for next milestone:

1. **Defensive-catch propagation between related functions in the same module.** The `quick_health_summary` DatabaseError miss is the example: a defensive pattern was explicit in one function but not required for the new sibling function. Future prompts: when adding a new function to a module with explicit defensive catches, default the new function to the same catches unless divergence is reasoned.
2. **Stale zip + multi-PR milestone.** The session zip was captured at the pre-milestone state. Line-number anchors went stale between next-1 and next-4. Template H v2's structural-anchor guidance fixes this for next time, but only if consistently applied. If a milestone ships more than ~2 PRs, either refresh the zip between prompts or use structural anchors exclusively.

---

## Starting the next session

If resuming on a new task, Chris will likely want:

1. Which campaign next (CP4, first-run wizard, tag composition, something else).
2. Whether to run a Phase 1 observation pass on Observable Archive v0 before committing to a next campaign — see `session-phase-plan-2026-04-23.md` Phase 1 for the three questions that still need honest answers now that the observability infrastructure exists.

If #156 hasn't merged yet when the next session starts, that's task zero — merge or resolve any remaining Codex threads.

Version at session end: `0.7.0a2` (unchanged; no version bumps in this milestone per Chris's one-prompt-one-merge instructions).
