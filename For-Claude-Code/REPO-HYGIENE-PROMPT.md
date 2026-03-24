# Claude Code Prompt — Repo Hygiene Pass

## MANDATORY READ (primacy zone)
Do NOT spawn explore agents. Do NOT scan the codebase beyond the files listed.

Read these files FIRST:
- README.md
- ROADMAP.md
- docs/README.md
- docs/manifesto.md
- docs/executable-packaging-overview.md (if it exists at docs/ root)
- docs/reference/ideas/future-directions.md (if it exists)

Then run:
```
python -m pytest tests/ --co -q 2>/dev/null | tail -3
find . -name "*.py" -path "*/tests/*" | wc -l
```

## Objective
Single hygiene commit that makes the repo look like a senior engineer maintains it.

## Starting State
- Two empty orphan files at repo root: `answer_trace_list.html` (0 bytes), `test_answer_trace_browser.py` (0 bytes)
- README.md claims "41 test files, 365 test methods" — stale
- README.md Project Status says "10 web surfaces" — undercounts
- README.md Repo Map omits roadmap/, scripts/, .github/
- README.md Quick Start doesn't mention Python 3.12+ or venv
- README.md has no embedded screenshots (files exist in docs/screenshots/)
- README.md Surfaces section doesn't mention the additional routes (continuity, memory detail, etc.)
- docs/manifesto.md is 6 lines (placeholder quality)
- docs/executable-packaging-overview.md may be at docs/ root describing unshipped feature
- docs/reference/ideas/future-directions.md may read like a pasted AI conversation
- ROADMAP.md "Detail References" may link to gitignored files that aren't in the repo
- No SECURITY.md

## Target State
- Orphan files deleted
- README.md has accurate test counts (from the pytest output you just ran)
- README.md has accurate surface/route counts
- README.md Repo Map includes roadmap/, scripts/, .github/
- README.md Quick Start includes Python 3.12+ and venv setup
- README.md has at least one embedded screenshot after the tagline
- README.md has a second screenshot after "What SoulPrint Does"
- README.md Surfaces section has a note about additional routes
- README.md Project Status row updated from "10 web surfaces" to accurate count
- README.md adds a short Security section (local-first, no network calls except BYOK)
- docs/manifesto.md either expanded to 10-15 lines or deleted + removed from docs/README.md
- docs/executable-packaging-overview.md moved to docs/reference/ideas/ with status header
- docs/reference/ideas/future-directions.md rewritten as architecture memo (strip conversational tone)
- ROADMAP.md Detail References only links to files that actually exist in the committed repo
- docs/README.md index updated to reflect all moves

## Allowed Actions
- Delete empty orphan files at repo root
- Edit README.md, ROADMAP.md, docs/README.md
- Move docs/executable-packaging-overview.md to docs/reference/ideas/
- Rewrite docs/reference/ideas/future-directions.md
- Expand or delete docs/manifesto.md
- Create SECURITY.md at repo root (minimal: 10-15 lines)
- Verify doc links resolve to real files

## Forbidden Actions
- Do NOT edit any Python code or tests
- Do NOT edit CLAUDE.md, DECISIONS.md, CONTRIBUTING.md, CHANGELOG.md
- Do NOT edit any file in src/, tests/, or landing/
- Do NOT change the docs/ directory structure beyond the specified move
- Do NOT add new product docs or specs
- Do NOT touch .gitignore or CI configuration

## Stop Conditions
Pause and ask before:
- Deleting any file other than the two specified orphans
- Changing any link in a file not listed in Allowed Actions
- Adding any new directory

## Checkpoints
After each file edit: ✅ [filename — what changed]
Final output:
1. List every file changed/deleted/created
2. The actual test count from pytest
3. The actual route count from grep
4. Confirm all doc links resolve

## Definition of Done
- `git status` shows only the intended changes
- `python -m pytest tests/ -v` passes (no code was changed)
- Every link in README.md and docs/README.md resolves to a real file
- No empty files remain at repo root
- README test counts match the pytest output
