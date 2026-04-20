# Template H v2 — Claude Code Prompt Structure (Context Layer Edition)

## What changed

The context layer (`CLAUDE.md` + `context/soul.md` + `context/user.md` + `ops/sessions/`) now carries three jobs that Template H v1 was doing by itself:

- **Agent disposition** (surgical, honest about uncertainty, no exploring without permission) → `context/soul.md`
- **Project orientation** (four-layer architecture, provider contract, trust chain) → `CLAUDE.md`
- **Session continuity** (what shipped last, what's queued, current branch) → `ops/sessions/` latest

Template H v1 prompts repeated this every time. With the context layer, that's redundant — and redundant context dilutes the task-specific parts that actually matter. Template H v2 is tighter because the agent arrives already oriented.

**What stays non-negotiable:** the mandatory read block at the top for task-specific files, Verified Facts for hypotheses-turned-confirmed, scope lock with explicit DO NOT EDIT, stop conditions, git instructions with branch specified.

**What gets cut:** re-statements of project architecture, communication style, agent disposition, git workflow preambles. Those live in `context/` now. The agent reads them on entry.

---

## v2 Structure (strict order)

### 1. Mandatory reads — task-specific only

Name only the files the agent needs to complete this task. Do NOT restate the context layer reads here; CLAUDE.md triggers them already on session start.

```
## MANDATORY READS (do NOT explore the codebase)

Read in full before any tool call. Do NOT spawn explore agents. Do NOT scan with Glob or Grep beyond the named files.

1. [file path] — [why: pattern to mirror / data shape / integration point]
2. [file path] — [why]
3. [file path] — [why]
```

Keep to 4-8 files. If the list grows past 8, the task is too big; split it.

### 2. Verified facts — hypotheses confirmed by code-reading

Facts that have been verified against the current codebase. These migrate into the prompt from the drafter's (me or Cowork's) pre-flight reads. When an assumption is stated here, the agent treats it as settled; when it's not listed, the agent must verify.

```
## Verified facts (confirmed against codebase at [commit SHA or branch name])

If any no longer holds, STOP and ask before continuing.

- [Specific fact about file structure, helper signature, existing pattern, or naming convention]
- [Specific fact about what already ships vs what doesn't]
```

This replaces Template H v1's "assumptions to verify." The drafter does the verification before writing the prompt; the agent doesn't waste a session on it. If the drafter can't verify a claim, it goes in a separate **Assumptions to verify** block below Verified Facts, and the agent checks those at the top of the session.

### 3. Objective

One sentence. What this prompt ships.

### 4. Starting state

Current state of the code, keyed to a specific commit or PR. Name existing routes, existing columns, existing helpers. Be specific enough that a diff would be reviewable against this block.

### 5. Target state

What exists after the prompt succeeds. Files created, columns added, routes registered, tests added, counts (where known).

### 6. Step-by-step tasks

Numbered. Each step verifiable. Inline code snippets for patterns the agent should copy; no full implementations unless the snippet IS the specification.

### 7. Scope lock — DO NOT EDIT

Explicit list. Files that are in scope for reading but not for editing get listed here with the word "read only." Files that are adjacent but must not be touched get listed here too.

Always include in DO NOT EDIT unless the task requires them:
- `pyproject.toml`
- `src/app/static/app.css`
- `CHANGELOG.md`
- Any file in `context/`, `ops/`, `.claude/rules/`
- Files explicitly owned by other in-flight prompts

### 8. Stop conditions

When the agent should stop and ask rather than proceeding.

Common ones:
- Any Verified Fact no longer holds
- An assumption in the Assumptions block fails verification
- The migration approach for a schema change has no established pattern and would break existing databases
- Pre-existing test failures surface that aren't in the known-baseline list
- Scope would need to expand past the DO NOT EDIT list

### 9. Git instructions

Explicit branch name. The agent creates the branch from `main` (or from the specified source branch) before any edits. Commit message template provided. Explicit "do NOT push" or "do NOT bump version" when those apply.

```
git checkout main
git pull
git checkout -b feat/[specific-branch-name]
# (do the work)
pytest
git add [explicit file list]
git commit -m "[type](scope): [specific message]"
git push -u origin feat/[specific-branch-name]
gh pr create ...
```

---

## What the agent auto-reads (do not repeat in the prompt)

On session start, CLAUDE.md's triggers tell the agent to read:

