"""CLI entrypoint for the SoulPrint quality toolchain.

Runs coverage instrumentation under pytest, computes cyclomatic complexity
with radon, joins per-function coverage and complexity into CRAP scores,
and writes a ranked report in JSON + Markdown.

Reports are timestamped, never overwritten:

    ops/quality/report-YYYY-MM-DD.json    full ranked list
    ops/quality/report-YYYY-MM-DD.md      top 20 offenders, table

If multiple runs happen on the same day, a -N suffix is appended to both.

Exit codes:
    0  healthy run, reports written (or JSON emitted to stdout)
    1  unexpected error (subprocess failure, parse error, etc.)

The MVP does not enforce thresholds. The threshold ratchet is a follow-up
branch (feat/quality-threshold-ratchet); the report shape carries the per-
function score so the ratchet can lock against it without re-deriving.
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

# `radon` is imported lazily inside `_collect_complexity`; `coverage` is
# invoked as a subprocess. Both live in the `dev` optional-dependency group
# rather than runtime requirements, so `main()` checks for availability up
# front and emits a clear install hint instead of letting a deep ImportError
# surface mid-run. See the install hint in `main()`.

CRAP_FORMULA_TEXT = "CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)"


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
        "--json",
        action="store_true",
        help="Emit machine-readable JSON to stdout instead of writing files",
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
        f"# SoulPrint Quality Report — {generated_at}",
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
