"""CLI entrypoint for the SoulPrint quality toolchain.

Runs coverage instrumentation under pytest, computes cyclomatic complexity
with radon, joins per-function coverage and complexity into CRAP scores,
and writes a ranked report in JSON + Markdown.

Reports are timestamped, never overwritten:

    ops/quality/report-YYYY-MM-DD.json    full ranked list
    ops/quality/report-YYYY-MM-DD.md      top 20 offenders, table

If multiple runs happen on the same day, a -N suffix is appended to both.

Modes:
    (default)   write timestamped reports under --out-dir
    --json      emit machine-readable JSON to stdout, write nothing
    --check     evaluate scores against quality-thresholds.json, exit non-zero on violation
    --ratchet   tighten quality-thresholds.json based on current measurements (never loosens)

Exit codes:
    0  healthy run, reports written / JSON emitted / threshold check passed / ratchet completed
    1  unexpected error (subprocess failure, parse error, etc.) or --check threshold violation
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Iterable

from .scorer import ScoreResult, derive_function_coverage, score_tree
from .thresholds import (
    Thresholds,
    Verdict,
    compute_ratchet,
    evaluate,
    load_thresholds,
    save_thresholds,
)

# `radon` is imported lazily inside `_collect_complexity`; `coverage` is
# invoked as a subprocess. Both live in the `dev` optional-dependency group
# rather than runtime requirements, so `main()` checks for availability up
# front and emits a clear install hint instead of letting a deep ImportError
# surface mid-run. See the install hint in `main()`.

CRAP_FORMULA_TEXT = "CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)"
DEFAULT_THRESHOLDS_PATH = "quality-thresholds.json"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute CRAP scores across the SoulPrint canonical tree.",
    )
    parser.add_argument(
        "--src",
        default="src/",
        help="Source root to scan with radon (default: src/)",
    )
    parser.add_argument(
        "--out-dir",
        default="ops/quality/",
        help="Directory for timestamped reports (default: ops/quality/)",
    )
    parser.add_argument(
        "--thresholds",
        default=DEFAULT_THRESHOLDS_PATH,
        help=(
            "Path to threshold policy file used by --check and --ratchet "
            f"(default: {DEFAULT_THRESHOLDS_PATH})"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON to stdout instead of writing files",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help=(
            "Evaluate current scores against the threshold policy and exit "
            "non-zero on violation. Writes no report files."
        ),
    )
    mode.add_argument(
        "--ratchet",
        action="store_true",
        help=(
            "Tighten the threshold policy in place based on current "
            "measurements. Never loosens; refuses to paper over regressions."
        ),
    )
    return parser


def _run_coverage(src_root: Path) -> dict:
    """Run pytest under coverage; return parsed coverage JSON.

    Two subprocess steps: `coverage run -m pytest tests/`, then
    `coverage json -o <tmp>`. The CLI itself does not invoke pytest.main()
    so it can be tested without recursive instrumentation.
    """
    pytest_cmd = [
        sys.executable,
        "-m",
        "coverage",
        "run",
        f"--source={src_root}",
        "-m",
        "pytest",
        "tests/",
        "-q",
    ]
    subprocess.run(pytest_cmd, check=True)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", str(tmp_path)],
            check=True,
        )
        return json.loads(tmp_path.read_text(encoding="utf-8"))
    finally:
        tmp_path.unlink(missing_ok=True)


def _normalize_file_path(file_path: str) -> str:
    return file_path.replace("\\", "/")


def _collect_complexity(
    src_root: Path,
) -> list[tuple[str, str, int, int, int]]:
    """Walk src_root for .py files; return list of (file, fullname, lineno, endline, complexity).

    `fullname` is radon's qualified name (e.g. `MyClass.my_method`),
    matching what coverage's line ranges will overlap.
    """
    from radon.complexity import cc_visit
    from radon.visitors import Class

    blocks: list[tuple[str, str, int, int, int]] = []
    for py_file in sorted(src_root.rglob("*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            functions = cc_visit(source)
        except SyntaxError:
            continue
        rel_path = _normalize_file_path(str(py_file))
        for fn in functions:
            # `cc_visit` returns Function, Method, AND Class blocks. Class
            # complexity aggregates the class's methods, which we already
            # score individually, so including Class blocks would double-
            # count the same code regions and skew the ranking.
            if isinstance(fn, Class):
                continue
            blocks.append((rel_path, fn.fullname, fn.lineno, fn.endline, fn.complexity))
    return blocks


def _join_coverage(
    coverage_payload: dict,
    blocks: Iterable[tuple[str, str, int, int, int]],
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], int]]:
    """Build coverage_data and complexity_data dicts keyed by (file, function).

    Coverage's "files" keys are normalized to forward slashes for
    cross-platform matching against radon's file paths. Functions whose
    file is missing from the coverage payload, or whose span has no
    executable lines, are emitted with 0% coverage so they remain in the
    ranking (matching the score_tree contract).
    """
    files = {
        _normalize_file_path(path): data
        for path, data in coverage_payload.get("files", {}).items()
    }

    coverage_data: dict[tuple[str, str], float] = {}
    complexity_data: dict[tuple[str, str], int] = {}

    for file_path, function_name, lineno, endline, complexity in blocks:
        key = (file_path, function_name)
        complexity_data[key] = complexity
        file_entry = files.get(file_path)
        if file_entry is None:
            coverage_data[key] = 0.0
            continue
        executed = set(file_entry.get("executed_lines", []))
        missing = set(file_entry.get("missing_lines", []))
        cov = derive_function_coverage(executed, missing, lineno, endline)
        coverage_data[key] = 0.0 if cov is None else cov

    return coverage_data, complexity_data


def _format_markdown(results: list[ScoreResult], generated_at: str) -> str:
    lines = [
        f"# SoulPrint Quality Report: {generated_at}",
        "",
        f"Formula: `{CRAP_FORMULA_TEXT}`",
        "",
        "Top 20 offenders by CRAP score. The full ranked list is in the",
        "sibling `.json` file.",
        "",
        "| Rank | File | Function | Complexity | Coverage % | CRAP |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for rank, r in enumerate(results[:20], start=1):
        lines.append(
            f"| {rank} | `{r.file}` | `{r.function}` | {r.complexity} | "
            f"{r.coverage_pct:.1f} | {r.crap:.2f} |"
        )
    lines.append("")
    return "\n".join(lines)


def _resolve_report_paths(out_dir: Path, today: str) -> tuple[Path, Path]:
    """Pick non-colliding (json, md) report paths for today.

    First run: report-YYYY-MM-DD.{json,md}.
    Subsequent same-day runs: -1, -2, ... suffix appended to both files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    base_json = out_dir / f"report-{today}.json"
    base_md = out_dir / f"report-{today}.md"
    if not base_json.exists() and not base_md.exists():
        return base_json, base_md
    n = 1
    while True:
        candidate_json = out_dir / f"report-{today}-{n}.json"
        candidate_md = out_dir / f"report-{today}-{n}.md"
        if not candidate_json.exists() and not candidate_md.exists():
            return candidate_json, candidate_md
        n += 1


