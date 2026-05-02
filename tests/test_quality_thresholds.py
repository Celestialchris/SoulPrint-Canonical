"""Tests for src/quality/thresholds.py.

These tests cover the threshold policy layer only: load, save, evaluate,
ratchet. They build synthetic ScoreResult lists rather than running the
real coverage pipeline; the CLI orchestration (subprocess + radon) is
verified manually. Tests must not invoke `coverage run -m pytest` from
inside the test suite (recursive instrumentation is a documented stop
condition for the quality toolchain).
"""

from __future__ import annotations

import dataclasses
import json
import unittest

from src.quality.cli import _run_check, _run_ratchet
from src.quality.scorer import ScoreResult
from src.quality.thresholds import (
    THRESHOLD_SCHEMA,
    Thresholds,
    Violation,
    Verdict,
    compute_ratchet,
    evaluate,
    load_thresholds,
    save_thresholds,
)
from tests.temp_helpers import make_test_temp_dir


def _r(file: str, function: str, complexity: int, cov: float, crap: float) -> ScoreResult:
    return ScoreResult(
        file=file,
        function=function,
        complexity=complexity,
        coverage_pct=cov,
        crap=crap,
    )


class ThresholdsDefaultsTest(unittest.TestCase):
    def test_defaults_are_permissive(self):
        # A bare Thresholds() must not block any valid measurement,
        # so partial configs that omit fields cannot silently fail CI.
        # The exact default values are pinned so a silent drift (e.g.,
        # 1_000_000_000 -> 1_000_000_001) surfaces here instead of in CI.
        t = Thresholds()
        self.assertEqual(t.max_crap, float("inf"))
        self.assertEqual(t.max_complexity, 1_000_000_000)
        self.assertEqual(t.min_coverage_percent, 0.0)
        self.assertEqual(t.top_n, 20)


class ThresholdSchemaConstantTest(unittest.TestCase):
    """The schema string is the on-disk format marker. Tests that compare
    saved JSON against the imported constant cannot detect a constant
    refactor, so the literal value is pinned here.
    """

    def test_schema_marker_is_canonical_string(self):
        self.assertEqual(THRESHOLD_SCHEMA, "soulprint.quality.thresholds.v1")


