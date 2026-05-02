# Expert Report 11: feat/quality-hardening-loop

Date: 2026-05-02
Branch: feat/quality-hardening-loop
PR: (pending)
Template H prompt: inline (Quality Hardening Loop MVP, first post-mutation-MVP slice)

## Routing

Section A expert: Code Quality Engineer
Section B stance: Senior Engineer

## Reads consumed during drafting

- `context/experts.md` (read-to-verify): confirmed Code Quality Engineer's
  proof-required block names mutation report, survivor counts, and surviving-
  mutation disposition. Confirmed out-of-scope boundary excludes Test Engineer
  (harness architecture) and Security Reviewer (sanitizer shape).
- `context/template-h.md` (pattern-mirror): structure and PR safe-body rules.
- `src/quality/README.md` (read-to-verify): mutation testing section confirms
  `mutmut run --paths-to-mutate src/quality/` is the canonical scoped command;
  CRAP layer documentation referenced for ratchet-pattern parallel.
- `src/quality/scorer.py` (read-to-verify, edited test-side only): pure
  functions `compute_crap`, `derive_function_coverage`, `score_tree`; the
  module is byte-identical post-branch — no production-code edits.
- `src/quality/thresholds.py` (read-to-verify, edited test-side only):
  validation in `Thresholds.__post_init__`, `evaluate` ceiling logic,
  `compute_ratchet` monotonicity. Module byte-identical post-branch.
- `tests/test_quality_scorer.py` (pattern-mirror, edited): existing
  `unittest.TestCase` style and `from src.quality.scorer import (...)` form.
- `tests/test_quality_thresholds.py` (pattern-mirror, edited): existing
  test class structure and `_r` factory pattern.
- `ops/sessions/2026-05-02-mutation-testing-mvp.md` (read-to-verify):
  Layer 4 closeout; "next: establish a baseline survival rate" is the
  motivating bridge to this branch.
- `ops/experts/report-10.md` (pattern-mirror): expert report format.

## Reads consumed during execution by Claude Code

- `pyproject.toml` (read-only): confirmed `mutmut==2.5.1` pin survived to
  branch tip.
- `.mutmut-cache` (read via `mutmut results`): inspected pre-existing cache,
  then re-ran `mutmut run --paths-to-mutate src/quality/` to get a fresh
  baseline against current source.
- `mutmut show 207`, `208`, `210`, `224` (scorer.py survivors): all four
  inspected.
- `mutmut show 244`–`247`, `251`, `259`–`267`, `272`–`276`, `278`–`279`,
  `310`, `318`, `320` (thresholds.py survivors): all 24 inspected.
- `pip install "mutmut==2.5.1"`: required because mutmut wasn't installed in
  the active Python 3.14 environment despite being pinned in dev deps.
  Transitive deps installed: `pony 0.7.19`, `glob2 0.7`, `toml 0.10.2`,
  `junit-xml 1.9`. No new top-level deps added.

## Outcome

- Tests: 50 → 71 passing on the targeted quality suite (21 new tests).
- New deps: none in `pyproject.toml`. The transitive packages noted above
  were resolved at install time from the pre-existing `mutmut==2.5.1` pin.
- Mutation results, scorer.py:
  - Survivors before: 4 (ids 207, 208, 210, 224).
  - Survivors after: 1 (id 210, deferred).
  - Killed: 3 (207, 208, 224).
  - Deferred (equivalent): 1 (id 210, see Observations).
- Mutation results, thresholds.py:
  - Survivors before: 24.
  - Survivors after: 1 (id 310, deferred).
  - Killed: 23 (244, 245, 246, 247, 251, 259, 260, 261, 262, 263, 264, 265,
    266, 267, 272, 273, 274, 275, 276, 278, 279, 318, 320).
  - Deferred (low-value format pin): 1 (id 310).
- Mutation results, cli.py: unchanged at 202 survivors (out of scope).
- Total run: 329 mutants, 230 → 204 survivors. Net new kills: 26.
- Kill rate on the actionable pure-function surface: 26/28 ≈ 93%.
- Behavior change: none. No production code modified. Test suite is stricter.

## Proof required (Code Quality Engineer)

Per `**Proof required.**` in `context/experts.md`:

- **Mutation report path or survivor count before and after.** Recorded above
  per file, with absolute baseline and absolute post-branch numbers.
