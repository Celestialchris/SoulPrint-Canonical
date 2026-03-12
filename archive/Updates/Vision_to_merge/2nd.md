Good correction. The order was fine, but the prompts still left too much interpretation room.

So here is the stronger version: **exactly what should be changed**, file by file, with replacement text and explicit deletions. I’m treating your new `VISUAL-DIRECTION.MD` and `2 layer meta prompt.md` as already-correct baselines, because they cleanly establish the separation between doctrine and aesthetic prompting and explicitly ban using style to alter architecture, provenance, or workflow.  

# What changes now

There are four cleanup moves.

## Clean-repo Step 1 — Reshape the root and stratify docs

### What to change

Move these files out of root:

* `POSITIONING.md` → `docs/product/positioning.md`
* `CONTEXT.md` → `docs/product/context.md`
* `MEM0_BOUNDARY_DESIGN.md` → `docs/architecture/mem0-boundary.md`
* `SETUP.md` → `docs/getting-started.md`
* `REPO_AUDIT.md` → `docs/reference/history/repo-audit-baseline.md`
* `REPAIR_NOTES.md` → `docs/reference/history/repair-notes.md`
* `Additional Step.md` → `docs/reference/ideas/future-directions.md`

Create these new root files:

* `LICENSE`
* `CONTRIBUTING.md`
* `ROADMAP.md`
* `CHANGELOG.md`

Keep at root:

* `README.md`
* `CLAUDE.md`
* `requirements*.txt`
* `.github/`
* `src/`
* `tests/`
* `sample_data/`
* `docs/`

### Exact docs structure to end with

```text
docs/
  getting-started.md
  product/
    positioning.md
    context.md
  architecture/
    answering-boundary.md
    mem0-boundary.md
    retrieval-surface.md
  specs/
    memory-passport-spec.md
  reference/
    history/
      repo-audit-baseline.md
      repair-notes.md
      project-status-2026-03-09.md
    ideas/
      future-directions.md
```

### Exact content for `CONTRIBUTING.md`

```md
# Contributing

SoulPrint is a local-first memory continuity product. Contributions should preserve clarity, provenance, and explicit boundaries.

## Development rules

- Run the test suite before opening a PR.
- Do not mutate derived data into canonical records.
- Do not blur native and imported lanes without an explicit architectural decision.
- Do not add heavy dependencies without a clear product reason.
- Do not add new routes or UI surfaces without tests.
- Prefer small, reversible changes over broad refactors.

## Local setup

See `docs/getting-started.md`.

## Pull requests

A good PR should include:

- a short summary of what changed
- the files touched
- the main risk
- test results
- screenshots for UI changes when relevant

## Out of bounds unless explicitly requested

- vector databases
- hosted sync
- mem0 activation
- speculative agent orchestration
- portability / USB-style storage features
```

### Exact content for `CHANGELOG.md`

```md
# Changelog

All notable changes to SoulPrint will be documented in this file.

## Unreleased

### Added
- Shared web app shell and unified visual grammar
- Transcript explorer with TOC and minimap rail
- Federated cross-lane retrieval
- Grounded answering with answer traces
- Citation-to-record handoff
- Memory Passport export
- Memory Passport validation
- Three-provider import support for ChatGPT, Claude, and Gemini

### Changed
- Product doctrine clarified around canonical ledger vs derived layers
- README and docs being aligned to current repo truth
- Visual styling guidance separated from doctrine guidance

### Fixed
- Template duplication issues in imported explorer
- Windows-oriented test hygiene for temp artifacts
```

### Exact content for `ROADMAP.md`

This is the cleaned version, with **portable-dir / USB implementation removed**.

```md
# SoulPrint Roadmap

SoulPrint is a local-first memory continuity system for AI users.

The current priority is not more capability breadth.  
The current priority is product coherence.

## Current active sequence

### 1. Repo face cleanup
Make the public repository look intentional, trustworthy, and professional.

### 2. README and docs truth alignment
Update product-facing and developer-facing docs so they reflect the actual current repo state.

### 3. Canonical Workspace
Turn `/` into the center-of-gravity workspace for the existing product loop:
Import → Inspect → Search → Answer → Export / Validate

### 4. Import lifecycle UI
Surface the existing importer pipeline in the web app.

### 5. In-app Ask
Make grounded answering and answer traces a first-class in-app experience.

### 6. Passport surface
Make Memory Passport export/validation more visible and understandable inside the product.

## Deferred sequence

### 7. Derived intelligence
Add provenance-bound summaries, notes, and later higher-order derived artifacts.

### 8. Product polish
Responsive improvements, onboarding, empty states, loading/error states, and UX refinement.

### 9. Growth experiments
Shareable summary surfaces, public launch assets, and other non-core presentation work.

## Explicitly deferred

The following are not current implementation priorities:

- mem0 activation
- hosted sync
- vector databases / RAG expansion
- mobile app development
- local-dir portability / USB-style packaging / “capsule” implementation

## Governing rule

Every step must make SoulPrint feel more like one calm, trustworthy product.

If a change adds another subsystem without improving coherence, it is not ready.
```