class ThresholdsDataclassContractTest(unittest.TestCase):
    """Thresholds, Violation, and Verdict use `@dataclass(frozen=True, slots=True)`.
    Mutation testing showed the suite did not enforce either half of that
    contract; these tests pin both.
    """

    def test_thresholds_is_frozen(self):
        t = Thresholds()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            t.max_crap = 999.0  # type: ignore[misc]

    def test_thresholds_class_defines_slots(self):
        self.assertTrue(hasattr(Thresholds, "__slots__"))

    def test_violation_is_frozen(self):
        v = Violation(
            kind="max_crap", file="x.py", function="f", actual=1.0, threshold=0.0
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            v.actual = 999.0  # type: ignore[misc]

    def test_violation_class_defines_slots(self):
        self.assertTrue(hasattr(Violation, "__slots__"))

    def test_verdict_is_frozen(self):
        v = Verdict(passed=True, violations=(), checked_count=0)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            v.passed = False  # type: ignore[misc]

    def test_verdict_class_defines_slots(self):
        self.assertTrue(hasattr(Verdict, "__slots__"))


class ThresholdsValidationTest(unittest.TestCase):
    """top_n < 1 and other obviously-bad values must fail at construction.

    Rationale: quality-thresholds.json is hand-editable. A typo like
    `"top_n": -20` would evaluate as a vacuous pass (no functions
    checked), silently disabling the check gate. The dataclass
    refuses construction so the failure surfaces at load_thresholds()
    rather than during evaluation.
    """

    def test_top_n_zero_rejected(self):
        with self.assertRaises(ValueError):
            Thresholds(top_n=0)

    def test_top_n_negative_rejected(self):
        with self.assertRaises(ValueError):
            Thresholds(top_n=-20)

    def test_negative_max_crap_rejected(self):
        with self.assertRaises(ValueError):
            Thresholds(max_crap=-1.0)

    def test_negative_max_complexity_rejected(self):
        with self.assertRaises(ValueError):
            Thresholds(max_complexity=-5)

    def test_min_coverage_above_100_rejected(self):
        with self.assertRaises(ValueError):
            Thresholds(min_coverage_percent=150.0)

    def test_min_coverage_below_zero_rejected(self):
        with self.assertRaises(ValueError):
            Thresholds(min_coverage_percent=-1.0)

    def test_min_coverage_at_boundaries_accepted(self):
        # 0 and 100 are the inclusive endpoints; both must be valid.
        Thresholds(min_coverage_percent=0.0)
        Thresholds(min_coverage_percent=100.0)

    def test_max_crap_at_zero_accepted(self):
        # `max_crap >= 0` is the documented invariant; 0 is the inclusive
        # lower bound. Guards against `< 0` being tightened to `<= 0` or `< 1`.
        Thresholds(max_crap=0.0)

    def test_max_crap_below_one_accepted(self):
        # Specifically guards against `< 0` -> `< 1`, which would reject
        # the legal value 0.5.
        Thresholds(max_crap=0.5)

    def test_max_complexity_at_zero_accepted(self):
        # Documented as `max_complexity >= 0`; zero must construct cleanly.
        Thresholds(max_complexity=0)

    def test_min_coverage_just_above_one_hundred_rejected(self):
        # 100.5 is just past the upper bound; guards against the inclusive
        # check `<= 100.0` being widened to `<= 101.0`.
        with self.assertRaises(ValueError):
            Thresholds(min_coverage_percent=100.5)

    def test_top_n_error_message_is_canonical(self):
        # Exact-match the full message so that any string mutation
        # (wholesale, wrap, or replacement) trips this test. Substring
        # checks would not catch wrap-style mutations like "XX...XX".
        with self.assertRaises(ValueError) as ctx:
            Thresholds(top_n=0)
        self.assertEqual(
            str(ctx.exception),
            "top_n must be >= 1; got 0. "
            "A non-positive top_n would silently disable enforcement "
            "(evaluate would report a vacuous pass with no functions checked).",
        )

    def test_max_crap_error_message_is_canonical(self):
        with self.assertRaises(ValueError) as ctx:
            Thresholds(max_crap=-1.0)
        self.assertEqual(str(ctx.exception), "max_crap must be >= 0; got -1.0")

    def test_max_complexity_error_message_is_canonical(self):
        with self.assertRaises(ValueError) as ctx:
            Thresholds(max_complexity=-5)
        self.assertEqual(
            str(ctx.exception), "max_complexity must be >= 0; got -5"
        )

    def test_min_coverage_error_message_is_canonical(self):
        with self.assertRaises(ValueError) as ctx:
            Thresholds(min_coverage_percent=-1.0)
        self.assertEqual(
            str(ctx.exception),
            "min_coverage_percent must be in [0, 100]; got -1.0",
        )


class LoadThresholdsTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "quality-thresholds-load")

    def test_loads_full_config(self):
        path = self.tmpdir / "thresholds.json"
        path.write_text(
            json.dumps(
                {
                    "schema": THRESHOLD_SCHEMA,
                    "max_crap": 550.0,
                    "max_complexity": 70,
                    "min_coverage_percent": 25.0,
                    "top_n": 15,
                }
            ),
            encoding="utf-8",
        )
        t = load_thresholds(path)
        self.assertEqual(t.max_crap, 550.0)
        self.assertEqual(t.max_complexity, 70)
        self.assertEqual(t.min_coverage_percent, 25.0)
        self.assertEqual(t.top_n, 15)

    def test_missing_fields_take_defaults(self):
        path = self.tmpdir / "partial.json"
        path.write_text(json.dumps({"max_crap": 100.0}), encoding="utf-8")
        t = load_thresholds(path)
        self.assertEqual(t.max_crap, 100.0)
        # all other fields fall back to permissive defaults
        self.assertEqual(t.min_coverage_percent, 0.0)
        self.assertEqual(t.top_n, 20)

    def test_unknown_fields_are_ignored(self):
        path = self.tmpdir / "extra.json"
        path.write_text(
            json.dumps({"max_crap": 100.0, "spaceship_mode": True}),
            encoding="utf-8",
        )
        t = load_thresholds(path)
        self.assertEqual(t.max_crap, 100.0)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_thresholds(self.tmpdir / "does-not-exist.json")

    def test_malformed_json_raises_json_decode_error(self):
        path = self.tmpdir / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            load_thresholds(path)

    def test_negative_top_n_in_file_raises_value_error(self):
        # The hand-edit footgun the validation guards against: a typo
        # of "top_n": -20 must surface at load time, not as a vacuous
        # pass during evaluation.
        path = self.tmpdir / "bad-top-n.json"
        path.write_text(json.dumps({"top_n": -20}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_thresholds(path)

    def test_non_numeric_max_crap_raises_value_error(self):
        path = self.tmpdir / "bad-type.json"
        path.write_text(
            json.dumps({"max_crap": "not a number"}), encoding="utf-8"
        )
        with self.assertRaises(ValueError):
            load_thresholds(path)


class SaveThresholdsTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "quality-thresholds-save")

    def test_round_trip(self):
        path = self.tmpdir / "out.json"
        original = Thresholds(
            max_crap=510.0,
            max_complexity=60,
            min_coverage_percent=25.0,
            top_n=15,
        )
        save_thresholds(path, original)
        loaded = load_thresholds(path)
        self.assertEqual(loaded, original)

    def test_writes_schema_marker(self):
        path = self.tmpdir / "out.json"
        save_thresholds(path, Thresholds(max_crap=100.0, max_complexity=10))
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], THRESHOLD_SCHEMA)


