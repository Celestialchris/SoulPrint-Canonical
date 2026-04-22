## Static analyzers match shapes, not logic

**From:** April 22, 2026 (CodeQL sanitizer saga, sessions april-22-2026-1 through april-22-2026-4)

**Principle**

CodeQL's taint tracker is a pattern matcher, not a logic checker. It doesn't verify that code is safe. It verifies that code looks like a known-safe shape. Those are different things. A sanitizer with correct logic but unrecognized structure is treated as no sanitizer at all.

This is not a bug in CodeQL. A taint tracker that actually reasoned about arbitrary Python would be too slow and too imprecise to run on every PR. So it hard-codes a library of recognized sanitizer shapes and trusts them. Anything outside that library gets flagged, even when strictly stronger than the recognized form.

**Evidence from this repo**

Two separate cases, same underlying lesson.

The path-validation case (PRs #126, #128, #130): `candidate.relative_to(home)` raises `ValueError` on out-of-home paths and is functionally correct. CodeQL does not recognize it. The recognized shape is `os.path.realpath(str(path))` followed by `str.startswith(base + os.sep)`. Three PRs to land the shape fix.

The open-redirect case (PRs #140, #142, #144): a factored `_safe_next()` helper with `urlparse(nxt).netloc/scheme` checks was correct. CodeQL did not follow the helper. Inlining at the sink with a factored `parsed = urlparse(nxt)` and `is_safe` intermediate boolean was also correct. CodeQL did not recognize the factored form. Only the exact canonical shape from CodeQL's own docs closed the alerts: `replace("\\", "")` mutation, inline double `urlparse(nxt).netloc`/`urlparse(nxt).scheme` directly in a guard, early-return pattern, no ternary at sink. Three attempts.

**Practical rule**

When refactoring for a static analyzer, find the analyzer's canonical example and copy it verbatim. Rename variables. Do not improve it. Do not factor it. Do not add defensive extras unless documented as deviation. The analyzer is not grading logic, it is grading shape. Shape compliance is the deliverable.

If logical correctness and analyzer recognition conflict, recognition wins. A correct implementation the analyzer refuses to accept is a problem that costs PRs; a canonical implementation with documented semantic equivalence is a problem that ships.

**Before committing code that touches a known CodeQL sink**

Ask these four questions. Write the answer in the session log if any are "no."

1. Does the analyzer have a canonical example for this sink in its published rule docs?
2. Does my code match that example's structure, not just its logic?
3. If I deviated (stricter check, different idiom), did I do so for a security reason, not an aesthetic one?
4. If the first scan flags my code anyway, will I treat that as a signal to converge further on canonical, not as a reason to dismiss?

Known sink types that trigger CodeQL's py rules in this repo: path validation (`py/path-injection`), URL redirects (`py/url-redirection`), SQL queries (`py/sql-injection`), HTML rendering (`py/reflective-xss`), subprocess calls (`py/command-line-injection`). Each has a canonical pattern. Search CodeQL's docs, copy verbatim.

**Related**

See `codeql-taint-vs-relative-to.md` for the exact canonical shapes for `py/path-injection` and `py/url-redirection` as discovered through these sagas.