---

## Clean-repo Step 2 — Rewrite README and remove the portability ghost

This is the biggest public-facing correction.

### What to remove everywhere in README and front-door docs

Delete language like:

* “portable mode”
* “USB memory”
* “carry it anywhere”
* “capsule”
* “portable directory”
* “virtual USB”
* “all state under one carryable folder”
* “memory on a stick”

Replace with:

* continuity
* exportability
* interoperability
* local ownership
* Memory Passport
* provenance-preserving export
* validation
* inspectable local continuity

### Exact replacement `README.md`

```md
# SoulPrint

Your AI conversations are scattered everywhere. SoulPrint brings them home.

SoulPrint is a local-first memory continuity system for AI users. It lets you import conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with explicit provenance, search and browse it fluidly, answer from it conservatively, and export it as a Memory Passport.

SoulPrint is not a hosted SaaS product.  
It is not a mem0 clone.  
It is not an AI dashboard.

## Product loop

**Import → Inspect → Search → Answer → Export / Validate**

## What works today

- three-provider import with auto-detection
- canonical SQLite ledger with explicit native and imported lanes
- transcript explorer with prompt-level TOC and minimap rail
- federated cross-lane retrieval
- grounded local answering with citation provenance
- answer trace audit residue
- citation-to-record handoff
- Memory Passport export
- Memory Passport validation
- shared app shell with calm, low-clutter visual grammar

## Main surfaces

| Route | Purpose |
|---|---|
| `/` | Workspace / continuity overview |
| `/chats` | Native memory lane |
| `/imported` | Imported conversation lane |
| `/imported/<id>/explorer` | Transcript explorer |
| `/federated` | Cross-lane retrieval |
| `/answer-traces` | Derived answer audit surface |

## What SoulPrint protects

SoulPrint is built around a simple rule:

- canonical local records remain authoritative
- browsing and retrieval are read-only over canonical records
- answers and traces are derived, never canonical
- exportability must preserve provenance, not erase it

## Quickstart

See `docs/getting-started.md`.

## Repo map

- `src/app/` — web app and browser surfaces
- `src/importers/` — provider-aware import adapters and persistence
- `src/retrieval/` — federated read-only retrieval
- `src/answering/` — grounded answering and traces
- `src/passport/` — export and validation
- `tests/` — unit and route coverage
- `sample_data/` — import fixtures
- `docs/` — product doctrine, architecture, and reference material

## Current priority

The next priority is not more breadth.

The next priority is product coherence:
make importing, inspecting, searching, answering, and export/validation feel like one calm, trustworthy local workflow.

## Contributing

See `CONTRIBUTING.md`.

## License

Apache-2.0
```

### Exact content for `docs/getting-started.md`

````md
# Getting Started

## Minimal setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-minimal.txt
````

## Run the app

```bash
python -m src.run
```

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Import sample data

Use the existing importer CLI with a sample fixture:

```bash
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db
```

## Export a Memory Passport

```bash
python -m src.passport.cli export --db instance/soulprint.db
```

## Validate a Memory Passport

```bash
python -m src.passport.cli validate <passport-path>
```

## Notes

* SoulPrint is local-first.
* The canonical ledger remains authoritative.
* Imported and native lanes remain explicit unless composed read-only.
* Derived layers must never overwrite canonical truth.

````

---

## Clean-repo Step 3 — Split doctrine from style and quarantine algorithmic-art

Your uploaded `VISUAL-DIRECTION.MD` and `2 layer meta prompt.md` are already right in spirit. The move now is to **canonize them in the repo and remove algorithmic-art contamination from execution documents**. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}

### What to create

Keep or create:

- `docs/product/execution-guide.md` → canonical implementation/governance guide
- `docs/product/visual-direction.md` → aesthetic layer only

### Exact content for `docs/product/visual-direction.md`

Use this as the final version:

