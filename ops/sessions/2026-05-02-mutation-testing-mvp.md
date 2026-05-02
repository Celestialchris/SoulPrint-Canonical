## May 2, 2026 — Quality Engine Layer 4 (Mutation Testing MVP)

**Branch:** feat/mutation-testing-mvp
**PR:** (pending)

**What:** Added mutation testing as an opt-in local quality dimension to the
SoulPrint quality toolchain. Installed `mutmut==2.5.1` in the `dev`
optional-dependency group and documented the local mutation testing workflow
in `src/quality/README.md`. No CI wiring, no threshold changes, no application
code modified.

**Decisions:**
- Used mutmut 2.5.1, not 3.x. mutmut 3.x pulls `textual` (a full TUI
  framework) and `libcst` (a concrete syntax tree library) as net-new
  top-level dependencies. This trips the broad-dependency stop condition in the
  prompt. mutmut 2.5.1 requires only `click`, `coverage`, and `pytest` — all
  already present in the `dev` group. Zero net-new top-level packages.
- Pinned to `mutmut==2.5.1`, not `mutmut>=2.5.1`. The 3.x rewrite changed
  the cache format, engine, and dep footprint significantly. An open floor
  would allow a silent upgrade to 3.x. The pin is intentional; bump it
  deliberately when the 3.x value is demonstrated.
- Documentation-only path; no wrapper in `src/quality/cli.py`. mutmut has
  its own clean CLI (`mutmut run --paths-to-mutate`, `mutmut results`,
  `mutmut show`). A wrapper would add ceremony without value for an MVP.
- Scoped to `src/quality/` by default in the README examples. The full repo
  is too large for exploratory mutation without understanding the time cost.
  `src/quality/` has a focused test suite and the smallest blast radius.
- Not wired into CI. Mutation runs execute the full test suite once per
  mutant. CI wiring belongs to a later branch after the signal quality and
  scope are calibrated. The ratchet pattern (track survival rate as a
  baseline, fail CI when it rises) is the natural extension — out of scope
  for this layer.
- `.mutmut-cache` added to `.gitignore`. mutmut 2.x writes this SQLite-backed
  cache file in the working directory; it must not be committed.

**No application code changed.** Only `pyproject.toml` (one line added to dev
deps), `src/quality/README.md` (new section + updated Coming next), and
`.gitignore` (one line added) were edited.

**Verification:**
- `mutmut==2.5.1` dry-run confirmed zero net-new top-level dependencies.
- Quality tests pass: `python -m pytest tests/test_quality_scorer.py tests/test_quality_thresholds.py -v`.
- `soulprint-quality --check` passes; thresholds and scorer unchanged.
- README renders correctly: Mutation Testing section appears between
  Conventions and Coming next; Coming next reflects Layer 4 as shipped.

**Next:**
- Open PR for `feat/mutation-testing-mvp`.
- After merge, run `mutmut run --paths-to-mutate src/quality/` to establish a
  baseline survival rate.
- Future: track mutation score per module in `quality-thresholds.json`
  (v2 schema), wire into CI once scope and noise are calibrated.