class EvaluateTest(unittest.TestCase):
    def test_pass_when_all_within_caps(self):
        results = [
            _r("a.py", "f1", 10, 50.0, 100.0),
            _r("b.py", "f2", 5, 80.0, 30.0),
        ]
        t = Thresholds(
            max_crap=200.0,
            max_complexity=20,
            min_coverage_percent=0.0,
            top_n=20,
        )
        verdict = evaluate(results, t)
        self.assertTrue(verdict.passed)
        self.assertEqual(verdict.violations, ())
        self.assertEqual(verdict.checked_count, 2)

    def test_fail_when_crap_exceeds_ceiling(self):
        results = [_r("a.py", "bad", 30, 0.0, 930.0)]
        t = Thresholds(max_crap=500.0, max_complexity=100, top_n=20)
        verdict = evaluate(results, t)
        self.assertFalse(verdict.passed)
        self.assertEqual(len(verdict.violations), 1)
        v = verdict.violations[0]
        self.assertEqual(v.kind, "max_crap")
        self.assertEqual(v.function, "bad")
        self.assertAlmostEqual(v.actual, 930.0)
        self.assertAlmostEqual(v.threshold, 500.0)

    def test_fail_when_complexity_exceeds_ceiling(self):
        # cov 100 keeps CRAP equal to complexity; only complexity violates
        results = [_r("a.py", "complex", 80, 100.0, 80.0)]
        t = Thresholds(max_crap=10000.0, max_complexity=70, top_n=20)
        verdict = evaluate(results, t)
        self.assertFalse(verdict.passed)
        kinds = {v.kind for v in verdict.violations}
        self.assertEqual(kinds, {"max_complexity"})

    def test_fail_when_coverage_below_floor(self):
        results = [_r("a.py", "thin", 10, 30.0, 50.0)]
        t = Thresholds(
            max_crap=1000.0,
            max_complexity=100,
            min_coverage_percent=50.0,
            top_n=20,
        )
        verdict = evaluate(results, t)
        self.assertFalse(verdict.passed)
        self.assertEqual(verdict.violations[0].kind, "min_coverage_percent")
        self.assertAlmostEqual(verdict.violations[0].actual, 30.0)
        self.assertAlmostEqual(verdict.violations[0].threshold, 50.0)

    def test_one_function_can_produce_multiple_violations(self):
        # complexity 80, cov 0 -> CRAP huge; all three thresholds breached
        results = [_r("a.py", "wreck", 80, 0.0, 6480.0)]
        t = Thresholds(
            max_crap=500.0,
            max_complexity=70,
            min_coverage_percent=10.0,
            top_n=20,
        )
        verdict = evaluate(results, t)
        kinds = {v.kind for v in verdict.violations}
        self.assertEqual(
            kinds,
            {"max_crap", "max_complexity", "min_coverage_percent"},
        )

    def test_only_top_n_evaluated(self):
        # Five functions; top_n=2; only the two highest-CRAP get checked.
        # Functions ranked 3-5 would violate max_complexity if checked,
        # but ranking puts them outside the top_n window.
        results = [
            _r("a.py", "worst", 30, 0.0, 930.0),
            _r("b.py", "bad", 20, 0.0, 420.0),
            _r("c.py", "ok1", 5, 0.0, 30.0),
            _r("d.py", "ok2", 5, 0.0, 30.0),
            _r("e.py", "ok3", 5, 0.0, 30.0),
        ]
        t = Thresholds(
            max_crap=10000.0,
            max_complexity=4,
            min_coverage_percent=0.0,
            top_n=2,
        )
        verdict = evaluate(results, t)
        self.assertEqual(verdict.checked_count, 2)
        functions = {v.function for v in verdict.violations}
        self.assertEqual(functions, {"worst", "bad"})

    def test_evaluate_does_not_assume_pre_sorted_input(self):
        # score_tree already sorts, but evaluate must be robust to arbitrary order.
        results = [
            _r("low.py", "low", 5, 100.0, 5.0),
            _r("hi.py", "hi", 30, 0.0, 930.0),  # worst, but appears second
        ]
        t = Thresholds(max_crap=500.0, max_complexity=100, top_n=1)
        verdict = evaluate(results, t)
        self.assertEqual(verdict.checked_count, 1)
        # The single checked function must be the worst by CRAP, not the first by index.
        self.assertEqual(verdict.violations[0].function, "hi")

    def test_actual_equal_to_max_crap_does_not_violate(self):
        # max_crap is a strict ceiling per the docstring: only `r.crap > max_crap`
        # fails. Equality is a pass. Guards against `>` being relaxed to `>=`,
        # which would turn the documented inclusive ceiling into an exclusive one.
        results = [_r("a.py", "exact", 10, 0.0, 110.0)]
        t = Thresholds(max_crap=110.0, max_complexity=20, top_n=20)
        verdict = evaluate(results, t)
        self.assertTrue(verdict.passed)

    def test_actual_equal_to_max_complexity_does_not_violate(self):
        # max_complexity is a strict ceiling: only `r.complexity > max_complexity`
        # fails. Symmetric to the max_crap boundary above.
        results = [_r("a.py", "exact", 20, 100.0, 20.0)]
        t = Thresholds(max_crap=1000.0, max_complexity=20, top_n=20)
        verdict = evaluate(results, t)
        self.assertTrue(verdict.passed)


