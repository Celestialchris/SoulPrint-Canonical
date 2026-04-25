# Template H - Claude Code Prompt Structure, Context Layer Edition v2.1

## Purpose

Template H is the operating contract for implementation prompts sent to Claude Code or another coding agent. Its job is to convert a scoped product or engineering intent into one branch, one prompt, and one merge.

This edition assumes SoulPrint now has a context layer. The context layer carries persistent project doctrine, agent behavior, user preferences, and session continuity. Template H should not repeat that material inside every task prompt. It should point the agent at the correct context boundary, then spend the rest of the prompt on the task-specific facts that decide the diff.

## MODE

Execution mode. This prompt is already the implementation plan.

Do not invoke writing-plans, advisor, subagent-driven-development, or any planning skill.
Do not create a separate plan.
After mandatory reads, begin editing allowed files unless a stop condition is hit.

## Authority rule

Use this order of authority when drafting, reviewing, or executing a Template H prompt:

1. Fresh files uploaded in the current conversation, especially a repo zip, handoff doc, diff, or session log.
2. Current repo files available to the coding agent after `git checkout main && git pull`.
3. Project files explicitly pinned by Chris, such as `CLAUDE.md`, `DECISIONS.md`, `ROADMAP.md`, `context/soul.md`, `context/user.md`, and current specs.
4. GitHub, only when Chris asks for web verification or repo reconciliation.
5. Model memory or chat recollection.

A state capsule is orientation. It is not implementation authority. For code-level prompts, use a fresh repo zip, exact file excerpts, or the coding agent's current checked-out repo as the authority.

Do not convert memory into Verified Facts. If it was not checked against files, it belongs in Assumptions to verify or in a State capsule.

## Context handling doctrine

The old Template H repeated agent disposition, project architecture, branch discipline, and user preferences in every prompt. That created long prompts with diluted signal.

The context layer now carries that information:

- `CLAUDE.md`: project orientation, architecture, workflow defaults, branch and test expectations.
- `context/soul.md`: agent behavior, feedback loop, session continuity protocol, skill routing.
- `context/user.md`: Chris' operating style, prompt expectations, tone, and environment.
- latest `ops/sessions/*.md`: recent work, current branch state, unresolved queue.
- `context/llm-config.md`: only when working on intelligence or local model behavior.
- design doctrine docs: only when working on UI, CSS, visual language, or frontend polish.
- `DECISIONS.md`: before reopening a settled architectural, product, or design question.

Template H prompts should trust the context layer when the target agent is known to auto-read it. Do not duplicate context-layer content inside the task prompt.

### Context preflight vs Mandatory reads

Use two different concepts:

- Context preflight: files the agent must have loaded to understand how to behave.
- Mandatory reads: task-specific files the agent must read to complete this branch.

For Claude Code sessions where `CLAUDE.md` already triggers context loading, do not list `CLAUDE.md`, `context/soul.md`, or `context/user.md` under Mandatory reads. The prompt may include a short Context preflight note instead:

```markdown
## CONTEXT PREFLIGHT

Before this prompt, follow the repo's normal session-start context loading from `CLAUDE.md`, including `context/soul.md`, `context/user.md`, and the latest `ops/sessions/` file.

Do not treat those as task files. The task-specific read list starts below.
```

For agents or environments that do not auto-load the context layer, include the context files in Context preflight, not in Mandatory reads:

```markdown
## CONTEXT PREFLIGHT

Read first, in this order:

1. `CLAUDE.md` - project workflow and branch/test doctrine.
2. `context/soul.md` - agent behavior and session continuity rules.
3. `context/user.md` - Chris' prompt and collaboration preferences.
4. Latest file in `ops/sessions/` - current session continuity.

Then proceed to the task-specific Mandatory reads.
```

This resolves the standing-read conflict: context files are still respected, but the Mandatory reads list remains task-specific.

## Template H structure, strict order

### 0. Context preflight

Use only when needed. Do not let this section become a second prompt. It should establish which context layer the agent has loaded and whether any context file must be read manually.

### 1. Mandatory reads, task-specific only

Name only the files needed for this branch. Keep to 4 to 8 files. If the list grows past 8, split the branch.

```markdown
## MANDATORY READS (do NOT explore the codebase)

Read these files in full before any code changes. Do NOT spawn explore agents. Do NOT scan with Glob or Grep beyond the named files unless a Stop condition instructs you to ask first.

1. `path/to/file.py` - pattern-mirror: existing function or route shape to imitate.
2. `path/to/model.py` - read-to-verify: confirm the model shape still matches Verified Facts.
3. `tests/test_existing_pattern.py` - pattern-mirror: test style and fixture pattern.
```

Each mandatory read must declare why it is included. Use one or both labels:

- Pattern-mirror: read to copy an existing shape.
- Read-to-verify: read to confirm a fact that a prior PR or current spec depends on.

If a file is listed only because the drafter felt nervous, remove it. Nervousness belongs in Assumptions to verify, not in Mandatory reads.

