# SoulPrint Quality Toolchain

A small, owned tool that ranks Python functions in `src/` by CRAP score:
the joint signal of cyclomatic complexity and test coverage. The output
is a ranked list of where hardening branches can spend effort with the
most measurable return.

## Formula

```
CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)
```

`comp(m)` is the cyclomatic complexity of function `m` (radon).
`cov(m)` is its line coverage as a percentage (coverage.py, derived to
the function's line span). When coverage is 100% the second term is
zero and the score collapses to `comp(m)`; uncovered complexity
compounds quickly.

The formula is the canonical CRAP score from crap4j (Alberto Savoia and
Bob Evans, 2007). SoulPrint does not modify it.

## Wiring

Two upstream tools, both in the `dev` optional-dependency group:

- `coverage>=7.0` for line-level coverage data
- `radon>=6.0` for per-function cyclomatic complexity

The toolchain wraps them; it does not reimplement either. Coverage is
invoked as a subprocess (`python -m coverage run -m pytest tests/`,
then `coverage json`). Radon is used as a Python library
(`radon.complexity.cc_visit`).

## CLI

```bash
soulprint-quality                   # write ops/quality/report-YYYY-MM-DD.{json,md}
soulprint-quality --json            # emit JSON to stdout, write nothing
soulprint-quality --src src/app/    # scope the scan
soulprint-quality --out-dir /tmp/   # write reports elsewhere
```

Reports are timestamped, never overwritten. Multiple same-day runs get
a `-N` suffix on both files.

### Report shape

`report-YYYY-MM-DD.json`:

```json
{
  "generated_at": "2026-04-29",
  "formula": "CRAP(m) = comp(m)^2 * (1 - cov(m)/100)^3 + comp(m)",
  "results": [
    {
      "file": "src/foo.py",
      "function": "Bar.do_thing",
      "complexity": 12,
      "coverage_pct": 33.3,
      "crap": 156.36
    }
  ]
}
```

`report-YYYY-MM-DD.md`: the top 20 offenders only, as a Markdown table,
for human triage. The full ranked list lives in the JSON sibling.

### Exit codes

- `0` healthy run; reports written or JSON emitted.
- `1` unexpected error (subprocess failure, parse error, missing source path).

The MVP does not have a regression-detection exit code. That arrives in
the threshold-ratchet branch (see Coming next).

## Conventions

- Per-function coverage is derived by intersecting coverage.py's
  per-file `executed_lines` and `missing_lines` with each radon block's
  `lineno..endline` span. Lines outside both sets are non-executable
  (docstrings, blank lines) and excluded from the denominator.
- Functions whose span has no executable lines, or whose file is absent
  from the coverage payload, are emitted with 0% coverage. This keeps
  unreached code visible in the ranking instead of silently dropped.
- File paths are normalized to forward slashes so reports are stable
  across Windows and Linux runs.

## Coming next

The threshold ratchet (`feat/quality-threshold-ratchet`, planned) adds:

- A locked baseline at `quality-thresholds.json`, capturing per-file or
  per-function score caps.
- A `--check` mode that exits non-zero on regression past the lock.
- A `--ratchet` mode that lowers the lock after a hardening branch.

Until then, the MVP only reports. Threshold enforcement, mutation
testing, and per-module budgets are deliberately out of scope here.
