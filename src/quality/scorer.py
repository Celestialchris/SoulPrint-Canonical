"""Pure scoring functions for the SoulPrint quality toolchain.

CRAP score (Change Risk Anti-Patterns), original formula by Alberto Savoia
and Bob Evans (crap4j, 2007):

    CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)

where comp(m) is the cyclomatic complexity of method m and cov(m) is its
test coverage as a percentage. High complexity and low coverage compound;
fully covered code reduces to its complexity.

This module is pure: no I/O, no subprocess, no filesystem access. The CLI
layer in src/quality/cli.py runs coverage and radon, then feeds the
joined data here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScoreResult:
    file: str
    function: str
    complexity: int
    coverage_pct: float
    crap: float


def compute_crap(coverage_pct: float, complexity: int) -> float:
    """Return the CRAP score for one function.

    coverage_pct: 0.0 to 100.0.
    complexity: cyclomatic complexity, integer.

    By convention complexity == 0 yields 0.0; radon does not normally emit
    blocks with complexity 0, so this branch only guards against synthetic
    inputs (e.g., from tests).
    """
    if complexity <= 0:
        return 0.0
    cov_fraction = coverage_pct / 100.0
    return complexity * complexity * (1.0 - cov_fraction) ** 3 + complexity


def derive_function_coverage(
    executed_lines: set[int],
    missing_lines: set[int],
    lineno: int,
    endline: int,
) -> float | None:
    """Derive per-function coverage from line-level coverage data.

    Intersects executed and missing line sets with the function's line
    span (inclusive). Lines outside both sets are non-executable
    (docstrings, blank lines, decorators that coverage skips); they do
    not count toward the denominator.

    Returns coverage as 0.0-100.0, or None if the span has no executable
    lines. Callers skip None-returning blocks rather than treating them
    as 100%; functions with no executable lines have no meaningful CRAP.
    """
    span = set(range(lineno, endline + 1))
    executed_in_span = executed_lines & span
    missing_in_span = missing_lines & span
    total = len(executed_in_span) + len(missing_in_span)
    if total == 0:
        return None
    return (len(executed_in_span) / total) * 100.0


def score_tree(
    coverage_data: dict[tuple[str, str], float],
    complexity_data: dict[tuple[str, str], int],
) -> list[ScoreResult]:
    """Join coverage and complexity by (file, function); rank desc by CRAP.

    A function present in complexity_data but missing from coverage_data
    is treated as 0% coverage; this keeps untested code visible in the
    ranking instead of silently dropped. The reverse case (coverage
    without complexity) is ignored: only functions radon identified are
    scored.
    """
    results: list[ScoreResult] = []
    for key, complexity in complexity_data.items():
        cov = coverage_data.get(key, 0.0)
        crap = compute_crap(cov, complexity)
        file_path, function_name = key
        results.append(
            ScoreResult(
                file=file_path,
                function=function_name,
                complexity=complexity,
                coverage_pct=cov,
                crap=crap,
            )
        )
    results.sort(key=lambda r: r.crap, reverse=True)
    return results