```md
# SoulPrint Visual Direction

Doctrine files are not aesthetic playgrounds.

Do not alter product architecture, lane honesty, provenance display rules, or workflow structure in the name of style.

Use aesthetic prompting only for:

- visual rhythm
- gradients
- subtle motion
- empty-state warmth
- brand atmosphere
- future summary / landing pages
- tasteful micro-interactions

Never use aesthetic prompting to redefine:

- route structure
- information architecture
- transcript explorer behavior
- import UX logic
- answer-trace trust model
- canonical vs derived boundaries

## UI style rules

SoulPrint should feel:

- calm
- fluid
- Apple-like
- low-clutter
- readable
- warm
- continuity-first
- obvious to navigate

Avoid:

- dashboard bloat
- metrics theater
- noisy admin-panel energy
- ornamental AI gimmicks

## algorithmic-art rule

Algorithmic-art may be used only as a secondary aesthetic lens.

Use it for:

- restrained generative texture
- subtle background systems
- motion language
- gradient rhythm
- premium atmosphere

Do not use it to drive:

- route structure
- layout doctrine
- provenance rules
- workflow logic
- product architecture

Treat it as lighting and atmosphere, not as the house.
````

### Exact content for `docs/product/execution-guide.md`

This is the cleaned, active version:

```md
# SoulPrint Execution Guide

## Source hierarchy

1. current repo truth first
2. corrected doctrine notes second
3. older execution-guide ideas third

## Product identity

SoulPrint is a local-first memory continuity system for AI users.

Its job is to let a person import AI conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with explicit provenance, search and browse it fluidly, answer from it conservatively, and export/validate it as a Memory Passport.

## Core rules

- canonical SQLite-backed local ledger remains authoritative
- native and imported lanes remain explicit unless composed read-only
- browsing and retrieval are read-only
- answering and traces are derived and non-canonical
- optional systems must never replace canonical truth
- no route sprawl
- no dashboard bloat
- no fake web execution for flows that are still CLI-only
- no slop

## Terminology correction

Do not use:

- portable mode
- USB memory
- carry it anywhere
- capsule
- local-dir portability

Use instead:

- continuity
- exportability
- interoperability
- local ownership

Memory Passport is a provenance-and-validation construct, not a physical portability metaphor.

## Current priority

The current problem is not missing capability breadth.

The current problem is product coherence.

## Active sequence

1. repo face cleanup
2. README and docs truth alignment
3. canonical workspace on `/`
4. import lifecycle UI
5. in-app Ask
6. passport surface

## Deferred sequence

- derived intelligence
- polish and onboarding
- growth experiments

## Execution mode

- one active task at a time
- one bounded merge at a time
- do not propose future phases unless asked
- if a task is out of scope, leave it alone
```

---

## Clean-repo Step 4 — Narrow the active roadmap into merge-sized work

This is where you stop vague sequencing and give Codex exact change sets.

### Phase-now file to add

Create `EXECUTION_GUIDE_NOW.md` or make it a section in the execution guide.

### Exact content

```md
# SoulPrint — Current Active Stretch

## Active phase

Coherence and control.

## Current active tasks

### 1. Repo face cleanup
Clean root structure, stratify docs, add missing public-repo signals.

### 2. README and docs alignment
Make public docs reflect actual current repo truth and remove the portability ghost.

### 3. Canonical Workspace
Turn `/` into the center-of-gravity workspace.

### 4. Import lifecycle UI
Surface the existing importer pipeline in the app.

## Frozen for now

- in-app Ask
- derived intelligence
- responsive polish
- growth experiments
- mem0 activation
- portability / USB-style implementation ideas

## Merge rule

Do not begin the next task until the current one is merged, verified, and accepted.
```

---

# The exact Codex prompts with actual changes

Now the important part: these are no longer “clean the repo” abstractions. These include the actual file content to create or replace.

## Prompt 1 — Repo face cleanup with concrete outputs

```text
Work from current main as source of truth.

Task:
Clean the public repo face and stratify documentation without changing runtime behavior.

Do exactly this:

1. Add LICENSE with Apache-2.0 full text.

2. Create CONTRIBUTING.md with this content:

[PASTE THE CONTRIBUTING.md TEXT PROVIDED ABOVE]

3. Create CHANGELOG.md with this content:

[PASTE THE CHANGELOG.md TEXT PROVIDED ABOVE]

4. Create ROADMAP.md with this content:

[PASTE THE ROADMAP.md TEXT PROVIDED ABOVE]