def _build_report(results: list[ScoreResult], generated_at: str) -> dict:
    return {
        "generated_at": generated_at,
        "formula": CRAP_FORMULA_TEXT,
        "results": [asdict(r) for r in results],
    }


def _format_check_summary(verdict: Verdict, thresholds: Thresholds) -> str:
    """Compact human-readable check result. ASCII only."""
    if verdict.passed:
        lines = [
            "soulprint-quality --check: PASS",
            f"Checked top {verdict.checked_count} by CRAP. All within thresholds:",
            f"  max_crap            <= {thresholds.max_crap}",
            f"  max_complexity      <= {thresholds.max_complexity}",
            f"  min_coverage_percent >= {thresholds.min_coverage_percent}",
        ]
        return "\n".join(lines)
    lines = [
        "soulprint-quality --check: FAIL",
        (
            f"{len(verdict.violations)} violation(s) in top "
            f"{verdict.checked_count} by CRAP:"
        ),
    ]
    for v in verdict.violations:
        if v.kind == "min_coverage_percent":
            comparator = ">="
        else:
            comparator = "<="
        lines.append(
            f"  {v.file}::{v.function}: {v.kind} {comparator} "
            f"{v.threshold} violated (actual {v.actual:.2f})"
        )
    lines.append(
        "Run `soulprint-quality` to write the full ranked report under ops/quality/."
    )
    return "\n".join(lines)


