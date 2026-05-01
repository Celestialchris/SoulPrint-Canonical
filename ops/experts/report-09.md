# Expert Report 09: feat/quality-ci-reporting

Date: 2026-05-02
Branch: feat/quality-ci-reporting
PR: (pending)
Template H prompt: inline (Uncle Bob Quality Engine Layer 3: Quality CI Reporting)

## Routing

Section A expert: Code Quality Engineer
Section B stance: Senior Engineer

## Reads consumed during drafting

- `src/quality/README.md` (pattern-mirror, edited): confirmed "CI wiring is NOT part of this branch" language from Layer 2 that needed removal; confirmed "Coming next" CI bullet that needed promotion; confirmed the check mode and ratchet mode sections that needed cross-referencing.
- `src/quality/cli.py` (read-to-verify): confirmed `--check` returns from `_run_check` before the default report-write path. The modes are structurally mutually exclusive at the argparse level and at the dispatch level in `main()`. Confirmed the two-pass CI strategy is necessary without touching cli.py.
- `src/quality/thresholds.py` (read-to-verify): confirmed `evaluate` and `load_thresholds` behavior; no changes required.
- `quality-thresholds.json` (read-to-verify): ratcheted values confirmed as `max_crap: 510.02`, `max_complexity: 64`, `min_coverage_percent: 0.0`, `top_n: 20`. These are the values CI will check against.
- `pyproject.toml` (read-to-verify): `soulprint-quality` console script confirmed registered; `.[dev]` confirmed includes `radon>=6.0` and `coverage>=7.0`. No dependency changes required.
- `.github/workflows/tests.yml` (pattern-mirror, edited): confirmed install pattern (`pip install -e ".[dev]"`), Python version (3.12), and existing job structure. Confirmed the quality job can mirror the install step exactly.
- `.github/workflows/claude-code-review.yml` (read-to-verify only): confirmed the bot-gating pattern (`if: github.event.pull_request.user.type != 'Bot'`) and that this workflow must not be touched.
- `ops/experts/report-08.md` (pattern-mirror): format reference for this report; confirmed Layer 2 state: `feat/quality-threshold-ratchet` merged as PR #204, initial thresholds set, ratchet run post-merge to tighten to actual measured values.
- `ops/sessions/2026-05-01-quality-threshold-ratchet.md` (read-to-verify): confirmed Layer 2 closeout state and "Next" section which explicitly named CI wiring as the next queue item.

## Reads consumed during execution by Claude Code

- All mandatory reads above.
- `ops/experts/` glob (read-only): confirmed next available report number is 09 (report-08.md is the most recent; report-03.md is absent, confirming non-sequential numbering in the series).
- `ops/sessions/` glob (read-only): confirmed naming convention for session logs.

## Outcome

- Tests: unchanged. No Python code modified; 1174 passing tests remain at 1174.
- New deps: none.
- Files changed:
  - `.github/workflows/tests.yml` (edited): added `quality` job with 5 steps.
  - `src/quality/README.md` (edited): updated Check mode section, added CI section, updated Coming next.
  - `ops/sessions/2026-05-02-quality-ci-reporting.md` (created): session log.
  - `ops/experts/report-09.md` (this file).

## Proof required (Code Quality Engineer)

Per the `**Proof required.**` field in `context/experts.md`:

- **No Python code changed.** The diff touches only `.github/workflows/tests.yml` and `src/quality/README.md`. The quality scorer, threshold layer, and CLI are byte-identical to their post-PR-#204 state. No test count delta is possible or expected.
- **CI gate uses the correct invocation.** `soulprint-quality --check` is the registered console script from `pyproject.toml` and is available after `pip install -e ".[dev]"`. The step exits non-zero if any function in the top-20 exceeds `max_crap: 510.02` or `max_complexity: 64`. This is the exact gate the Layer 2 README described as "Coming next."
- **Ratchet cannot run in CI.** The workflow contains `soulprint-quality` (default, report mode) and `soulprint-quality --check` (gate mode). Neither is `--ratchet`. CI verifies policy only.
- **Existing test job unchanged.** The `test` job matrix (ubuntu, macos, windows; Python 3.12; `pytest tests/ -v`) is structurally identical before and after this change. The quality job is additive.
- **Artifact upload does not commit generated files.** `actions/upload-artifact@v4` uploads to GitHub's artifact store, not to the git working tree. The `ops/quality/` directory is not staged or committed.

## Observations

The two-pass cost (running `coverage run -m pytest` twice in the quality job) is a direct consequence of the Layer 2 CLI design decision to make `--check` and the default report mode mutually exclusive. This was the right call for Layer 2: the two modes have different semantics and different exit code contracts, so conflating them would have produced ambiguous exit codes and made the gate less trustworthy. The cost at Layer 3 is paying for that clarity. If the two-pass overhead becomes a real bottleneck (measured CI slowdown), the right fix is a `--write-and-check` combined mode in cli.py, not restructuring the CI job.

The `if: always()` pattern on the artifact upload is worth noting. In GitHub Actions, a failing step prevents subsequent steps from running unless they carry an explicit condition. Using `if: always()` on the upload means the report is downloadable even when the threshold check fails — which is exactly the scenario where it is most valuable. The alternative (upload only on success) would make the artifact invisible in the failure case, defeating the purpose of "visible pressure."

No `needs` dependency between the `test` and `quality` jobs is also a deliberate choice. The quality job will fail on its own if the test suite is broken (its internal `coverage run -m pytest` subprocess exits non-zero). A `needs: [test]` dependency would serialize the jobs without adding correctness. Sequential CI is slower CI; the quality check does not need the main test matrix to pass first.

No reusable pattern is promoted to `ops/learned/` on this branch. The CI job pattern is project-specific (it depends on the console script name and the `.[dev]` extras). The `if: always()` on artifact uploads is general enough to be a learned pattern, but it is a single instance with no prior occurrence to validate against. The `ops/learned/` bar (two instances or empirical pain) is not met.