5. Create .github/workflows/tests.yml that:
- runs on push and pull_request
- uses Python 3.12
- installs requirements-minimal.txt
- runs:
  python -m unittest discover -s tests -p "test_*.py"

6. Add issue templates:
- .github/ISSUE_TEMPLATE/bug_report.md
- .github/ISSUE_TEMPLATE/feature_request.md

7. Move these root markdown files:
- POSITIONING.md → docs/product/positioning.md
- CONTEXT.md → docs/product/context.md
- MEM0_BOUNDARY_DESIGN.md → docs/architecture/mem0-boundary.md
- SETUP.md → docs/getting-started.md
- REPO_AUDIT.md → docs/reference/history/repo-audit-baseline.md
- REPAIR_NOTES.md → docs/reference/history/repair-notes.md
- Additional Step.md → docs/reference/ideas/future-directions.md

8. Preserve README.md and CLAUDE.md at root.

9. Update links after moving files.

Out of scope:
- no app behavior changes
- no route changes
- no schema changes
- no runtime dependency expansion

Definition of done:
- root looks intentional and professional
- docs are stratified by role
- CI runs
- runtime behavior unchanged
```

## Prompt 2 — README/docs truth alignment with exact replacement text

```text
Work from current repo truth first, then corrected doctrine notes.

Task:
Rewrite public-facing docs so they reflect the actual current product and remove the portability ghost.

Do exactly this:

1. Replace README.md with:

[PASTE THE README.md TEXT PROVIDED ABOVE]

2. Replace docs/getting-started.md with:

[PASTE THE docs/getting-started.md TEXT PROVIDED ABOVE]

3. Sweep product-facing docs and remove or replace phrases like:
- portable mode
- USB memory
- carry it anywhere
- capsule
- local-dir portability
- virtual USB

4. Replace those with:
- continuity
- exportability
- interoperability
- local ownership
- provenance-preserving export
- Memory Passport validation

5. Preserve Memory Passport as a core product concept.
6. Do not change runtime code.

Definition of done:
- public docs match actual repo truth
- portable-dir / USB interpretation is gone
- Memory Passport remains intact
```

## Prompt 3 — Split canon from style with exact file content

```text
Task:
Separate doctrine from aesthetic prompting and quarantine algorithmic-art to a style-only layer.

Do exactly this:

1. Create docs/product/visual-direction.md with this content:

[PASTE THE visual-direction.md TEXT PROVIDED ABOVE]

2. Create docs/product/execution-guide.md with this content:

[PASTE THE execution-guide.md TEXT PROVIDED ABOVE]

3. Remove algorithmic-art references from any canonical execution/planning document.
4. Keep algorithmic-art only as a downstream aesthetic lens.
5. Do not change runtime behavior.

Definition of done:
- execution guide is clean product canon
- visual direction is separate
- algorithmic-art is style-only
```

## Prompt 4 — Narrow the active roadmap and add a “now” guide

```text
Task:
Create a strict current-phase guide that keeps SoulPrint under control.

Do exactly this:

1. Create EXECUTION_GUIDE_NOW.md with this content:

[PASTE THE EXECUTION_GUIDE_NOW.md TEXT PROVIDED ABOVE]

2. Make sure the active sequence is only:
- repo face cleanup
- README/docs alignment
- canonical workspace on /
- import lifecycle UI

3. Keep these frozen:
- in-app Ask
- derived intelligence
- polish / onboarding
- growth experiments
- mem0 activation
- portability / USB-style implementation

4. Do not add future-phase planning beyond that.

Definition of done:
- there is one active stretch
- tasks are merge-sized
- future drift is frozen
```

---

# My final read

You were right to push back.

The earlier cleanup prompts gave the order, but not enough **substance**. That leaves too much creative discretion in the hands of the coding agent, and that is exactly how projects drift from “executed” into “interpreted.”

Now the change set is explicit:

* what files move
* what new files appear
* what README becomes
* what ROADMAP becomes
* what VISUAL DIRECTION becomes
* what EXECUTION GUIDE becomes
* what terminology dies
* what terminology survives

And the key correction remains:

**remove the portable-dir / USB implementation idea from the active product language and planning.**
Keep Memory Passport.
Keep continuity.
Keep exportability.
Drop the storage-theater metaphor.

Your uploaded `VISUAL-DIRECTION.MD` and `2 layer meta prompt.md` were already the right instinct. This just turns that instinct into clean, enforceable repo structure and Codex-ready instructions.  

The next best move is simple:
run Prompt 1 first, merge it, then Prompt 2. After those two, the repo will already feel dramatically more controlled.