class ComputeRatchetTest(unittest.TestCase):
    def test_tightens_when_measured_is_stricter(self):
        results = [
            _r("a.py", "x", 60, 50.0, 510.0),
            _r("b.py", "y", 30, 70.0, 100.0),
        ]
        current = Thresholds(
            max_crap=600.0,
            max_complexity=80,
            min_coverage_percent=0.0,
            top_n=20,
        )
        new = compute_ratchet(results, current)
        self.assertEqual(new.max_crap, 510.0)
        self.assertEqual(new.max_complexity, 60)
        self.assertEqual(new.min_coverage_percent, 50.0)

    def test_refuses_to_loosen_when_measured_is_worse(self):
        # Measured exceeds current; threshold must NOT rise to match.
        results = [_r("a.py", "x", 100, 0.0, 10000.0)]
        current = Thresholds(
            max_crap=500.0,
            max_complexity=50,
            min_coverage_percent=10.0,
            top_n=20,
        )
        new = compute_ratchet(results, current)
        self.assertEqual(new.max_crap, 500.0)
        self.assertEqual(new.max_complexity, 50)
        # measured min coverage 0.0 is BELOW current floor 10.0; floor stays.
        self.assertEqual(new.min_coverage_percent, 10.0)

    def test_no_op_when_already_at_limit(self):
        results = [_r("a.py", "x", 60, 50.0, 510.0)]
        current = Thresholds(
            max_crap=510.0,
            max_complexity=60,
            min_coverage_percent=50.0,
            top_n=20,
        )
        new = compute_ratchet(results, current)
        self.assertEqual(new, current)

    def test_partial_tighten_per_field(self):
        # CRAP can tighten; complexity already tight; coverage already tight.
        results = [_r("a.py", "x", 60, 50.0, 400.0)]
        current = Thresholds(
            max_crap=600.0,
            max_complexity=60,
            min_coverage_percent=50.0,
            top_n=20,
        )
        new = compute_ratchet(results, current)
        self.assertEqual(new.max_crap, 400.0)
        self.assertEqual(new.max_complexity, 60)
        self.assertEqual(new.min_coverage_percent, 50.0)
        self.assertNotEqual(new, current)

    def test_empty_results_returns_current_unchanged(self):
        current = Thresholds(
            max_crap=500.0,
            max_complexity=70,
            min_coverage_percent=0.0,
            top_n=20,
        )
        new = compute_ratchet([], current)
        self.assertEqual(new, current)

    def test_only_top_n_drives_ratchet(self):
        # Top_n=1; the single worst by CRAP determines new max_complexity,
        # not a higher-complexity but lower-CRAP function ranked below it.
        results = [
            _r("a.py", "worst_crap", 10, 0.0, 110.0),  # ranked 1 by CRAP
            _r("b.py", "high_complex", 100, 100.0, 100.0),  # ranked 2 by CRAP
        ]
        current = Thresholds(
            max_crap=200.0,
            max_complexity=200,
            top_n=1,
        )
        new = compute_ratchet(results, current)
        # Only "worst_crap" (complexity=10) was in scope; complexity tightens to 10.
        self.assertEqual(new.max_complexity, 10)
        self.assertEqual(new.max_crap, 110.0)


