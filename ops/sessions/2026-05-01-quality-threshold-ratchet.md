## May 1, 2026 — Quality Engine Layer 2 (threshold check + ratchet)

**Branch:** feat/quality-threshold-ratchet
**PR:** (pending)

**What:** Extended the SoulPrint quality toolchain from report-only into threshold enforcement. New module `src/quality/thresholds.py` carries the policy layer (load, save, evaluate, ratchet); `src/quality/cli.py` gains `--check`, `--ratchet`, and `--thresholds` flags as a mutually-exclusive group with the existing `--json`. New `quality-thresholds.json` at repo root holds the initial policy. New `tests/test_quality_thresholds.py` covers all four policy operations with synthetic ScoreResult inputs (no recursive `coverage run -m pytest`).

**Decisions:**
- Created a new focused module `src/quality/thresholds.py` rather than inlining policy in `cli.py`. The CLI now orchestrates two pure layers (scorer + thresholds); both are unit-testable without subprocess.
- `Thresholds` defaults are permissive (`max_crap=inf`, `max_complexity=1e9`, `min_coverage_percent=0.0`). Missing fields in a partial config evaluate as "not enforced" rather than "strict zero" so a hand-edited file cannot silently block CI.
- Initial `quality-thresholds.json` calibrated against the 2026-04-29 report: max_crap=550.0 (worst measured 510.02), max_complexity=70 (worst measured 64), min_coverage_percent=0.0 (multiple top-20 functions at 0%), top_n=20. The repo passes immediately after this branch lands.
- Ratchet logic is two `min`s and one `max` over current vs measured. If `current` is stricter than `measured` for any field (typical when CI is failing), that field is preserved. Element-wise monotonic strictness: `compute_ratchet` cannot produce a Thresholds that is looser in any dimension than the input.
- `--check`, `--ratchet`, and `--json` are an argparse mutually exclusive group, not three independent flags. Argparse rejects `--json --check` at parse time, eliminating a class of runtime ambiguity.
- `--check` writes no report files. Default behavior (write timestamped reports) is unchanged. CI can run `--check` cleanly without producing artifacts; humans run the default for diagnosis.
- `compute_ratchet` and `evaluate` defensively re-sort results by CRAP descending. `score_tree` already sorts, but the policy layer must not assume pre-sorted input — that decoupling lets tests use arbitrary-order synthetic ScoreResults (see `test_evaluate_does_not_assume_pre_sorted_input`).
- Ratchet refuses to bootstrap. Missing thresholds file → `--ratchet` errors with "create one first." The branch creates the initial file; future repos copy it. Bootstrap-from-empty is deferred until empirical demand.

**Pattern observation:**
- The decoupling between `scorer.py` (pure data → ranked list) and `thresholds.py` (policy verdict over ranked list) lets the CLI compose them without either layer knowing about the other. Future Layer 3 additions (per-module budgets, mutation scores) can plug in as additional policy modules consuming the same `ScoreResult` shape, without touching the scorer or the CLI orchestration. No new pattern entry to `ops/learned/` is warranted yet — the pattern is "two-layer policy/data split", which is generic and not yet validated by a second instance in this codebase.
- Mutually-exclusive-group pattern: argparse can encode "exactly one of these three modes" structurally, replacing runtime branch-checking. Worth noting if a future CLI gains a third or fourth mode, but again not yet a learned pattern requiring promotion.

**Tests:** 1152 → 1174 passing (+22, exactly matching the new test file). 1 skipped (the pre-existing Windows symlink test). Full suite runtime ~79s; no regressions.

**Verification:**
- 22 new tests across 6 unittest.TestCase classes in `tests/test_quality_thresholds.py` cover: defaults are permissive; load with full config / partial / unknown fields / missing file; save round-trip and schema marker; evaluate pass / fail per dimension / multiple violations per function / top_n bound / top_n=0 vacuous pass / not-pre-sorted; ratchet tighten / refuse-to-loosen / no-op-at-limit / partial-tighten / empty results / top_n bound; load+ratchet+save+load round trip.
- End-to-end manual check against the actual top-5 from `ops/quality/report-2026-04-29.md`: `evaluate` returns PASS under the initial policy; `compute_ratchet` would tighten max_crap 550.0 → 510.02 and max_complexity 70 → 64. The numbers prove the policy is calibrated correctly.
- Argparse surface: bare invocation, single mode, and `--thresholds <path> --check` all parse correctly; `--json --check` rejected at parse time as expected.
- Did NOT exercise the full `--check` CLI through `_run_coverage` because the existing toolchain doctrine forbids recursive `coverage run -m pytest` inside the test suite. The pipeline pieces are tested independently; their composition is verified manually with the simulated top-5.

**Next:**
- Open PR for `feat/quality-threshold-ratchet`.
- After merge, the threshold policy is in main and `--check` is available locally. CI wiring (a required pre-merge gate) is intentionally out of scope for this branch and is the next queue item if the team wants enforcement.
- Recommended first ratchet: run `soulprint-quality --ratchet` after this branch lands to lock the policy at the actual measured values (510.02 / 64 / 0.0). That conversion of "passing" into "tight" is the discipline the ratchet exists to enforce.
