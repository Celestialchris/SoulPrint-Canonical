## May 2, 2026 — Quality Engine Layer 3 (CI reporting)

**Branch:** feat/quality-ci-reporting
**PR:** (pending)

**What:** Wired the existing `soulprint-quality --check` gate into CI as a
standalone `quality` job in `.github/workflows/tests.yml`. The job generates
timestamped report artifacts, enforces threshold policy, and uploads the
report as a GitHub Actions artifact regardless of pass/fail outcome. Updated
`src/quality/README.md` to document CI behavior and promote the "Coming next"
section to reflect Layer 3 as shipped.

**Decisions:**
- Added a separate `quality` job rather than a new step inside the `test`
  matrix job. Running on `ubuntu-latest` only keeps the quality signal on a
  single canonical platform. CRAP scores (coverage + complexity) are OS-
  independent Python analysis, so there is no value in a 3-OS quality matrix.
- The quality job runs the pipeline twice: `soulprint-quality` (default mode,
  writes reports) then `soulprint-quality --check` (gate mode, exits non-zero
  on violation). The two-pass cost (~2x test suite time) is unavoidable given
  the CLI's mutually-exclusive mode design. Modifying cli.py to combine modes
  in one pass would be out of scope for a CI wiring branch.
- No `needs: [test]` dependency. Both jobs run in parallel. If the main test
  suite fails, the quality job's internal `coverage run -m pytest` subprocess
  will also fail, so there is no false-positive "quality passes" risk.
- Artifact upload uses `if: always()` so the report is available for download
  even when the threshold check fails. `if-no-files-found: warn` prevents the
  upload step from failing if the report generation step itself errored.
- Ratchet mode is never run in CI. CI verifies policy; it does not mutate it.
  The README makes this explicit.

**No code changes.** Only `.github/workflows/tests.yml` and
`src/quality/README.md` were edited. No Python files, no tests, no
dependencies.

**Verification:**
- Workflow YAML verified by inspection: two jobs (`test` with matrix,
  `quality` with single ubuntu-latest runner), no shared state, no dependency
  on the existing Claude review workflow.
- `--check` writes no report artifacts (confirmed in cli.py source) so CI
  does not commit generated files or dirty the working tree.
- `if: always()` on the upload step confirmed to upload regardless of prior
  step exit codes.
- Full local test suite not re-run since no Python code changed.
  Existing test suite (1174 tests passing) is unchanged.

**Next:**
- Open PR for `feat/quality-ci-reporting`.
- After merge, the first CI run proves the quality gate is live.
- If `--check` fails on the first CI run, the artifact download shows which
  functions are violating; the remedy is hardening (not widening thresholds).
- Future: per-file or per-function baselines (v2 threshold schema) and
  mutation testing as a third quality dimension.