- **Surviving mutations killed, ignored, or explicitly deferred with
  rationale.**
  - Killed: every survivor in scorer.py except id 210 (equivalent) and every
    survivor in thresholds.py covered by an added or tightened test (see
    breakdown below).
  - Deferred (equivalent): scorer.py id 210. Rationale: `compute_crap(0.0, 0)`
    and `compute_crap(100.0, 0)` both evaluate the formula `0 * 0 *
    (1 - cov/100) ** 3 + 0` to the float `0.0`, indistinguishable from the
    early `return 0.0`. No behavioral test can distinguish original from the
    `complexity < 0` mutant. The guard is kept for readability — its docstring
    explicitly says the branch is for synthetic inputs.
  - Out of scope: 202 survivors in `src/quality/cli.py`. These mutate
    subprocess invocation, argparse setup, JSON-report formatting, and exit
    code paths. Killing them requires either a real-coverage integration suite
    (tooling change, out of scope) or a CLI refactor to extract pure helpers
    (refactor, out of scope per the prompt's scope lock).
- **Tests run and passing counts before and after the branch.** 50 → 71
  passing on the targeted suite. No regressions in the broader suite (was
  already passing under `soulprint-quality --check`).
- **No threshold change.** `quality-thresholds.json` is byte-identical.
- **No CI wiring change.** `.github/workflows/` not touched.
- **Target chosen from a current ranked report, not from taste.** Target was
  the four scorer.py survivor IDs from `mutmut results`, plus the 24
  thresholds.py survivor IDs. Inspection used `mutmut show <id>` on every
  survivor; no test added without a paired surviving mutant.

## Mapping: tests added → survivor IDs killed

scorer.py:
- `ScoreResultContractTest.test_score_result_is_frozen` → kills 207.
- `ScoreResultContractTest.test_score_result_class_defines_slots` → kills 208.
- `DeriveFunctionCoverageTest.test_endline_plus_one_excluded_from_span` →
  kills 224.
- (no test for 210; explicit equivalent-mutant defer.)

thresholds.py:
- `ThresholdSchemaConstantTest.test_schema_marker_is_canonical_string` →
  kills 244, 245.
- `ThresholdsDataclassContractTest.test_thresholds_is_frozen` → kills 246.
- `ThresholdsDataclassContractTest.test_thresholds_class_defines_slots` →
  kills 247.
- `ThresholdsDefaultsTest.test_defaults_are_permissive` (tightened from
  `assertGreater` to `assertEqual`) → kills 251.
- `ThresholdsValidationTest.test_top_n_error_message_is_canonical` →
  kills 259, 260, 261.
- `ThresholdsValidationTest.test_max_crap_at_zero_accepted` → kills 262.
- `ThresholdsValidationTest.test_max_crap_below_one_accepted` → kills 263.
- `ThresholdsValidationTest.test_max_crap_error_message_is_canonical` →
  kills 264.
- `ThresholdsValidationTest.test_max_complexity_at_zero_accepted` →
  kills 265, 266.
- `ThresholdsValidationTest.test_max_complexity_error_message_is_canonical` →
  kills 267.
- `ThresholdsValidationTest.test_min_coverage_just_above_one_hundred_rejected`
  → kills 272.
- `ThresholdsValidationTest.test_min_coverage_error_message_is_canonical` →
  kills 273, 274.
- `ThresholdsDataclassContractTest.test_violation_is_frozen` → kills 275.
- `ThresholdsDataclassContractTest.test_violation_class_defines_slots` →
  kills 276.
- `ThresholdsDataclassContractTest.test_verdict_is_frozen` → kills 278.
- `ThresholdsDataclassContractTest.test_verdict_class_defines_slots` →
  kills 279.
- `EvaluateTest.test_actual_equal_to_max_crap_does_not_violate` → kills 318.
- `EvaluateTest.test_actual_equal_to_max_complexity_does_not_violate` →
  kills 320.
- (no test for 310: `save_thresholds` `indent=2 → 3`. Pinning the JSON
  indent format is brittle to intentional formatting changes; deferred as
  low-value.)

Verified by per-ID `mutmut run <id>`: 23 of 24 thresholds.py survivors killed;
3 of 4 scorer.py survivors killed. Deferred with rationale: scorer.py 210
(equivalent mutant — `complexity=0` returns `0.0` via formula too),
thresholds.py 310 (low-value format pin — JSON `indent=2` is stylistic and a
test for it would fight intentional formatting changes).

## Observations

The most useful pattern this branch surfaced is the **string-mutation
test-design rule**: when mutmut wraps a literal in `XX...XX`, substring
assertions fail to detect the change because the original substring is still
present inside the wrapper. Tests that assert on error message text need
either exact-match (`assertEqual(str(ctx.exception), expected)`) or anchored
regex (`^...$`). The codebase's existing error-message tests used substring
checks via `assertRaisesRegex` with no anchoring; the surviving 259/260/261/
264/267/273/274 mutants are all the same problem.

The second pattern is the **dataclass-contract test gap**. The project
canonically uses `@dataclass(frozen=True, slots=True)` for normalized data
(`python-patterns.md`). Removing `frozen=True` would silently allow mutation
of `ScoreResult`, `Thresholds`, `Violation`, or `Verdict` — and the existing
test suite would not have caught it. A `with self.assertRaises(FrozenInstance
Error): instance.field = ...` per dataclass is enough to pin the contract;
`hasattr(cls, "__slots__")` covers the slots half.

These two patterns are reusable beyond this module. If the broader codebase
ever runs mutation testing against `src/app/` or `src/importers/`, the same
two gap-classes will dominate the survivor list. A learned-pattern note may
be worth promoting after a second instance — one branch is below the bar.

The cli.py situation deserves a structural note. mutmut treats every line of
subprocess wiring as a mutable target, so the survivor count is high by
construction. The honest read of the 202 cli.py survivors is "mutation
testing reveals the integration boundary, not necessarily a defect" — much
the same way that a 100% line-covered subprocess wrapper can still let
behavior break. The path forward is either to extract small pure helpers
from cli.py (which would surface as new mutants in those helpers, killable
by unit tests) or to add a real coverage-subprocess integration test. Both
are out of scope for this slice but documented here so the next hardening
branch starts from facts, not taste.

The Windows-specific `PYTHONIOENCODING=utf-8` workaround for `mutmut`'s
emoji output is a tooling friction that does not belong in this branch.
A future improvement could ship a small wrapper command, but that needs to
weigh against the "documentation-only path" decision in PR #209.