- `context/soul.md` — agent disposition, feedback loop, skill routing, session continuity protocol
- `context/user.md` — solo dev profile, preferences, prompt expectations
- Latest `ops/sessions/*.md` — what shipped last, current branch, active specs
- `context/llm-config.md` — when working on intelligence features
- `docs/product/design-doctrine-quiet-archive.md` — when working on UI/CSS
- `DECISIONS.md` — before revisiting a settled question

Template H v2 prompts trust that these reads happen. Don't restate them.

---

## What moves from the prompt to the context layer

Patterns I used to bake into every Template H v1 prompt that now live in `context/`:

| Template H v1 had | v2 location |
|---|---|
| "Use small reversible changes" | `context/user.md` |
| "No em dashes in public copy" | `context/user.md` |
| "Check before proposing" | `context/soul.md` |
| "Flag uncertainty explicitly" | `context/soul.md` |
| Four-layer architecture explanation | `CLAUDE.md` |
| ConversationImporter contract pointer | `CLAUDE.md` |
| Trust chain reminder | `CLAUDE.md` |
| "Template H structure" instruction | `context/user.md` |
| Branch-safety rules | `CLAUDE.md` (Git Workflow section) |
| Test command (`pytest` from repo root) | `CLAUDE.md` |

All of that is gone from the prompt body. The prompt is now ~60% the length of a v1 prompt covering the same task, and the retained content is all task-specific signal.

---

## Example: v1 vs v2 (same task, archive/hide)

**v1 opening (what used to be there):**

> Before any code changes, read EXACTLY these files. Do NOT spawn explore agents. Do NOT scan with Glob or Grep beyond the named files.
>
> 1. `src/app/__init__.py` — for existing delete routes, imported_conversations route, `_sqlite_path_from_uri` helper
> 2. `src/app/models/__init__.py` — model definitions
> 3. ... [6 more files]
> 7. `.claude/rules/python-patterns.md`, `.claude/rules/soulprint-testing.md`, `.claude/rules/brand.md`
>
> [Then: assumptions to verify covering migration pattern, model location, sidebar template, FTS untouched, archive doesn't cascade]

**v2 opening (what replaces it):**

> ## MANDATORY READS (do NOT explore the codebase)
>
> 1. `src/app/__init__.py` — existing delete routes at line 863-974 (pattern to mirror), `_sqlite_path_from_uri` at line 168
> 2. `src/app/models/__init__.py` — ImportedConversation model definition
> 3. `src/app/templates/imported_list.html` — row action pattern (Delete link)
> 4. `src/app/templates/base.html` — sidebar Memory group at line 62-65
> 5. `src/app/templates/imported_delete_confirm.html` — back-link tweak target at line 13
> 6. `tests/test_imported_delete_route.py` — test pattern to mirror
>
> ## Verified facts (confirmed against main at 09ccb02)
>
> - No Alembic or Flask-Migrate. Schema changes use `db.create_all()` at startup + idempotent ALTER guard.
> - `ImportedConversation` is defined in `src/app/models/__init__.py:15`, not a separate module.
> - Sidebar template is `src/app/templates/base.html`; Memory group uses `sidebar_item` macro from `_ui.html`.
> - Existing "What you've discussed" active state uses `request.path.startswith('/imported')` — will need narrowing.
> - FTS search route (`federated_browser`, line 1117) has no `is_archived` filter and should stay that way.

Same information density, half the words. The agent reads `context/soul.md` for "no explore, no scan" and `CLAUDE.md` for where things live; the prompt only has to say what's specific to *this* task.

---

## Drafter checklist

Before handing a v2 prompt to Claude Code, verify:

- [ ] Mandatory reads name 4-8 specific files with "why" per file
- [ ] Verified Facts block exists and each fact is specific (no "check if X exists" — that's an Assumption)
- [ ] Commit SHA or branch name is cited as the verification baseline
- [ ] Objective is one sentence
- [ ] Starting state references line numbers or commit SHAs where possible
- [ ] Target state specifies file paths, column types, route paths, test counts
- [ ] Scope lock lists `pyproject.toml` and `src/app/static/app.css` unless the task requires them
- [ ] Stop conditions include "any Verified Fact no longer holds"
- [ ] Git instructions name an explicit branch prefix matching `feat/`, `fix/`, or `chore/`
- [ ] The prompt does NOT restate agent disposition, architecture, or user preferences

If the prompt repeats anything already in `context/` or `CLAUDE.md`, cut it.
