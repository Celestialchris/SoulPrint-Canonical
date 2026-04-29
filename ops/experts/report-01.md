# Expert Report 01: feat/quality-toolchain-mvp

Date: 2026-04-29
Branch: feat/quality-toolchain-mvp
PR: #192
Template H prompt: inline (Quality Toolchain MVP / CRAP scorer)

## Routing

Section A expert: Code Quality Engineer
Section B stance: Senior Engineer

## Reads consumed during drafting

- `context/experts.md` (project canon) — routing doctrine, Code Quality Engineer stanza, Senior Engineer stance, expert-report format and numbering rules.
- `context/template-h.md` (project canon) — Template H structure, mandatory-reads block placement, scope-lock conventions, SESSION CONTINUITY closing tasks.
- `.claude/rules/python-patterns.md` (project canon) — `from __future__ import annotations`, PEP 604 unions, `@dataclass(slots=True, frozen=True)`, no async in Flask, the two-lane storage pattern (not load-bearing here but read in full).
- `.claude/rules/soulprint-testing.md` (project canon) — `unittest.TestCase` style under pytest, test naming, no shared `app` across tests, no exact-BM25 asserts (the assertion-stability pattern that informed the float comparisons here).
- `pyproject.toml` (read-to-verify) — current `[project.optional-dependencies]` and `[project.scripts]` shape; verified `soulprint-quality` was not taken.
- `src/passport/cli.py` (pattern-mirror) — argparse shape, exit-code convention, `--json` flag pattern.

## Reads consumed during execution by Claude Code

- `pyproject.toml` (read, edited): added `coverage>=7.0` and `radon>=6.0` to `dev`, added `soulprint-quality` to `[project.scripts]`.
- `.gitignore` (read, edited): added `coverage.json`, `ops/quality/report-*.json`, `ops/quality/report-*.md`.
- `.github/workflows/tests.yml` (read): confirmed CI does not invoke coverage; the Verified Fact gap was real.
- `src/quality/__init__.py` (created, empty namespace marker).
- `src/quality/scorer.py` (created): `compute_crap`, `derive_function_coverage`, `score_tree`, `ScoreResult` dataclass.
- `src/quality/cli.py` (created): subprocess orchestration for coverage, library use of radon, JSON+Markdown report writers, `--json` stdout mode.
- `src/quality/README.md` (created): formula, citation, CLI usage, report shape, "Coming next" pointer to the threshold ratchet.
- `tests/test_quality_scorer.py` (created): 12 tests across 3 `unittest.TestCase` classes.
- `ops/quality/.gitkeep` (created).
- `ops/learned/per-function-coverage-from-line-data.md` (created).
- `ops/sessions/april-29-2026-1.md` (created).
- `ops/experts/report-01.md` (this file).

## Outcome

- Tests: 1138 → 1150 passing (+12, exactly matching the new test file).
- New deps: `coverage>=7.0` and `radon>=6.0` in the `dev` optional-dependency group.
- Behavior change: a new `soulprint-quality` console script ranks functions in `src/` by CRAP score and writes timestamped reports under `ops/quality/`. No existing behavior altered.

## Observations

The Verified Fact about `coverage.py` already being in `pyproject.toml` (used in CI) was wrong. It was named in `context/experts.md` as a Code Quality Engineer internal dependency, but no entry existed in `pyproject.toml`'s `dev` extras and `.github/workflows/tests.yml` runs plain `python -m pytest tests/ -v` with no coverage step. The drafter mistook routing-doctrine intent for installed reality. Both `coverage>=7.0` and `radon>=6.0` were added as Step 1 of this branch instead of being assumed. This is the first Section A + Section B run after the routing doctrine landed (PR #191), and the gap is the empirical record of the drafter-vs-reality delta. Future Template H prompts should treat any "already in" claim as a verifiable assertion, not a precondition.

A second observation: the routing-doctrine PR had to land before this one because `context/experts.md` was untracked at session start. The split into two branches (`docs/experts-routing-doctrine` then `feat/quality-toolchain-mvp`) was the correct call; without the routing doctrine on `main` first, this report would have nothing canonical to point at.
