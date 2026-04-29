## Derive per-function coverage from line-level coverage data, in pure code

**From:** April 29, 2026: feat/quality-toolchain-mvp

---

### The bridge problem

`coverage.py` reports executed and missing lines per file. `radon`
reports per-function blocks with `lineno` and `endline`. Joining them
into per-function coverage is one short, pure function. But it is the
non-obvious math at the centre of the SoulPrint quality toolchain.
Getting the denominator wrong skews every score downstream.

```python
def derive_function_coverage(
    executed_lines: set[int],
    missing_lines: set[int],
    lineno: int,
    endline: int,
) -> float | None:
    span = set(range(lineno, endline + 1))
    executed_in_span = executed_lines & span
    missing_in_span = missing_lines & span
    total = len(executed_in_span) + len(missing_in_span)
    if total == 0:
        return None
    return (len(executed_in_span) / total) * 100.0
```

### Why the denominator is `executed + missing`, not `endline - lineno + 1`

Lines that appear in neither `executed_lines` nor `missing_lines` are
non-executable: docstrings, blank lines, `else:` keywords, decorator
prefixes, multi-line argument lists, etc. `coverage.py` excludes them
from its per-file model on purpose. If you divide by the raw line
span you punish docstring-heavy code with phantom uncovered lines and
inflate CRAP for honest functions.

### Why None on an all-non-executable span

A function with no executable lines (only a docstring, only `pass`,
only constants) has no meaningful coverage signal. The CLI emits 0%
for it so it stays visible in the ranking, but the helper itself
returns `None` so the convention is set in one place. Future callers
might choose to skip rather than zero; the helper does not bake in a
policy.

### Test shape that survives recursive pytest

Tests for this helper live in `tests/test_quality_scorer.py` and use
hand-crafted line sets. They never invoke `coverage run -m pytest`
from inside the test suite. The CLI orchestration that does invoke
coverage is left for manual smoke runs; recursive instrumentation is
a documented stop condition because it deadlocks the test session and
inflates run time without adding signal.

### Where this applies

Any tool that joins a per-region static analyzer (radon, mccabe,
custom AST walks) with a per-line dynamic analyzer (coverage,
profilers, runtime traces). The pattern: the join lives in a pure
function with synthetic-fixture tests; the orchestration that
produces both inputs lives in a thin CLI layer.
