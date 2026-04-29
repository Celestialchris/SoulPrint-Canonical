"""Tests for src/quality/scorer.py.

These tests cover the pure scoring logic only. The CLI in
src/quality/cli.py orchestrates subprocesses (coverage, pytest) and is
verified by running it manually; tests must not invoke
`coverage run -m pytest` from inside the test suite (recursive
instrumentation is a documented stop condition).
"""

from __future__ import annotations

import unittest

from src.quality.scorer import (
    ScoreResult,
    compute_crap,
    derive_function_coverage,
    score_tree,
)


class ComputeCrapTest(unittest.TestCase):
    def test_full_coverage_low_complexity_equals_complexity(self):
        # cov term collapses to 0; CRAP = complexity
        self.assertAlmostEqual(compute_crap(100.0, 1), 1.0)
        self.assertAlmostEqual(compute_crap(100.0, 5), 5.0)

    def test_zero_coverage_high_complexity_is_large(self):
        # comp=20, cov=0 -> 20^2 * 1 + 20 = 420
        self.assertAlmostEqual(compute_crap(0.0, 20), 420.0)

    def test_half_coverage_medium_complexity_is_middle(self):
        # comp=10, cov=50 -> 100 * (0.5)^3 + 10 = 12.5 + 10 = 22.5
        self.assertAlmostEqual(compute_crap(50.0, 10), 22.5)

    def test_zero_complexity_returns_zero(self):
        # Synthetic guard; radon does not normally emit comp=0.
        self.assertEqual(compute_crap(0.0, 0), 0.0)
        self.assertEqual(compute_crap(100.0, 0), 0.0)

    def test_full_coverage_collapses_to_complexity_for_any_complexity(self):
        # (1 - 1.0)^3 == 0, so CRAP = complexity for any cov=100.
        for c in (1, 3, 7, 12, 25):
            with self.subTest(complexity=c):
                self.assertAlmostEqual(compute_crap(100.0, c), float(c))


class DeriveFunctionCoverageTest(unittest.TestCase):
    def test_synthetic_block_matches_spec(self):
        # Span 10..20 (inclusive, 11 lines).
        # Executed in span: {10,12,14} (3 lines).
        # Missing in span:  {11,13,15,16,17,18,19,20} (8 lines).
        # Total executable: 11. Coverage = 3/11 * 100.
        executed = {10, 12, 14}
        missing = {11, 13, 15, 16, 17, 18, 19, 20}
        cov = derive_function_coverage(executed, missing, 10, 20)
        self.assertIsNotNone(cov)
        self.assertAlmostEqual(cov, (3 / 11) * 100.0)

    def test_no_executable_lines_returns_none(self):
        # Function span exists but coverage marks no lines either way.
        self.assertIsNone(derive_function_coverage(set(), set(), 5, 8))

    def test_lines_outside_span_are_ignored(self):
        # Executed/missing lines outside lineno..endline must not affect result.
        executed = {1, 2, 3, 50}
        missing = {4, 5, 60, 70}
        cov = derive_function_coverage(executed, missing, 10, 20)
        self.assertIsNone(cov)


class ScoreTreeTest(unittest.TestCase):
    def test_results_are_ranked_descending_by_crap(self):
        complexity_data = {
            ("src/a.py", "low"): 2,
            ("src/b.py", "high"): 15,
            ("src/c.py", "mid"): 8,
        }
        coverage_data = {
            ("src/a.py", "low"): 100.0,
            ("src/b.py", "high"): 0.0,
            ("src/c.py", "mid"): 50.0,
        }
        results = score_tree(coverage_data, complexity_data)
        craps = [r.crap for r in results]
        self.assertEqual(craps, sorted(craps, reverse=True))
        self.assertEqual(results[0].function, "high")
        self.assertEqual(results[-1].function, "low")

    def test_joins_inputs_by_file_and_function_key(self):
        complexity_data = {
            ("src/foo.py", "alpha"): 4,
            ("src/foo.py", "beta"): 6,
            ("src/bar.py", "alpha"): 2,  # same function name, different file
        }
        coverage_data = {
            ("src/foo.py", "alpha"): 75.0,
            ("src/foo.py", "beta"): 25.0,
            ("src/bar.py", "alpha"): 100.0,
        }
        results = score_tree(coverage_data, complexity_data)
        self.assertEqual(len(results), 3)
        as_dict = {(r.file, r.function): r for r in results}
        self.assertEqual(as_dict[("src/foo.py", "alpha")].complexity, 4)
        self.assertEqual(as_dict[("src/foo.py", "alpha")].coverage_pct, 75.0)
        self.assertEqual(as_dict[("src/bar.py", "alpha")].complexity, 2)
        self.assertEqual(as_dict[("src/bar.py", "alpha")].coverage_pct, 100.0)

    def test_missing_coverage_treated_as_zero_percent(self):
        complexity_data = {("src/x.py", "untracked"): 5}
        coverage_data: dict[tuple[str, str], float] = {}
        results = score_tree(coverage_data, complexity_data)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.coverage_pct, 0.0)
        # comp=5, cov=0 -> 25 * 1 + 5 = 30
        self.assertAlmostEqual(result.crap, 30.0)

    def test_returns_score_result_dataclass_instances(self):
        complexity_data = {("src/m.py", "f"): 3}
        coverage_data = {("src/m.py", "f"): 100.0}
        results = score_tree(coverage_data, complexity_data)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ScoreResult)


if __name__ == "__main__":
    unittest.main()
