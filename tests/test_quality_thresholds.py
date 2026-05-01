"""Tests for src/quality/thresholds.py.

These tests cover the threshold policy layer only: load, save, evaluate,
ratchet. They build synthetic ScoreResult lists rather than running the
real coverage pipeline; the CLI orchestration (subprocess + radon) is
verified manually. Tests must not invoke `coverage run -m pytest` from
inside the test suite (recursive instrumentation is a documented stop
condition for the quality toolchain).
"""

from __future__ import annotations

import json
import unittest

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
        t = Thresholds()
        self.assertEqual(t.max_crap, float("inf"))
        self.assertGreater(t.max_complexity, 1_000_000)
        self.assertEqual(t.min_coverage_percent, 0.0)
        self.assertEqual(t.top_n, 20)


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

    def test_top_n_zero_passes_vacuously(self):
        results = [_r("a.py", "x", 100, 0.0, 10000.0)]
        t = Thresholds(max_crap=10.0, top_n=0)
        verdict = evaluate(results, t)
        self.assertTrue(verdict.passed)
        self.assertEqual(verdict.checked_count, 0)

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
