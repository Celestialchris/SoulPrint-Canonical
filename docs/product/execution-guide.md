# SoulPrint — Final Execution Guide v3

*Merged from: original execution guide, ChatGPT editorial corrections, governance reset, terminology corrections, vision file exact contents, and two-layer prompt architecture.*

---

## Source Hierarchy

1. Current repo truth first
2. Corrected doctrine notes second
3. Older execution-guide ideas third

---

## Product Identity

SoulPrint is a local-first memory continuity system for AI users.

Its job is to let a person import AI conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with explicit provenance, search and browse it fluidly, answer from it conservatively, and export/validate it as a Memory Passport.

SoulPrint is not a hosted SaaS product. It is not a mem0 clone. It is not an AI dashboard.

---

## Core Diagnosis

The code kept moving. The presentation did not consolidate at the same speed.

The repo's problem is not broken architecture — it is unstratified truth. Nine markdown files compete at root level. Historical docs still describe a Milestone-1 baseline, and active doctrine can still lag product reality if not maintained. The product is real; the front door must continue reflecting it.

**The current problem is not missing capability breadth. The current problem is product coherence.**

---

## Terminology Rules (enforced everywhere)

**Remove from all docs, prompts, and UI copy:**
- portable mode
- USB memory
- carry it anywhere
- capsule
- local-dir portability
- virtual USB
- portable directory
- memory on a stick

**Replace with:**
- continuity
- exportability
- interoperability
- local ownership
- provenance-preserving export
- Memory Passport (as a provenance-and-validation construct, not a physical transport metaphor)

The governing correction: SoulPrint is not about carrying memory like an object. It is about **preventing memory exile**.

---

## Active Execution Sequence

### Phase 1 — Repo face cleanup
Clean the public repo face without touching runtime behavior.

**Create:**

| File | Content |
|------|---------|
| `LICENSE` | Apache-2.0 full text |
| `CONTRIBUTING.md` | Setup, test rules, PR guide, anti-drift rules, out-of-bounds list |
| `ROADMAP.md` | Active sequence + deferred sequence + explicitly deferred items |
| `CHANGELOG.md` | Backfilled from git history through current state |
| `.github/workflows/tests.yml` | Python 3.12, install requirements-minimal, run tests |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Standard template |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Standard template |

**Move out of root:**

| Source | Destination |
|--------|-------------|
| `POSITIONING.md` | `docs/product/positioning.md` |
| `CONTEXT.md` | `docs/product/context.md` |
| `MEM0_BOUNDARY_DESIGN.md` | `docs/architecture/mem0-boundary.md` |
| `SETUP.md` | `docs/getting-started.md` |
| `REPO_AUDIT.md` | `docs/reference/history/repo-audit-baseline.md` |
| `REPAIR_NOTES.md` | `docs/reference/history/repair-notes.md` |
| `Additional Step.md` | `docs/reference/ideas/future-directions.md` |

**Keep at root:** `README.md`, `CLAUDE.md`

**Definition of done:** root looks intentional, docs stratified by role, CI runs, runtime unchanged.

---

### Phase 2 — README and docs truth alignment
Rewrite public-facing docs to reflect actual current product. Remove the portability ghost.

**README.md** becomes a product front page (<100 lines): one-liner tagline, what it is (3 sentences), what it is NOT, product loop diagram, what works today, main surfaces table, repo map, quickstart link, license/contributing links.

**Critical wording rule:** never use "unify" for lane behavior. Native and imported lanes remain separate unless composed read-only. Use "browse across" or "bring together."

**docs/getting-started.md** replaces old SETUP.md: minimal install, run app, run tests, import sample, export passport, validate passport.

**Sweep all product docs** and enforce terminology rules from above.

**Definition of done:** public docs match actual repo truth, portable-dir/USB interpretation is gone, Memory Passport remains intact.

---

### Phase 3 — Canonical Workspace on `/`
Turn the homepage into the center of gravity. Not a dashboard — a foyer.

**Create:** `src/app/viewmodels/workspace.py` with `WorkspaceSummary` dataclass (counts, providers, recent items, has_any_data).

