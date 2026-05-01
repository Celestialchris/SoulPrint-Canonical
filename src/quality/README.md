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
soulprint-quality --check           # evaluate scores against quality-thresholds.json
soulprint-quality --ratchet         # tighten quality-thresholds.json from current scores
soulprint-quality --src src/app/    # scope the scan
soulprint-quality --out-dir /tmp/   # write reports elsewhere
soulprint-quality --thresholds path/to/thresholds.json   # override threshold file
```

`--json`, `--check`, and `--ratchet` are mutually exclusive modes.
Default behavior (write timestamped reports) is unchanged.

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

- `0` healthy run: reports written, JSON emitted, `--check` passed, or `--ratchet` completed.
- `1` unexpected error (subprocess failure, parse error, missing source path, missing thresholds file) **or** `--check` threshold violation.

`--check` is the regression-detection gate: any function in the top-N
that exceeds `max_crap` or `max_complexity`, or falls below
`min_coverage_percent`, fails the run.

## Threshold policy (`quality-thresholds.json`)

The repo-root `quality-thresholds.json` file is the policy layer. It is
inspectable, hand-editable, and version-controlled. The scorer never
mutates it; only `--ratchet` does, and only by tightening.

### Schema

```json
{
  "schema": "soulprint.quality.thresholds.v1",
  "max_crap": 550.0,
  "max_complexity": 70,
  "min_coverage_percent": 0.0,
  "top_n": 20
}
```

- `max_crap`: ceiling. Any function in the top-N with `crap > max_crap` fails `--check`.
- `max_complexity`: ceiling on cyclomatic complexity for the top-N.
- `min_coverage_percent`: floor on per-function coverage for the top-N.
- `top_n`: how many ranked functions are checked. Functions ranked below this are not enforced (they will be when subsequent ratchets pull `top_n` deeper).

Missing fields take permissive defaults so a partial config does not
silently block CI; unknown fields are ignored.

### Check mode

```bash
soulprint-quality --check
```

Runs the full coverage + radon + scoring pipeline, evaluates the top-N
ranked functions against the threshold policy, prints a compact summary,
and exits non-zero on any violation. Writes no report files.

Intended for use as a pre-merge or CI gate. The CI check runs automatically
on every push and pull request; see the **CI** section below.

## CI

The quality check is wired into `.github/workflows/tests.yml` as a
standalone `quality` job that runs on `ubuntu-latest` on every push and
pull request.

The job runs two steps:

1. `soulprint-quality` — runs the full coverage + radon + scoring pipeline
   and writes timestamped reports to `ops/quality/`.
2. `soulprint-quality --check` — re-runs the pipeline, evaluates the
   top-N against `quality-thresholds.json`, and exits non-zero on any
   violation. This step is the CI gate.

Report artifacts (`ops/quality/report-*.md` and `ops/quality/report-*.json`)
are uploaded as a GitHub Actions artifact named `quality-report` regardless
of whether the threshold check passes or fails. Download the artifact from
the Actions run to inspect which functions are violating.

The ratchet is never run in CI. `quality-thresholds.json` is only tightened
manually by running `soulprint-quality --ratchet` locally and committing the
result. CI verifies policy; it does not mutate it.

### Ratchet mode

```bash
soulprint-quality --ratchet
```

Reads the current threshold policy, runs the full scoring pipeline,
computes the strictest possible new policy that the current code still
satisfies, and writes it back to `quality-thresholds.json` if (and only
if) anything tightened.

The ratchet is monotonic: it never loosens. If the code is currently
worse than the policy (`--check` is failing), `--ratchet` will refuse to
tighten the regressing dimension and report no-op for it. The remedy is
to harden the offender, not to widen the threshold.

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

Layer 3 (CI reporting) shipped in `feat/quality-ci-reporting`. Still future:

- Per-file or per-function baselines (current policy is global; once
  too coarse, a v2 schema can carry per-target caps).
- Mutation testing as a third quality dimension (orthogonal to coverage
  and complexity).
- Per-module budgets (Layer 4 policy).