### 2. Verified facts

Verified facts are claims already checked against the authority source. They are not guesses and not instructions.

```markdown
## VERIFIED FACTS (confirmed against `[commit SHA]` / `[uploaded zip name]` / `[branch]`)

If any Verified Fact no longer holds, STOP and ask before continuing.

- `ImportedConversation` is defined in `src/app/models/__init__.py`.
- Schema changes in this repo use `db.create_all()` plus idempotent guards, not Alembic.
- `provider_display_name` is exposed as a Jinja filter, so templates use `{{ provider | provider_display_name }}`.
```

Rules:

- Cite a commit, branch, uploaded zip, or exact file excerpt baseline.
- Prefer structural anchors over line numbers when the file may have moved.
- Use line numbers only when they were verified in the current authority file.
- Never put unchecked memory claims here.
- Never use Verified Facts to freeze implementation strategy. Facts describe what is true, not what should be built.

### 3. Assumptions to verify, optional

Use this only when a claim is plausible but not yet confirmed.

```markdown
## ASSUMPTIONS TO VERIFY

Before editing, verify these against the Mandatory reads. If any fails, STOP and report the corrected shape.

- The existing startup schema guard pattern can be reused for the new table.
- The route helper still returns `(path, error)` rather than raising.
```

If this block has more than 3 assumptions, the drafter has not done enough preflight or the branch is too broad.

### 4. Pre-draft design decisions

Use this in the chat or prompt preamble when the branch contains non-obvious choices.

```markdown
## DESIGN DECISIONS

1. Store file bytes on disk, not in SQLite. Alternative considered: BLOB column. Rejected because SoulPrint's ledger should carry provenance and pointers, while the filesystem carries weight.
2. Add a storage helper before routes. Alternative considered: upload UI first. Rejected because duplicate handling and custody rules need to be proven before product surface.
```

Keep this to 2 or 3 decisions. If there are more, split the task.

### 5. Objective

One sentence. No background essay.

```markdown
## OBJECTIVE

Ship the asset ledger and content-addressed file storage foundation without adding routes, UI, parsing, or export behavior.
```

### 6. Starting state

Describe the current code and product state that matters for this branch.

Include:

- existing models, services, helpers, routes, CLI commands, or tests that are relevant;
- current behavior that must remain unchanged;
- known test count or known baseline if available;
- any current spec that is already canonical.

Do not re-explain SoulPrint's whole architecture.

### 7. Target state

Describe what exists after the branch succeeds.

Include:

- files created;
- files modified;
- columns or tables added;
- helper functions added;
- tests added;
- routes explicitly not added;
- user-visible behavior explicitly unchanged when that matters.

### 8. Step-by-step tasks

Every step must be verifiable. Use small tasks. Avoid broad verbs such as "wire up everything" or "make it robust."

Good task shape:

```markdown
1. Add `Asset`, `ConversationAsset`, and `MessageAsset` models in the existing model module.
2. Add an idempotent startup schema guard if the repo's current pattern requires one.
3. Add `src/app/assets.py` with `sha256_file`, `asset_storage_path`, and `store_asset_file` helpers.
4. Add tests proving identical bytes are stored once and linked twice.
```

Bad task shape:

```markdown
1. Implement attachments.
```

### 9. Scope lock and DO NOT EDIT

Explicitly list what is allowed and what is forbidden.

Always include these in DO NOT EDIT unless the task specifically requires touching them:

- `pyproject.toml`
- `src/app/static/app.css`
- `CHANGELOG.md`
- license files and license key validation logic
- files in `context/`
- files in `ops/`
- files in `.claude/rules/`
- unrelated importers, exporters, intelligence providers, and UI templates
- files owned by another in-flight branch

If a task needs a session log or learned pattern update, make that an explicit final task and carve out only the exact `ops/` path needed.

### 10. Stop conditions

Stop conditions should protect against wrong facts, scope creep, and dangerous migrations. They should not halt on harmless refactors.

Use contract-based stop conditions:

```markdown
## STOP CONDITIONS

STOP and ask before continuing if:

- Any Verified Fact no longer holds.
- Any Assumption to verify fails.
- The repo has no established schema-change pattern for this kind of model addition.
- Implementing this requires storing file bytes in SQLite.
- Implementing this requires adding routes, UI, parsing, or export behavior.
- Tests fail for reasons unrelated to the files touched in this branch.
- The required change expands outside the Scope lock.
```

Avoid count-based stop conditions such as "STOP if there are three helper branches." They are brittle and create false positives.

### 11. Tests and verification

Name exact commands. Include the narrow tests first, then the full suite when appropriate.

```markdown
## TESTS AND VERIFICATION

Run:

```bash
pytest tests/test_asset_storage.py
pytest
```

If the full suite has pre-existing failures, stop and report them without masking them as branch failures.
```

### 12. Git instructions

Always specify the branch and commit message. One prompt, one branch, one merge.