**Modify:** route stays `/`, nav label becomes "Workspace", template shows six blocks:
1. Continuity Status
2. Provider Coverage (badges)
3. Resume Recent Work
4. Search handoff
5. Passport Status (honest capability check)
6. Next Actions

**NOTE:** Visual Summary Dashboard content folds into blocks 1-2 as supporting data, not as a product headline. No dashboard bloat. No metrics theater.

**Definition of done:** `/` feels like the center of the app, user can see what's here and resume.

---

### Phase 4 — Import lifecycle UI
Surface the existing import pipeline in the web app. Import is the first gate of value.

**Create:** `/import` route with upload form, provider auto-detection, result display, and bounded error handling.

**Current implementation note:** the web route reuses the existing import pipeline and hands the uploaded JSON through the current file-based importer path. No `parse_import_payload()` helper is part of the landed implementation.

**Definition of done:** user can import from the browser, auto-detection works for all three providers, CLI still works.

---

### Phase 5 — In-app Ask
Surface grounded answering as a first-class product experience.

**Create:** `/ask` route with text input, answer display with status badge, inline citation links, trace link, recent questions.

**Uses existing pipeline only.** No new LLM integration. No streaming. No model selection.

**Definition of done:** user can ask a question and get a grounded answer with clickable citations.

---

### Phase 6 — Passport surface / integrity UX
Make the "memory passport" promise visible and inspectable inside the product.

**Create:** a calm capability/status surface that shows what a passport is, whether export and validation are available, and what continuity means without replacing canonical local records.

**Current implementation note:** the web surface is live and first-class, but bounded. Export and validation remain existing CLI-backed capabilities, and the current web scope does not inspect a specific artifact.

**Definition of done:** Memory Passport is no longer basement-only. Users can see and understand it.

---

## Deferred Sequence

### 7. Derived intelligence
Provenance-bound summaries, notes, topic threads. All derived. All non-canonical. Per-conversation only first. No auto-summarize. No vector DB. No cross-conversation synthesis until per-conversation is solid.

### 8. Product polish
Responsive CSS, keyboard navigation, scroll-spy in explorer, empty/loading/error states, blueprint extraction for route sprawl, legacy cleanup.

### 9. Growth experiments
Shareable summary ("Spotify Wrapped for AI"), landing page, public launch assets. Not in the mainline execution spine — belongs in a separate growth appendix.

---

## Explicitly Removed from Active Plan

- Portable data-root / `SOULPRINT_DATA_DIR` implementation
- USB / capsule / physical portability framing
- Portable-mode docs
- Desktop packaging (deferred until coherence phases complete)
- mem0 activation
- Mobile app
- Any language suggesting "carry it on a stick"

---

## Governance Rules

**One source of truth.** `EXECUTION_GUIDE.md` (or this document once placed in `docs/product/`).

**One active phase.** Do not work on multiple phases simultaneously.

**One bounded task per merge.** Each PR should be reviewable and self-contained.

**Claude as contractor, not roadmap driver.** Do not let the agent propose future phases unless asked. Do not let agent velocity outrun founder control.

**After every Claude output, ask only:** accept, revise, or reject?

---

## Two-Layer Prompt Architecture

### Layer 1 — Product / Doctrine / Implementation

This controls: architecture, lane honesty, route behavior, scope, anti-drift rules.

Place in repo as: `CLAUDE.md` (root) + `docs/product/execution-guide.md`

### Layer 2 — Visual Direction / Aesthetic Rules

This controls: texture, motion, gradients, empty-state warmth, brand atmosphere.

Place in repo as: `docs/product/visual-direction.md`

**The rule:** Layer 1 always wins. Layer 2 may only enhance finish without creating drift. If style conflicts with clarity, choose clarity. Algorithmic-art is lighting and atmosphere, not the house.

---

## Repo Integration Plan for the Two-Layer System

### Where files go:

