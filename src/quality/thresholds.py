"""Threshold checking and ratcheting for the SoulPrint quality toolchain.

Layer 2 of the quality engine. Layer 1 (`scorer.py`) computes CRAP scores;
this layer converts those scores into pass/fail verdicts against a
configured policy file (`quality-thresholds.json` at repo root).

Three operations, all pure (no filesystem outside `load_thresholds` and
`save_thresholds`):

    load_thresholds(path) -> Thresholds
        Read the JSON policy file. Missing fields fall back to defaults.

    evaluate(results, thresholds) -> Verdict
        Compare the top-N ranked ScoreResults against the configured caps
        (max_crap, max_complexity) and floor (min_coverage_percent).

    compute_ratchet(results, thresholds) -> Thresholds
        Tighten thresholds based on current measurements. Never loosens.
        Returns an equal Thresholds when no tightening is possible.

The CRAP formula itself lives in `scorer.py` and is not modified here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

from .scorer import ScoreResult


THRESHOLD_SCHEMA = "soulprint.quality.thresholds.v1"


@dataclass(frozen=True, slots=True)
class Thresholds:
    """Policy caps for the quality toolchain.

    `max_crap` and `max_complexity` are ceilings (any function exceeding
    them is a violation). `min_coverage_percent` is a floor. `top_n`
    bounds how many ranked functions are checked; functions ranked
    below top_n are not enforced.

    Defaults are permissive so a partial config does not silently block
    CI: missing fields evaluate as "not enforced" rather than "strict
    zero". Field-level invariants (top_n >= 1, max_* >= 0,
    min_coverage_percent in [0, 100]) are enforced in __post_init__ so a
    hand-edit typo in quality-thresholds.json fails fast at load time
    rather than silently disabling enforcement.
    """

    max_crap: float = float("inf")
    max_complexity: int = 1_000_000_000
    min_coverage_percent: float = 0.0
    top_n: int = 20

    def __post_init__(self) -> None:
        if self.top_n < 1:
            raise ValueError(
                f"top_n must be >= 1; got {self.top_n}. "
                "A non-positive top_n would silently disable enforcement "
                "(evaluate would report a vacuous pass with no functions checked)."
            )
        if self.max_crap < 0:
            raise ValueError(f"max_crap must be >= 0; got {self.max_crap}")
        if self.max_complexity < 0:
            raise ValueError(
                f"max_complexity must be >= 0; got {self.max_complexity}"
            )
        if not (0.0 <= self.min_coverage_percent <= 100.0):
            raise ValueError(
                "min_coverage_percent must be in [0, 100]; "
                f"got {self.min_coverage_percent}"
            )


@dataclass(frozen=True, slots=True)
class Violation:
    """A single threshold breach for one ranked function."""

    kind: str  # "max_crap" | "max_complexity" | "min_coverage_percent"
    file: str
    function: str
    actual: float
    threshold: float


@dataclass(frozen=True, slots=True)
class Verdict:
    """Outcome of an `evaluate` call.

    `passed` is True iff `violations` is empty. `checked_count` is the
    actual number of functions evaluated (min of len(results) and top_n).
    """

    passed: bool
    violations: tuple[Violation, ...]
    checked_count: int


def load_thresholds(path: Path) -> Thresholds:
    """Read a quality-thresholds.json file.

    Raises FileNotFoundError if the file does not exist; the CLI catches
    this to print a helpful bootstrap hint. Unknown fields are ignored;
    missing fields take dataclass defaults.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    fields: dict = {}
    if "max_crap" in raw:
        fields["max_crap"] = float(raw["max_crap"])
    if "max_complexity" in raw:
        fields["max_complexity"] = int(raw["max_complexity"])
    if "min_coverage_percent" in raw:
        fields["min_coverage_percent"] = float(raw["min_coverage_percent"])
    if "top_n" in raw:
        fields["top_n"] = int(raw["top_n"])
    return Thresholds(**fields)


def save_thresholds(path: Path, thresholds: Thresholds) -> None:
    """Write a Thresholds policy as JSON, including the schema marker."""
    payload = {
        "schema": THRESHOLD_SCHEMA,
        "max_crap": thresholds.max_crap,
        "max_complexity": thresholds.max_complexity,
        "min_coverage_percent": thresholds.min_coverage_percent,
        "top_n": thresholds.top_n,
    }
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _top_n_by_crap(results: Iterable[ScoreResult], top_n: int) -> list[ScoreResult]:
    """Return the top_n results by CRAP, descending. Defensive sort.

    `top_n` is guaranteed >= 1 by Thresholds.__post_init__; callers always
    pass `thresholds.top_n` so there is no path here that yields a
    non-positive value.
    """
    return sorted(results, key=lambda r: r.crap, reverse=True)[:top_n]


def evaluate(results: Iterable[ScoreResult], thresholds: Thresholds) -> Verdict:
    """Check the top_n results against thresholds; return a Verdict.

    A function may produce up to three violations (one per dimension).
    The Verdict carries every breach so the CLI can render a complete
    summary instead of one-violation-at-a-time iteration.
    """
    top = _top_n_by_crap(results, thresholds.top_n)
    violations: list[Violation] = []
    for r in top:
        if r.crap > thresholds.max_crap:
            violations.append(
                Violation(
                    kind="max_crap",
                    file=r.file,
                    function=r.function,
                    actual=r.crap,
                    threshold=thresholds.max_crap,
                )
            )
        if r.complexity > thresholds.max_complexity:
            violations.append(
                Violation(
                    kind="max_complexity",
                    file=r.file,
                    function=r.function,
                    actual=float(r.complexity),
                    threshold=float(thresholds.max_complexity),
                )
            )
        if r.coverage_pct < thresholds.min_coverage_percent:
            violations.append(
                Violation(
                    kind="min_coverage_percent",
                    file=r.file,
                    function=r.function,
                    actual=r.coverage_pct,
                    threshold=thresholds.min_coverage_percent,
                )
            )
    return Verdict(
        passed=not violations,
        violations=tuple(violations),
        checked_count=len(top),
    )


def compute_ratchet(
    results: Iterable[ScoreResult], current: Thresholds
) -> Thresholds:
    """Return tighter thresholds based on the current measurement set.

    Never loosens. If `current` is already stricter than what the code
    measures, the corresponding field is preserved (typical when CI is
    failing: ratcheting must not paper over the regression).

    The contract is element-wise monotonic: every field of the returned
    Thresholds is at least as strict as the same field in `current`.
    """
    top = _top_n_by_crap(results, current.top_n)
    if not top:
        return current

    measured_max_crap = max(r.crap for r in top)
    measured_max_complexity = max(r.complexity for r in top)
    measured_min_coverage = min(r.coverage_pct for r in top)

    return replace(
        current,
        max_crap=min(current.max_crap, measured_max_crap),
        max_complexity=min(current.max_complexity, measured_max_complexity),
        min_coverage_percent=max(
            current.min_coverage_percent, measured_min_coverage
        ),
    )
