# Template H — Claude Code Prompt Structure (Context Layer Edition)

## What changed

The context layer (`CLAUDE.md` + `context/soul.md` + `context/user.md` + `ops/sessions/`) now carries three jobs that Template H v1 was doing by itself:

- **Agent disposition** (surgical, honest about uncertainty, no exploring without permission) → `context/soul.md`
- **Project orientation** (four-layer architecture, provider contract, trust chain) → `CLAUDE.md`
- **Session continuity** (what shipped last, what's queued, current branch) → `ops/sessions/` latest

Template H v1 prompts repeated this every time. With the context layer, that's redundant — and redundant context dilutes the task-specific parts that actually matter. Template H is tighter because the agent arrives already oriented.

**What stays non-negotiable:** the mandatory read block at the top for task-specific files, Verified Facts for hypotheses-turned-confirmed, scope lock with explicit DO NOT EDIT, stop conditions, git instructions with branch specified.

**What gets cut:** re-statements of project architecture, communication style, agent disposition, git workflow preambles. Those live in `context/` now. The agent reads them on entry.

---

## Template-H Structure (strict order)

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

Each mandatory read serves one of two purposes — name which:

- **Pattern-mirror.** "Existing route at lines 394-419 is the structural mirror for the new route." The agent reads to understand what to imitate.
- **Read-to-verify.** "Confirm the shipped `verify_archive()` signature matches the shape in Verified Facts. If it has drifted, STOP." Used when a Verified Fact references a shape locked by a prior PR in the same milestone. The zip or checkpoint the drafter is working from may be one or more merges behind main, so the agent confirms-on-read before trusting the stated shape.

A single file can serve both purposes; say so.

### 2. Verified facts — hypotheses confirmed by code-reading

Facts that have been verified against the current codebase. These migrate into the prompt from the drafter's (me or Cowork's) pre-flight reads. When an assumption is stated here, the agent treats it as settled; when it's not listed, the agent must verify.

```
## Verified facts (confirmed against codebase at [commit SHA or branch name])

If any no longer holds, STOP and ask before continuing.

- [Specific fact about file structure, helper signature, existing pattern, or naming convention]
- [Specific fact about what already ships vs what doesn't]
```

This replaces Template H v1's "assumptions to verify." The drafter does the verification before writing the prompt; the agent doesn't waste a session on it. If the drafter can't verify a claim, it goes in a separate **Assumptions to verify** block below Verified Facts, and the agent checks those at the top of the session.

**Prefer structural anchors over line numbers.** When prior PRs in the same milestone have shipped, line numbers from an older zip are stale. "Between `home()` and `passport_surface()`" survives a merge; "line 392" doesn't. Line-number anchors are fine when the reference file hasn't moved since the drafter's working copy was captured; otherwise, describe by signature or neighborhood.

**Verify template-helper exposure before writing Jinja snippets.** Before the Verified Facts block references any helper used inside a `{% ... %}` or `{{ ... }}`, confirm how it's exposed: Jinja filter (pipe syntax: `{{ x | helper }}`), plain Python function passed via `render_template` (call syntax: `{{ helper(x) }}`), or global template context. These three look similar and fail silently at render time if mistaken for each other. State the exposure explicitly in Verified Facts:

> "`format_timestamp` is a plain Python function (NOT a Jinja filter). Pass it into `render_template` as `format_timestamp=format_timestamp`; call with `{{ format_timestamp(x) }}`. Do NOT use pipe syntax."

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
- Any file in `context/`, `ops/`, `.claude/rules/`
- Files explicitly owned by other in-flight prompts

### 8. Stop conditions

When the agent should stop and ask rather than proceeding.