class CliInvalidConfigTest(unittest.TestCase):
    """--check and --ratchet must convert load failures into exit 1.

    Without the structured exception handling in _load_thresholds_or_report,
    a malformed quality-thresholds.json raises uncaught
    JSONDecodeError/ValueError/OSError, surfacing in CI as a traceback
    rather than a graceful failure with a useful message.
    """

    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "quality-cli-invalid")

    def test_check_returns_one_on_missing_file(self):
        rc = _run_check([], self.tmpdir / "missing.json")
        self.assertEqual(rc, 1)

    def test_check_returns_one_on_malformed_json(self):
        path = self.tmpdir / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        rc = _run_check([], path)
        self.assertEqual(rc, 1)

    def test_check_returns_one_on_invalid_field(self):
        path = self.tmpdir / "bad.json"
        path.write_text(json.dumps({"top_n": -20}), encoding="utf-8")
        rc = _run_check([], path)
        self.assertEqual(rc, 1)

    def test_check_returns_one_on_non_numeric_field(self):
        path = self.tmpdir / "bad.json"
        path.write_text(
            json.dumps({"max_crap": "infinite"}), encoding="utf-8"
        )
        rc = _run_check([], path)
        self.assertEqual(rc, 1)

    def test_ratchet_returns_one_on_missing_file(self):
        rc = _run_ratchet([], self.tmpdir / "missing.json")
        self.assertEqual(rc, 1)

    def test_ratchet_returns_one_on_malformed_json(self):
        path = self.tmpdir / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        rc = _run_ratchet([], path)
        self.assertEqual(rc, 1)

    def test_ratchet_returns_one_on_invalid_field(self):
        path = self.tmpdir / "bad.json"
        path.write_text(json.dumps({"top_n": 0}), encoding="utf-8")
        rc = _run_ratchet([], path)
        self.assertEqual(rc, 1)


class RatchetSaveLoadIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "quality-thresholds-ratchet")

    def test_load_ratchet_save_load_round_trip(self):
        path = self.tmpdir / "thresholds.json"
        save_thresholds(
            path,
            Thresholds(
                max_crap=600.0,
                max_complexity=80,
                min_coverage_percent=0.0,
                top_n=20,
            ),
        )
        current = load_thresholds(path)
        results = [_r("a.py", "x", 60, 50.0, 510.0)]
        new = compute_ratchet(results, current)
        save_thresholds(path, new)
        reloaded = load_thresholds(path)
        self.assertEqual(reloaded.max_crap, 510.0)
        self.assertEqual(reloaded.max_complexity, 60)
        self.assertEqual(reloaded.min_coverage_percent, 50.0)


if __name__ == "__main__":
    unittest.main()