```markdown
## GIT INSTRUCTIONS

```bash
git checkout main
git pull
git checkout -b feat/asset-ledger-storage
# make the scoped changes
pytest tests/test_asset_storage.py
pytest
git add src/app/models/__init__.py src/app/assets.py tests/test_asset_storage.py
git commit -m "feat(assets): add asset ledger storage foundation"
git push -u origin feat/asset-ledger-storage
```

Do not bump version. Do not edit `CHANGELOG.md` unless Chris explicitly asks.
```

### 13. Session log and learned pattern update

For real work prompts, close with the repository's continuity duties.

```markdown
## SESSION CONTINUITY

After the code and tests are complete:

1. If this branch creates a reusable pattern, add a focused note under `ops/learned/`.
2. Write a session log under `ops/sessions/` using the repo's naming convention.
3. Keep both files factual. Do not write a narrative postmortem unless this was a debugging campaign.
```

If the prompt is only a review, planning note, or dry spec, omit this section unless a decision was made.

## State work protocol

Use this when Chris asks "what is current," "what should the next session know," or "write the repo state capsule."

### State capsule

A state capsule is for orientation. It may include:

- current product identity;
- authority rule;
- what was reported as shipped;
- what was verified from files;
- what remains unverified;
- next branch menu;
- what files are needed before a real implementation prompt.

A state capsule must not include code-level Verified Facts unless those facts were checked against current files.

Use this language when appropriate:

```markdown
Treat this capsule as orientation only. For a code-level Template H implementation prompt, use a fresh repo zip, exact file excerpts, or the coding agent's checked-out repo as authority.
```

### Campaign capsule

Use this for multi-PR debugging arcs where the team learned something non-obvious.

Include:

- symptom;
- repro case;
- wrong hypothesis;
- causal chain;
- PR sequence;
- final evidence;
- reusable pattern;
- files future agents should read.

Do not write a campaign capsule for ordinary feature work.

## Attachment and asset prompt doctrine

For Session Attachments and asset work, the branch order is:

1. Asset schema and content-addressed storage service.
2. Conversation-level attachment UI.
3. Message-level attachment UI.
4. Markdown export markers.
5. Obsidian `.assets` bundle plus `manifest.json`.

Do not jump into attachment UI before the storage foundation exists.

For the first asset branch, enforce these constraints:

```markdown
No file bytes in SQLite.
No routes.
No UI.
No parsing.
No Obsidian export changes.
Only ledger metadata plus filesystem custody.
Duplicate file bytes must store once by sha256.
```

This is the bone before nerves and skin.

## Review protocol for generated prompts

No generated implementation prompt is trusted until it passes this gate:

- every file path is verified;
- every Verified Fact is checked against the current authority;
- assumptions are separated from facts;
- stop conditions are contract-based and unlikely to false-positive;
- git commands are sane;
- scope lock includes the standard DO NOT EDIT list;
- the prompt does not repeat context-layer doctrine;
- the final deliverable is an editable `.md` file, a patched `.md` file, or a unified diff.

If modifying an existing prompt or template, provide an applied artifact. Do not end with manual line-insert instructions when a replacement file or diff can be produced.

## Compact skeleton

```markdown
# [Prompt title]

## CONTEXT PREFLIGHT

[Only if needed. State which context layer has been loaded or must be read.]

## MANDATORY READS (do NOT explore the codebase)

1. `path` - pattern-mirror: [why]
2. `path` - read-to-verify: [why]

## VERIFIED FACTS (confirmed against `[authority]`)

If any Verified Fact no longer holds, STOP and ask before continuing.

- [fact]

## ASSUMPTIONS TO VERIFY

- [optional]

## DESIGN DECISIONS

1. [decision, alternative rejected, why]
2. [decision, alternative rejected, why]

## OBJECTIVE

[One sentence.]

## STARTING STATE

[Current relevant state only.]

## TARGET STATE

[Expected diff and behavior.]

## STEP-BY-STEP TASKS

1. [task]
2. [task]
3. [task]

## SCOPE LOCK

In scope:

- `path`

Do NOT edit:

- `pyproject.toml`
- `src/app/static/app.css`
- `CHANGELOG.md`
- license files or license validation logic
- `context/`
- `.claude/rules/`
- unrelated importers/exporters/intelligence/UI files

## STOP CONDITIONS

STOP and ask if:

- Any Verified Fact no longer holds.
- Any Assumption to verify fails.
- The change expands beyond Scope lock.
- Tests fail outside the touched scope.

## TESTS AND VERIFICATION

```bash
pytest [targeted tests]
pytest
```

## GIT INSTRUCTIONS

```bash
git checkout main
git pull
git checkout -b feat/[branch]
# work
pytest [targeted tests]
pytest
git add [explicit files]
git commit -m "feat(scope): message"
git push -u origin feat/[branch]
```

Do not bump version. Do not edit `CHANGELOG.md` unless explicitly requested.

## SESSION CONTINUITY

If code was committed or a decision was made, write the session log. If a reusable pattern appeared, write the focused learned note.
```
