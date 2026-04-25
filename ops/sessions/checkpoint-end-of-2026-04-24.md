# Checkpoint — end of 2026-04-24

Compact rollup. Read `session-handoff-end-of-2026-04-24.md` for full narrative and calibration notes.

---

## Shipped today (in ship order)

Eight PRs, two arcs. Morning: four housekeeping PRs tightening labels, provider lists, test anchors, and star destinations. Afternoon through evening: Observable Archive v0 in four PRs, delivering a reliable health check, durable import history, a read-only health page, and a Workspace glance badge.

- [x] **PR 0** — `chore/claude-md-provider-list` — CLAUDE.md provider list corrected to five providers matching `SUPPORTED_IMPORT_PROVIDERS`.
- [x] **PR 1 / #149** — `chore/sidebar-language-alignment` — Five sidebar labels aligned with page headers; Grok added to Import page_desc.
- [x] **PR 1b** — `chore/tighten-sidebar-test-anchors` — Three weak `assertIn` strings replaced with page-unique anchors after Codex review on #149.
- [x] **PR 2 / #152** — `feat/chats-starred-imports` — "Your own notes" (`/chats`) now renders starred imports below notes list; starring an import has a destination.
- [x] **PR next-1 / #153** — `feat/soulprint-verify-cli` — New `src/verify.py` with `verify_archive(db_path)` returning a five-check structured dict + counts. `soulprint verify` subcommand mirrors `_cmd_info`. Exit codes 0/1/2 distinguish healthy / check failed / DB missing. *(Observable Archive v0, 1/4)*
- [x] **PR next-2 / #154** — `feat/import-run-table` — ImportRun model + outer try/finally wire-ins at `/import` and `/imported/scan-claude-code`. Four statuses: `success` / `duplicate_only` / `partial` / `failed`. Recent imports table on `/import`. `+27 tests → 1014.` *(2/4)*
- [x] **PR next-3 / #155** — `feat/archive-health-page` — `/archive/health` read-only route rendering full verify output + last-import-per-provider for all five providers. New `last_import_run_per_provider()` helper using plain ordered query + Python grouping. `app.css` untouched. `+10 tests → 1024.` *(3/4)*
- [x] **PR next-4 / #156** — `feat/workspace-health-badge` — `quick_health_summary()` appended to `src/verify.py`, skips integrity and orphan checks. Badge at top of Workspace right panel above Archive status. Three states link to `/archive/health`. Codex follow-up added `try/except sqlite3.DatabaseError` guard against corrupt DB files. Scoped `app.css` append, ~25 lines, no token changes. `+9 tests → 1033.` *(4/4, milestone complete)*

## State

- **Branch:** main (PR #156 pending merge at checkpoint write)
- **Tests:** 1033 passing
- **Version:** v0.7.0-alpha.2 (no bumps this session)
- **Observable Archive v0:** complete pending #156 merge

---

## What exists now that didn't before

- `src/verify.py` — two functions (`verify_archive`, `quick_health_summary`) shared by CLI, page, and badge.
- `src/app/import_runs.py` — four public functions: `classify_import_outcome`, `record_import_run`, `latest_import_runs`, `last_import_run_per_provider`.
- `ImportRun` model — appended to `src/app/models/__init__.py`; created via `db.create_all()`, no migration.
- `/archive/health` route — first entry under `/archive/*` namespace; singular by design.
- `Archive health` sidebar entry — Sanctum group, third item after Workspace and Ask.
- Workspace health badge — top of right panel, three states (`healthy` / `needs_attention` / `unknown`), all linking to `/archive/health`.
- `soulprint verify` CLI subcommand — human + `--json` output, exit codes 0/1/2.
- `context/template-h.md` — v2.1 with five additions (purpose-tagged Mandatory Reads, structural anchors, template-helper exposure verification, pre-draft design decisions, milestone-internal calibration). File is at `/mnt/user-data/outputs/template-h.md` if not yet dropped into repo.

---

## Next-session parked menu

Not prescriptive. Pick based on appetite and what the first Phase 1 observation surfaces.

**Near-term candidates (each as its own Template H v2 campaign):**

- [ ] Phase 1 observation pass — three questions in `session-phase-plan-2026-04-23.md` Phase 1, previously blocked on "launch is imminent" pressure that's now lifted. 15 minutes of actually using the app with tags + stars + Observable Archive v0 surfaces.
- [ ] CP4 Continue-in-X — Copy-for-ChatGPT / Copy-for-Claude / Copy bridge packet buttons on explorer, distill, continuity surfaces.
- [ ] First-run wizard — guided onboarding: provider selection → import → stats → search.
- [ ] Aggregate Open Loops — `/continuity/open-loops` command center.
- [ ] Tag/query composition — `tag:X provider:Y` FTS prefix tokens.
- [ ] Landing refresh — trigger-gated; parked until a launch window is on the calendar. Handoff at `docs/product/landing-refresh-handoff.md`.

**Doc hygiene (small, standalone, can be bundled):**

- [ ] ROADMAP.md cleanup — retire Phase 11 "soft launch" framing.
- [ ] README text — "release v0.6.0" badge and "ChatGPT, Claude, and Gemini" tagline predate Claude Code + Grok importers.

**Frozen per DECISIONS.md (do not re-propose):**

- Cloud-first rewrites, vector DBs, semantic memory replacements, mem0 activation.
- Normalized tag table (tagging-spec v2 §4).
- Cross-user shared taxonomies, semantic tag clustering.

---

## Upstream

- [ ] rtk pytest no-args bug — filed at rtk repo #1417, triaged upstream, "good first issue" labeled. Not SoulPrint's problem.
