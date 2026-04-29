# Expert Report 02: fix/codeql-path-injection-assets

Date: 2026-04-29
Branch: fix/codeql-path-injection-assets
PR: (pending)
Template H prompt: inline (CodeQL py/path-injection at assets.py write sinks)

## Routing

Section A expert: Security Reviewer
Section B stance: Senior Engineer

## Reads consumed during drafting

- `context/experts.md` (project canon): Security Reviewer stanza and the project-canon link list (the four `ops/learned/` security entries plus `SECURITY.md`).
- `context/template-h.md` (project canon): Template H structure and the Expert and stance routing section.
- `ops/learned/static-analyzer-shape-matching.md` (learned pattern): root doctrine. CodeQL grades shape, not logic. The PR #126-#130 (path-injection) and #140-#144 (url-redirection) sagas are the practical evidence.
- `ops/learned/codeql-taint-vs-relative-to.md` (learned pattern): the url-redirection canonical shape inline plus the dismiss-text for the path-injection case. The path-injection canonical shape itself is not duplicated here; the live source is `claude_code_discovery.py:42-53`.
- `src/importers/claude_code_discovery.py:42-55` (pattern-mirror, project canon by reference): the live canonical `os.path.realpath` + `str.startswith` shape that already closed `py/path-injection` elsewhere in this repo. Verbatim source.
- `src/app/assets.py` (read-to-verify): confirmed the sink lines (77 `mkdir`, 78 `write_bytes`), the regex sanitizer at `_sanitize_filename` (lines 158-164), and the `is_relative_to` check at `asset_absolute_path` (line 146). Both are CodeQL-unrecognized but logically correct, so they remain in place; the fix is additive at the sink.
- `.claude/rules/soulprint-testing.md` (project canon): `unittest.TestCase` style under pytest, `make_test_temp_dir` and `release_app_db_handles` fixture patterns, the LIFO cleanup ordering rule.
- `.claude/rules/python-patterns.md` (project canon): `from __future__ import annotations`, PEP 604 unions, the two-lane storage doctrine.
- `tests/temp_helpers.py` (read-to-verify): exact signatures of `make_test_temp_dir` and `release_app_db_handles`. Confirmed `drop_all=True` is the right cleanup posture for tests that call `db.create_all()`.
- `tests/test_importer_contract.py` (pattern-mirror): the bare-Flask + bare-`db` test bootstrap pattern, used here instead of the full app factory.

## Reads consumed during execution by Claude Code

- `src/app/assets.py` (read, edited): added `import os`; extracted `storage_base = _resolve_instance_root(instance_root)` as a local on line 45; inserted the inline canonical-shape sanitizer block before the sinks at lines 86-87 (formerly 77-78).
- `tests/test_assets_path_injection.py` (created): three regression tests covering normal write, symlink-escape rejection, and traversal-filename containment.
- `ops/sessions/april-29-2026-2.md` (created): branch session log.
- `ops/experts/report-02.md` (this file).

## Outcome

- Tests: 1149 → 1152 passing (+3, exactly matching the new file). 1 skipped on Windows due to `os.symlink` permission requirements; the test runs on Linux CI.
- New deps: none.
- Behavior change: `store_asset` raises `ValueError("Asset path must be under storage base")` if the resolved write path escapes the resolved storage base. Under normal use (the existing `_sanitize_filename` regex already strips traversal characters from `original_filename`), the new check never triggers; it is defense-in-depth at the sink and, more importantly, the CodeQL-recognized canonical shape that closes alerts #20 and #21.

## Observations

This branch was a clean Security Reviewer + Senior Engineer fit. The doctrine (`static-analyzer-shape-matching.md` + `codeql-taint-vs-relative-to.md`) and the live canonical shape (`claude_code_discovery.py:42-53`) were sufficient to draft a Template H prompt that executed without scope drift. Two concrete signals the routing worked:

The expert's Out of scope list (CodeQL alerts route here, not to Code Quality Engineer) made the branch boundary obvious from the start. No coverage hardening, no test ergonomics work, no schema changes leaked in. The fix touched exactly one production file and added exactly one test file.

The stance choice (Senior Engineer) was the correct default. There was no surface-level user-facing decision (no Lead Product Designer), no copy decision (no Brand Guardian), no multi-step user path (no UX Strategist). The work was idiomatic, scoped, reversible, and boring-when-possible — the Senior Engineer vocabulary. Any other stance would have been pretense.

One small empirical finding for future expert iterations: `ops/learned/codeql-taint-vs-relative-to.md` is the natural home for the path-injection canonical shape, but currently only the url-redirection shape is inlined there. The path-injection canonical shape lives in production code at `claude_code_discovery.py:42-53` and is referenced from `static-analyzer-shape-matching.md` only narratively. Promoting the shape into the learned doc would compound knowledge for the next path-injection alert. Out of scope for this branch (`ops/learned/` edits would have widened the diff beyond the alert closure), but a candidate follow-up if a third path-injection alert ever fires.