```
SoulPrint-Canonical/
  CLAUDE.md                          ← Layer 1 (agent/operator instructions)
  README.md                          ← product front door
  LICENSE
  CONTRIBUTING.md
  ROADMAP.md
  CHANGELOG.md
  docs/
    getting-started.md
    product/
      positioning.md
      context.md
      execution-guide.md             ← Layer 1 (canonical execution spine)
      visual-direction.md            ← Layer 2 (aesthetic rules only)
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

### How Claude Code reads them:

`CLAUDE.md` is read automatically every session (Layer 1 operator rules).

When working on UI/CSS/template tasks, Claude Code should also read `docs/product/visual-direction.md` (Layer 2 aesthetic rules).

When planning implementation, Claude Code should read `docs/product/execution-guide.md` for scope and phase governance.

### Integration rule:

**Doctrine files (`CLAUDE.md`, `execution-guide.md`) are Layer 1.** They control what gets built, what's in scope, what lanes are honest, and what stays derived.

**Visual direction (`visual-direction.md`) is Layer 2.** It controls how things look and feel. It may only be applied to UI, interaction, empty states, brand surfaces, and aesthetic polish. It may never alter route structure, information architecture, provenance rules, or canonical-vs-derived boundaries.

**algorithmic-art stays quarantined.** It can inform visual-direction prompts for landing pages, summary pages, and ambient atmospherics. It must never drive product architecture.

---

## Current Active Stretch

**Phase:** Active surface truth alignment

**Current live surfaces in code:**
1. Workspace on `/`
2. Import web surface on `/import`
3. In-app Ask on `/ask`
4. Passport capability/status surface on `/passport`

**Frozen:**
- Derived intelligence
- Polish / onboarding
- Growth experiments
- Desktop packaging
- mem0 activation
- Any portability/USB-style implementation

**Merge rule:** Do not begin the next task until the current one is merged, verified, and accepted.

---

## The Four Codex Prompts (Today's Implementation)

### Prompt 1 — Repo face cleanup

```
Work from current main as source of truth.

Task:
Clean the public repo face and stratify documentation without
changing runtime behavior.

Do:
1. Add LICENSE (Apache-2.0)
2. Create CONTRIBUTING.md
3. Create CHANGELOG.md
4. Create ROADMAP.md
5. Create .github/workflows/tests.yml
6. Add issue templates
7. Move root markdown clutter under docs/ subfolders
8. Update internal links after file moves
9. Keep README.md and CLAUDE.md at root

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

### Prompt 2 — README/docs truth alignment

```
Work from current repo truth first, then corrected doctrine notes.

Task:
Rewrite public-facing docs so they reflect actual current product
and remove the portability ghost.

Do:
1. Rewrite README.md as product front page
2. Rewrite docs/getting-started.md for current state
3. Remove all portable-mode/USB/capsule language
4. Replace with: continuity, exportability, interoperability,
   local ownership, Memory Passport
5. Preserve Memory Passport as core concept
6. Do not change runtime code

Definition of done:
- public docs match actual repo truth
- portable-dir / USB interpretation is gone
- Memory Passport remains intact
```

### Prompt 3 — Split canon from style

```
Task:
Separate doctrine from aesthetic prompting.

Do:
1. Create docs/product/visual-direction.md
2. Create docs/product/execution-guide.md
3. Remove algorithmic-art references from canonical execution docs
4. Keep algorithmic-art only as downstream aesthetic lens
5. Add clear rule: Layer 1 (doctrine) always overrides Layer 2 (style)

Definition of done:
- execution guide is clean product canon
- visual direction is separate
- algorithmic-art is style-only
```

### Prompt 4 — Narrow the active roadmap

```
Task:
Create strict current-phase guide.

Do:
1. Active sequence: active-surface truth alignment across workspace, import, Ask, and Passport wording
2. Freeze only what is still outside the live surface set: intelligence, polish, growth, desktop, portability
3. No future-phase planning beyond active stretch

Definition of done:
- one active stretch
- tasks are merge-sized
- future drift is frozen
```

---

## The One Rule

Every phase, every prompt, every commit must pass this test:

**Does this make SoulPrint feel like one calm, trustworthy product — or does it add another subsystem?**

If it's another subsystem, it's not ready.

*SoulPrint is not about carrying memory like an object. It is about preventing memory exile.*
