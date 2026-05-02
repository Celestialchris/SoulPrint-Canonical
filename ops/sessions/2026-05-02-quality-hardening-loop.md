## May 2, 2026 — Quality Engine Layer 5 (First Mutation-Killing Hardening Slice)

**Branch:** feat/quality-hardening-loop
**PR:** (pending)

**What:** First post-MVP slice of the quality hardening loop. Layer 4 shipped
mutation testing as a local tool in `feat/mutation-testing-mvp` (PR #209) but
landed without inspecting any survivors. This branch establishes the loop:
baseline, inspect, harden, re-baseline, document. Scope was held to the pure
functions in `src/quality/scorer.py` and `src/quality/thresholds.py`; the
subprocess-orchestration mutants in `src/quality/cli.py` are explicitly out of
scope for this slice (per the routed prompt's stop condition).

**Decisions:**
- Hardening targets were chosen by inspecting `mutmut show <id>` output, not by
  intuition. Every test added traces to a specific surviving mutant.
- Two test-design lessons from the survivor map were applied:
  1. The `mutmut` "XX...XX" wrapper for string-literal mutations is not killable
     by substring assertions — `assertIn("top_n must be", message)` still passes
     against `"XXtop_n must be...XX"`. Error-message tests use exact-match
     `assertEqual(str(ctx.exception), ...)` instead.
  2. The `@dataclass(frozen=True, slots=True)` pattern (canonical in
     `python-patterns.md`) had no test enforcement on any of the four
     dataclasses in the quality module. A surviving frozen→False mutant on
     `ScoreResult` was the trigger to pin both halves of the contract for
     `ScoreResult`, `Thresholds`, `Violation`, and `Verdict`.
- One mutant was identified as semantically equivalent and explicitly deferred
  rather than killed: `compute_crap`'s early return for `complexity <= 0`. When
  `complexity == 0`, the formula `0 * 0 * (1 - cov/100) ** 3 + 0` evaluates to
  the same float `0.0` as the early return, so no behavioral test can
  distinguish the original from the `complexity < 0` mutant. The guard is kept
  for readability; the mutant is deferred with rationale rather than papering
  over with a contrived test.
- Scope held: no edits to `src/quality/cli.py` (subprocess paths), no schema
  changes, no CI wiring, no threshold edits, no full-repo mutation runs.
- Did not touch `quality-thresholds.json`, `pyproject.toml`,
  `.github/workflows/`, or `.gitignore`. The `.mutmut-cache` remains gitignored
  and uncommitted.
- A Windows-specific console encoding workaround was needed for `mutmut`:
  `PYTHONIOENCODING=utf-8` is required to print the survival emoji (`🙁`) under
  cp1252 default. Not in scope to upstream-fix; documented inline.

**Files changed:**
- `tests/test_quality_scorer.py`: added `dataclasses` import, two boundary
  tests in `DeriveFunctionCoverageTest`, and a new `ScoreResultContractTest`
  class pinning the frozen + slots contract.
- `tests/test_quality_thresholds.py`: added `dataclasses` import, tightened
  `test_defaults_are_permissive` from `assertGreater` to `assertEqual`,
  and added: `ThresholdSchemaConstantTest`, `ThresholdsDataclassContractTest`,
  five boundary-acceptance tests in `ThresholdsValidationTest`, four
  exact-match error-message tests, and two equality-boundary tests in
  `EvaluateTest`.

**Verification:**
- Targeted suite: 50 → 71 passing (21 new tests). `python -m pytest
  tests/test_quality_scorer.py tests/test_quality_thresholds.py -v`.
- `soulprint-quality --check`: PASS, unchanged thresholds (max_crap ≤ 510.02,
  max_complexity ≤ 64, min_coverage ≥ 0.0).
- Mutation baseline (before hardening): 329 mutants, 230 survived
  (cli.py: 202, thresholds.py: 24, scorer.py: 4).
- Mutation baseline (after hardening): 329 mutants, 204 survived
  (cli.py: 202, thresholds.py: 1, scorer.py: 1).
- Net new kills: 26 (3 scorer.py + 23 thresholds.py). Kill rate on the
  actionable pure-function surface: 26/28 ≈ 93%.

**Survivors deferred:**
- scorer.py id 210 (`if complexity <= 0` → `if complexity < 0`): equivalent
  mutant. Documented above.
- src/quality/cli.py mutants 1–158, 161–165, 168–206 (202 total): out of scope
  for this slice. These are subprocess orchestration paths (coverage/radon
  invocation, JSON I/O, exit code branches). Killing them would require either
  CLI integration tests against a real coverage subprocess (tooling change,
  out of scope) or a refactor to extract pure helpers (refactor, out of scope).
  Documented as known-limitation in the expert report.

**Next:**
- Open PR for `feat/quality-hardening-loop` once mutation re-baseline is
  recorded.
- Future hardening slices can extract pure helpers from `cli.py` (e.g., the
  arg-parse and report-formatting code paths) to widen the killable surface
  without changing CI scope.
