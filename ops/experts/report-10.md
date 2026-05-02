# Expert Report 10: feat/mutation-testing-mvp

Date: 2026-05-02
Branch: feat/mutation-testing-mvp
PR: (pending)
Template H prompt: inline (Uncle Bob Quality Engine Layer 4: Mutation Testing MVP)

## Routing

Section A expert: Code Quality Engineer
Section B stance: Senior Engineer

## Reads consumed during drafting

- `src/quality/README.md` (pattern-mirror, edited): confirmed Layer 3 CI section structure; confirmed "Mutation testing as a third quality dimension" bullet in Coming next that is now promoted to its own section.
- `src/quality/scorer.py` (read-to-verify): pure scoring module, byte-identical to post-PR-#207 state; no changes required.
- `src/quality/cli.py` (read-to-verify): confirmed mutually exclusive mode structure (default / --json / --check / --ratchet); confirmed no wrapper in cli.py is needed for the mutation MVP since mutmut has its own CLI.
- `src/quality/thresholds.py` (read-to-verify): unchanged; no new threshold schema required for MVP.
- `quality-thresholds.json` (read-to-verify): ratcheted values confirmed (max_crap: 510.02, max_complexity: 64); not touched.
- `.github/workflows/tests.yml` (read-to-verify): Layer 3 quality job confirmed present; not touched.
- `pyproject.toml` (pattern-mirror, edited): confirmed dev dep group structure; added `mutmut==2.5.1`.
- `tests/test_quality_scorer.py` and `tests/test_quality_thresholds.py` (pattern-mirror): confirmed test style (unittest.TestCase, no recursive subprocess invocation); no new tests added — documentation-only path requires none.
- `ops/experts/report-09.md` (pattern-mirror): format reference; confirmed Layer 3 state and expert report conventions.
- `ops/sessions/2026-05-02-quality-ci-reporting.md` (read-to-verify): confirmed Layer 3 closeout and "Future: mutation testing" as explicitly next.

## Reads consumed during execution by Claude Code

- All mandatory reads above.
- pip dry-run (mutmut 3.5.0): confirmed textual>=1.0.0 and libcst>=1.8.5 as net-new top-level packages — broad dependency stop condition applies.
- pip dry-run (mutmut 2.5.1): confirmed click, coverage, pytest only — all already in dev group, zero net-new packages.
- `.gitignore` (read-to-verify): confirmed `.mutmut-cache` was not already present; added.
- `ops/experts/` glob (read-only): confirmed next available report number is 10.

## Outcome

- Tests: unchanged. No Python code modified; all quality tests pass.
- New deps: `mutmut==2.5.1` in the `dev` group only. Zero net-new top-level packages.
- Files changed:
  - `pyproject.toml` (edited): added `"mutmut==2.5.1"` to dev deps.
  - `src/quality/README.md` (edited): added `## Mutation Testing` section with running/interpreting/CI-rationale subsections; updated `## Coming next` to reflect Layer 4 as shipped.
  - `.gitignore` (edited): added `.mutmut-cache`.
  - `ops/sessions/2026-05-02-mutation-testing-mvp.md` (created): session log.
  - `ops/experts/report-10.md` (this file).

## Proof required (Code Quality Engineer)

Per the `**Proof required.**` field in `context/experts.md`:

- **No Python application code changed.** `src/quality/scorer.py`, `src/quality/thresholds.py`, and `src/quality/cli.py` are byte-identical to their post-PR-#207 state. No test count delta is possible or expected.
- **No CI wiring.** `.github/workflows/tests.yml` is unchanged. Mutation testing is local-only on this branch.
- **No threshold changes.** `quality-thresholds.json` is unchanged. The `--check` gate is unaffected.
- **mutmut 2.5.1 chosen over 3.x.** mutmut 3.x requires `textual>=1.0.0` and `libcst>=1.8.5` — 4 net-new top-level packages. This is "broad dependency churn" under the prompt's stop condition. mutmut 2.5.1 requires click, coverage, and pytest, all already present in dev. Zero net-new top-level packages.
- **Exact version pin, not a floor.** `mutmut==2.5.1` prevents a silent upgrade to 3.x on the next `pip install`. The 3.x rewrite changed the cache format, engine, and dep footprint; opt into it deliberately.
- **Documentation-only CLI path.** No wrapper added to `src/quality/cli.py`. mutmut's own CLI is clean and sufficient; a wrapper would add ceremony without value for an MVP.
- **Mutation cache gitignored.** `.mutmut-cache` added to `.gitignore`. `mutmut run` writes this SQLite-backed file in the working directory; it does not become a committed artifact.

## Observations

The version pin decision (`mutmut==2.5.1` vs `mutmut>=2.5.1`) deserves a brief note here because it is non-obvious to a future maintainer. The 3.x series is a full rewrite: it swapped the token-based mutation engine for a CST-based one (libcst), replaced the argparse CLI with a Textual TUI, and changed the cache format. These are meaningful improvements if you want the TUI experience or the CST fidelity. They are overhead if you want a scoped `--paths-to-mutate` local run. The pin means a version bump is an intentional decision, not a side effect of `pip install --upgrade`. If 3.x proves its value locally, the upgrade path is one line in pyproject.toml.

The README section deliberately ends with the ratchet-extension note ("track a mutation survival rate baseline in quality-thresholds.json, fail CI when it rises"). This plants the next layer's pattern without committing to it. The CRAP layer showed that a ratchet-based gate is tractable; mutation survival rate is the same shape of problem. The extension requires a v2 threshold schema that can carry a new dimension — that schema work is out of scope for this layer but the conceptual path is already clear.

No `ops/learned/` promotion on this branch. The mutmut 2.x vs 3.x version reasoning is documented in this report and the session log. A single instance does not meet the two-instance bar for learned patterns.