Common ones:
- Any Verified Fact no longer holds
- An assumption in the Assumptions block fails verification
- A read-to-verify file's shipped shape has drifted from what Verified Facts describes (prior-PR drift)
- A template helper is exposed differently than Verified Facts state (filter vs function vs context global)
- Line-number anchors in Verified Facts no longer point at the described code (file drifted since the drafter's working copy)
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

Template H prompts trust that these reads happen. Don't restate them.

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

## Example: Template H vs Old Template H (same task, archive/hide)

**v1 opening (what used to be there):**

> Before any code changes, read EXACTLY these files. Do NOT spawn explore agents. Do NOT scan with Glob or Grep beyond the named files.
>
> 1. `src/app/__init__.py` — for existing delete routes, imported_conversations route, `_sqlite_path_from_uri` helper
> 2. `src/app/models/__init__.py` — model definitions
> 3. ... [6 more files]
> 7. `.claude/rules/python-patterns.md`, `.claude/rules/soulprint-testing.md`, `.claude/rules/brand.md`
>
> [Then: assumptions to verify covering migration pattern, model location, sidebar template, FTS untouched, archive doesn't cascade]

**Template H opening (what replaces it):**

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

## Drafter authoring practices

These live in the chat thread between drafter and reviewer, not in the .md prompt that Claude Code reads. They exist to catch design errors before the prompt ships.

### Pre-draft design decisions

Before writing the prompt body, state 2-3 non-obvious design decisions the drafter is committing to, with the alternative considered and the reason for rejection. Example shape:

> 1. **Logic lives in `src/verify.py`, not inline in `_cmd_verify`.** Alternative considered: inline in cli.py. Rejected because the web route in the next PR would then duplicate the SQL.
> 2. **Return shape is a dict, not a dataclass.** Alternative considered: `@dataclass(frozen=True) VerifyResult`. Rejected because JSON serialization and CLI formatting both want dict access; dataclass adds conversion ceremony for no safety benefit at this scope.

Three decisions is the typical band; two is fine; four or more usually means the task needs splitting. The point is to make design commitments visible and reversible before they're baked into the prompt body.

### Milestone-internal calibration

When shipping PR N of a multi-PR milestone, read the Claude Code session log from PR N-1 before drafting PR N. Note any details the previous prompt got wrong that CC worked around or flagged: helper exposure mistakes, line-number drift, scope inaccuracies, control-flow assumptions. These are calibration signals. Fold the corrections into the next prompt explicitly:

- As Verified Facts stating the corrected shape
- As Mandatory Reads tagged "read-to-verify" when the shape was set in a prior PR
- As stop conditions when the same failure mode could recur

This is how a milestone gets tighter prompt-to-prompt instead of staying flat.

---

## Reviewer trust gate

No Claude/Codex/GPT-generated implementation prompt is trusted until:

1. every file path is verified against the repo,
2. every "verified fact" is checked against code,
3. every stop condition is tested for false positives,
4. every git command is sanity-checked,
5. assumptions are separated from facts.

A prompt that fails any of these gets sent back to the drafter. This applies regardless of delivery medium — the failure modes don't care whether the prompt arrived as a `.md` file, a code fence, or a paste. The cost of a redraft is one chat round; the cost of letting the agent run on a wrong fact is a half-day of rollback.

False positives in stop conditions deserve specific attention. A stop condition that says "STOP if the service has a third error branch" will halt the agent on a benign refactor; the right shape is a contract-based check ("STOP if `result.error` is no longer typed `str | None`") that holds regardless of how many branches exist. When in doubt, prefer type/shape checks over count/enumeration checks.

---

## Prompt delivery standard

Template-H prompts are implementation artifacts, not disposable chat messages. The final prompt body must live in an editable `.md` file. Inline chat may contain the reasoning, corrections, and a concise diff summary, but not the full implementation prompt as the only deliverable.

Acceptable prompt deliverables:

1. a new `prompt-*.md` file,
2. a repo-local prompt/spec file committed in the appropriate `ops/`, `context/`, or planning path,
3. a unified diff against an existing prompt file when the reviewer only needs a patch.

Unacceptable final deliverables:

- a large code-fenced prompt pasted only into chat,
- manual copy/paste instructions when an editable file can be produced,
- path references left outside backticks, especially paths containing double underscores such as `src/app/__init__.py`.

The reason is practical: `.md` files save chat context, remain editable, preserve underscores and indentation, and can be diffed before Claude Code or Codex touches the repo.

---

## File modification standard

When modifying any prompt, template, rule, checklist, or project document, the assistant must deliver an applied artifact, not only instructions.

Acceptable outputs:

1. a fully patched `.md` file,
2. a unified diff,
3. a replacement file plus a clear note that the original source was read-only.

Unacceptable outputs:

- "Insert this after line X" as the final deliverable,
- manual copy/paste instructions when the assistant has enough context to produce the patched file,
- unverified edits based only on approximate line numbers.

If the assistant truly cannot modify the source file directly, it must say so explicitly and still provide a replacement file or unified diff. Do not transfer clerical merge work back to the reviewer unless the reviewer specifically asks for manual instructions.

---

## Authority hierarchy for generated prompts

Generated prompts are drafts until verified. The repo is the authority; the prompt is only a proposed operating contract.

When a prompt disagrees with code, tests, or git state, trust the codebase and report the correction. Obvious path typos should be corrected silently when the intended file is unambiguous, then called out in the final summary. Non-obvious drift becomes a stop condition.

Use this hierarchy when resolving conflict:

1. current repo state,
2. existing tests and reproducible command output,
3. latest session log or checkpoint,
4. Template-H prompt text,
5. model memory or chat claims.

This prevents a model-written "Verified Fact" from outranking the thing it was supposed to verify.

---

## Drafter checklist

Before handing a Template-H prompt to Claude Code, verify:

- [ ] Mandatory reads name 4-8 specific files with "why" per file
- [ ] Each mandatory read is tagged with its purpose (pattern-mirror or read-to-verify; one file may carry both)
- [ ] Any Verified Fact that references a shape locked by a prior PR in this milestone has the defining file listed in Mandatory Reads as read-to-verify
- [ ] Verified Facts block exists and each fact is specific (no "check if X exists" — that's an Assumption)
- [ ] Commit SHA or branch name is cited as the verification baseline
- [ ] Template helpers used in Jinja snippets have their exposure (filter / function / global) explicitly stated in Verified Facts
- [ ] Line-number anchors are only used when the reference file has not shipped changes since the drafter's working copy; otherwise use structural anchors (function names, block markers)
- [ ] Objective is one sentence
- [ ] Starting state references line numbers or commit SHAs where possible
- [ ] Target state specifies file paths, column types, route paths, test counts
- [ ] Scope lock lists `pyproject.toml` and `src/app/static/app.css` unless the task requires them
- [ ] Stop conditions include "any Verified Fact no longer holds"
- [ ] Stop conditions are contract/shape based, not count/enumeration based, where possible
- [ ] Git instructions name an explicit branch prefix matching `feat/`, `fix/`, or `chore/`
- [ ] Every file path in the prompt body is inside backticks or a code fence (markdown renderers will eat double underscores in `__init__.py` if left bare)
- [ ] The prompt does NOT restate agent disposition, architecture, or user preferences
- [ ] Before the prompt body: drafter has stated 2-3 pre-draft design decisions in chat and gotten reviewer acknowledgment
- [ ] The prompt body itself is delivered as a `.md` file (e.g. `/mnt/user-data/outputs/prompt-*.md` for Claude-drafted prompts, or directly into the repo for manually drafted ones), not as a code fence pasted in chat. Saves chat context, lets the reviewer edit in place, and prevents markdown renderers from eating double underscores in paths like `__init__.py`.
- [ ] The reviewer trust gate has been walked before the prompt is sent: file paths verified, verified facts checked against code, stop conditions tested for false positives, git commands sanity-checked, assumptions separated from facts
- [ ] If modifying a prompt/template/doc file, the deliverable is an applied artifact: fully patched `.md`, unified diff, or replacement file with read-only note; not manual line-insert instructions
- [ ] The prompt treats repo state as authority over model claims; any conflict between prompt text and code/test/git output is resolved in favor of the repo and reported
- [ ] If this is PR N of a multi-PR milestone (N > 1): the PR N-1 session log has been read and any CC corrections are reflected as Verified Facts, read-to-verify Mandatory Reads, or stop conditions

If the prompt repeats anything already in `context/` or `CLAUDE.md`, cut it.
