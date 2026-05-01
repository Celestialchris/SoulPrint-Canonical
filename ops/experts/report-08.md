# Expert Report 08: feat/quality-threshold-ratchet

Date: 2026-05-01
Branch: feat/quality-threshold-ratchet
PR: (pending)
Template H prompt: inline (Uncle Bob Quality Engine Layer 2: Quality Threshold Ratchet)

## Routing

Section A expert: Code Quality Engineer
Section B stance: Senior Engineer

## Reads consumed during drafting

- `context/experts.md` (project canon, read-to-verify): confirmed the Code Quality Engineer stanza still owns the quality toolchain, that the `**Proof required.**` field added in report-07 applies to this branch, and that the Importer Engineer placeholder is unchanged.
- `context/template-h.md` (project canon, read-to-verify): confirmed the Routing Justification subsection (PR #200) and the Proof Required field (PR #201) both remain part of the routed-prompt contract.
- `.claude/rules/python-patterns.md` (project canon): `from __future__ import annotations`, `@dataclass(frozen=True, slots=True)`, no async, errors at the edge. The `Thresholds`, `Violation`, `Verdict` dataclasses are written in this style.
- `.claude/rules/soulprint-testing.md` (project canon): `unittest.TestCase` under pytest, `make_test_temp_dir` for any filesystem use, no recursive `coverage run -m pytest`. `tests/test_quality_thresholds.py` mirrors `tests/test_quality_scorer.py` exactly in style.
- `ops/experts/report-01.md` (pattern-mirror): the prior quality-toolchain report; format reference for this report. Confirmed the prior branch landed as PR #192 and that the `Coming next` section in the Layer 1 README pointed forward to `feat/quality-threshold-ratchet`, which this branch fulfills.
- `ops/experts/report-07.md` (pattern-mirror): most recent routed report; format reference for the Observations and Reads sections.

## Reads consumed during execution by Claude Code

- `src/quality/README.md` (read, edited): updated CLI block with three new modes; replaced `Coming next` to reflect Layer 2 shipping; added a full "Threshold policy" section with schema, check semantics, ratchet semantics.
- `src/quality/scorer.py` (read only): confirmed `ScoreResult` dataclass fields (file, function, complexity, coverage_pct, crap) are sufficient for the threshold layer without any modification to the CRAP formula.
- `src/quality/cli.py` (read, edited): added `--check`, `--ratchet`, `--thresholds` flags as a mutually-exclusive group with `--json`; added `_format_check_summary`, `_format_ratchet_diff`, `_run_check`, `_run_ratchet` helpers; dispatched the new modes from `main()` before the default report-write path.
- `tests/test_quality_scorer.py` (read only): pattern reference for unittest.TestCase style; confirmed I should not touch this file.
- `pyproject.toml` (read only): confirmed `coverage>=7.0` and `radon>=6.0` are already in `[project.optional-dependencies].dev`; no new dependency required for this branch.
- `.gitignore` (read only): confirmed `quality-thresholds.json` is NOT in the ignore list and will be tracked when added.
- `ops/quality/report-2026-04-29.md` (read only): used the actual top-20 to calibrate the initial threshold values so the repo passes immediately after merge.
- `src/quality/thresholds.py` (created): policy layer with `Thresholds`, `Violation`, `Verdict` dataclasses and `load_thresholds`, `save_thresholds`, `evaluate`, `compute_ratchet` functions.
- `quality-thresholds.json` (created, repo root): initial policy `{max_crap: 550.0, max_complexity: 70, min_coverage_percent: 0.0, top_n: 20}`.
- `tests/test_quality_thresholds.py` (created): 22 tests across 6 unittest.TestCase classes.
- `ops/sessions/2026-05-01-quality-threshold-ratchet.md` (created): branch session log.
- `ops/experts/report-08.md` (this file).

## Outcome

- Tests: 1152 → 1174 passing (+22, exactly matching the new test file). 1 pre-existing skip (Windows symlink). Full suite runtime ~79s.
- New deps: none. `coverage>=7.0` and `radon>=6.0` were added in PR #192; this branch consumes them and adds no further.
- Behavior change: the existing `soulprint-quality` console script gains three orthogonal modes — `--check` (evaluate against `quality-thresholds.json`, exit 1 on violation), `--ratchet` (tighten the policy in place, never loosen), and the new `--thresholds` flag for path override. Default report-writing behavior is unchanged. A new repo-root `quality-thresholds.json` carries the initial policy, calibrated so `--check` passes against the current `main` measurement (worst CRAP 510.02, worst complexity 64).

## Proof required (Code Quality Engineer)

Per the `**Proof required.**` field added to `context/experts.md` in PR #201:

- **Test count delta is exact and attributable.** 1152 → 1174 is +22, matching exactly the new test file. No other test files added, removed, or skipped. The arithmetic is the proof: anything else changing would have shifted the delta.
- **Existing scoring formula unchanged.** `src/quality/scorer.py` was not edited. `compute_crap`, `derive_function_coverage`, `score_tree`, and the `ScoreResult` dataclass are byte-identical to PR #192. The threshold layer consumes the scorer's output without modifying it.
- **Initial policy calibrated against measured reality.** Initial thresholds (550 / 70 / 0.0 / 20) are above the worst measured values from `report-2026-04-29.md` (510.02 / 64 / 0.0). `--check` PASSES on `main` immediately after merge; `--ratchet` would tighten 550→510.02 and 70→64. Both verified against simulated top-5 measurements taken from the existing report.
- **Ratchet monotonicity is verified.** `test_refuses_to_loosen_when_measured_is_worse` exercises the path where the current policy is stricter than measurement (the "CI is failing" case): `compute_ratchet` keeps the strict value rather than raising it to match the regression. `test_no_op_when_already_at_limit` verifies the at-limit case. The two together cover the full monotonicity contract.
- **No recursive `coverage run -m pytest`.** All threshold-layer tests use synthetic `ScoreResult` instances directly; none invoke the CLI's coverage subprocess. The documented stop condition for the quality toolchain is preserved.

## Observations

This branch composed cleanly with the two prior doctrine pressure points (Routing Justification from PR #200 and Proof Required from PR #201). Both were satisfied without friction: the prompt's ROUTING block named Code Quality Engineer with "why this expert" and "why not adjacent experts" reasoning, and this report's Outcome section had a structural target (the five Proof bullets above) rather than freeform proof shape. The Phase 5 thesis that doctrine pressure points compose mechanically is holding empirically: report-07 satisfied PR #200's deliverable downstream, and this report satisfies PR #201's deliverable downstream of both. Two routed branches in a row have inherited the rigor without it costing extra effort at draft time.

The 2-layer split (`scorer.py` is data; `thresholds.py` is policy) is the first time the quality toolchain has had distinct horizontal layers. The original PR #192 was monolithic-by-necessity (there was nothing to compose with). The split is what unlocks Layer 3 candidates — per-module budgets, mutation scoring, custom dimensions — to plug in alongside `thresholds.py` without rewriting the scorer or the CLI orchestration. The pattern is generic enough that I considered promoting it to `ops/learned/`, but it is not yet validated by a second instance in this codebase, so per the `ops/learned/` discipline (no new entry without empirical pain or a second instance) it stays as an Observation here. If a future Layer 3 module is added and the same split survives, that becomes the second instance and the entry is justified.

The mutually-exclusive-group argparse pattern is a smaller observation: it converts "exactly one of N modes" from a runtime check into a parse-time error. The cli.py diff is only ~30 lines for the new modes precisely because argparse handles the modal logic structurally. If a fourth mode is ever added (e.g. `--baseline` for the per-function v2 schema), the same group accepts it without restructuring. This is also not yet a learned pattern by my single-instance bar.

The initial threshold values were chosen by hand from the 2026-04-29 report, not by running `--ratchet` to derive them. This is intentional for the bootstrap branch: the values are round-number caps with measurable headroom (550 vs 510.02, 70 vs 64) so the policy is human-legible and tolerates small noise. The natural follow-up is to run `--ratchet` once after merge, which will lock the policy at the exact measured values and convert "the repo passes loosely" into "the repo passes tightly". I did not perform that ratchet in-branch because the prompt's Step 3 says "Add `quality-thresholds.json` at repo root with an initial passing threshold based on the current report scale" — round-number initial values, then the user runs `--ratchet` post-merge to tighten. Doing both in one branch would conflate "create policy" with "tighten policy" and obscure what the ratchet actually does.

The bootstrap-from-empty case (running `--ratchet` against a missing thresholds file) is intentionally not implemented. It would be a small addition, but it would make `--ratchet` mutate-or-create rather than tighten-only, which weakens the monotonicity contract conceptually. If empirical demand arises (someone copies the toolchain to a new repo with no policy yet), the right answer is a separate `--init` mode rather than overloading `--ratchet`. For now the user creates the file by hand, exactly as this branch did.

CI wiring is also intentionally out of scope. The prompt's stop conditions explicitly call out "The branch appears to require CI wiring." as a stop trigger. The check gate is opt-in until the team chooses to wire it; this branch ships the gate, not the wiring. The `Coming next` section of the README documents CI wiring as the next queue item.

No reusable pattern is promoted to `ops/learned/` on this branch. The two candidate patterns noted above (two-layer policy/data split, mutually-exclusive-group argparse modes) are single-instance and not yet validated by a second occurrence. The `ops/learned/` discipline introduced by the Phase 5 audit (Section 7) is preserved.