def _format_ratchet_diff(old: Thresholds, new: Thresholds) -> str:
    def _line(label: str, old_val, new_val) -> str:
        if old_val == new_val:
            return f"  {label}: unchanged at {old_val}"
        return f"  {label}: {old_val} -> {new_val}"

    return "\n".join(
        [
            _line("max_crap", old.max_crap, new.max_crap),
            _line("max_complexity", old.max_complexity, new.max_complexity),
            _line(
                "min_coverage_percent",
                old.min_coverage_percent,
                new.min_coverage_percent,
            ),
        ]
    )


def _load_thresholds_or_report(
    thresholds_path: Path, missing_hint: str
) -> Thresholds | None:
    """Load thresholds and convert load failures into stderr + None.

    Returns the Thresholds instance on success, or None when the caller
    should exit 1. Centralized so --check and --ratchet handle the same
    failure modes (missing file, malformed JSON, invalid field types,
    field-validation failures, OS-level read errors) uniformly.
    """
    try:
        return load_thresholds(thresholds_path)
    except FileNotFoundError:
        print(
            f"thresholds policy not found at {thresholds_path}.",
            file=sys.stderr,
        )
        print(missing_hint, file=sys.stderr)
        return None
    except json.JSONDecodeError as exc:
        print(
            f"thresholds policy at {thresholds_path} is not valid JSON: {exc}",
            file=sys.stderr,
        )
        return None
    except ValueError as exc:
        # Raised by Thresholds.__post_init__ for negative/out-of-range values
        # and by load_thresholds when a numeric field cannot be coerced.
        print(
            f"thresholds policy at {thresholds_path} is invalid: {exc}",
            file=sys.stderr,
        )
        return None
    except OSError as exc:
        print(
            f"thresholds policy at {thresholds_path} could not be read: {exc}",
            file=sys.stderr,
        )
        return None


def _run_check(
    results: list[ScoreResult], thresholds_path: Path
) -> int:
    thresholds = _load_thresholds_or_report(
        thresholds_path,
        missing_hint="Create one (see src/quality/README.md for the schema) and re-run.",
    )
    if thresholds is None:
        return 1
    verdict = evaluate(results, thresholds)
    print(_format_check_summary(verdict, thresholds))
    return 0 if verdict.passed else 1


def _run_ratchet(
    results: list[ScoreResult], thresholds_path: Path
) -> int:
    current = _load_thresholds_or_report(
        thresholds_path,
        missing_hint="Create one first; --ratchet only tightens existing policies.",
    )
    if current is None:
        return 1
    new = compute_ratchet(results, current)
    if new == current:
        print(
            "soulprint-quality --ratchet: no tighter thresholds possible "
            "(current policy is already at or below measured values)."
        )
        return 0
    save_thresholds(thresholds_path, new)
    print(
        f"soulprint-quality --ratchet: tightened thresholds in {thresholds_path}"
    )
    print(_format_ratchet_diff(current, new))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        import radon  # noqa: F401
    except ImportError:
        print(
            "soulprint-quality requires the 'dev' optional dependencies "
            "(radon, coverage). Install with: pip install -e \".[dev]\"",
            file=sys.stderr,
        )
        return 1

    src_root = Path(args.src)
    if not src_root.exists():
        print(f"Source path not found: {src_root}", file=sys.stderr)
        return 1

    try:
        coverage_payload = _run_coverage(src_root)
    except subprocess.CalledProcessError as exc:
        print(f"coverage subprocess failed: {exc}", file=sys.stderr)
        return 1

    blocks = _collect_complexity(src_root)
    coverage_data, complexity_data = _join_coverage(coverage_payload, blocks)
    results = score_tree(coverage_data, complexity_data)

    if args.check:
        return _run_check(results, Path(args.thresholds))
    if args.ratchet:
        return _run_ratchet(results, Path(args.thresholds))

    today = date.today().isoformat()
    report = _build_report(results, today)

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    out_dir = Path(args.out_dir)
    json_path, md_path = _resolve_report_paths(out_dir, today)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_format_markdown(results, today), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
