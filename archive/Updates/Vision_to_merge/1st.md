I treated the sources in the order you clarified:

**1. current repo truth first**
**2. corrective markdown next**
**3. the large execution guide last**

That ordering matters, because the public repo is still visibly behind the repo’s actual product state: the root still carries `MEM0_BOUNDARY_DESIGN.md`, `REPAIR_NOTES.md`, `REPO_AUDIT.md`, and `SETUP.md`, and the public README still presents SoulPrint as a “Current Milestone 1+ importer capability” centered on the first ChatGPT importer path rather than the fuller three-provider product spine. ([GitHub][1])

## The final recap of what changed across the markdown sequence

Here is the clean bird’s-eye recap.

### 1. The execution guide got the big diagnosis right

The large execution guide correctly identified the repo problem as **“unstratified truth”** and proposed a full phase map from repo cleanup through workspace, ask, import, desktop, portability, intelligence, polish, and virality. It also framed the system model as **truth → legibility → portability → intelligence → distribution**. 

That part survives.

### 2. The review corrected the execution order

The corrective review kept most of the guide but made the decisive edits:

* **Import UI must come before Ask**
* **Passport surface must become explicit**
* **Visual Summary Dashboard must be demoted from product identity to supporting workspace block**
* **algorithmic-art must be removed from the canonical execution guide**
* the guide needed one senior editorial pass before becoming canon 

That correction survives too.

### 3. The portability interpretation was explicitly rejected

The next major correction is even more important for your current request:

the “portable dir / USB / carry it anywhere” interpretation was explicitly marked as wrong. The corrective file says portability in SoulPrint should **not** mean USB-stick portability or physical transport metaphor, and recommends replacing it with **continuity**, **exportability**, **interoperability**, and **local ownership** language instead. It even calls out README, POSITIONING, ROADMAP/doctrine language, and UI copy as the first places to fix. 

This is now the governing correction.

### 4. algorithmic-art was reclassified, not deleted

The two-layer prompt notes and follow-up discussion settled the right role for `algorithmic-art.md`:

* **keep it**
* **do not let it govern product doctrine**
* use it only as a **secondary visual-style layer**
* keep it downstream from README, ROADMAP, CONTEXT, and the execution guide  

That means algorithmic-art stays alive, but in quarantine.

### 5. The governance correction matters as much as the product correction

The conclusion file makes the human problem explicit: too many lanes, too many prompts, too much agent velocity. Its fix is simple and right:

* one source of truth
* one active phase
* one bounded task
* one merge at a time
* Claude as contractor, not roadmap driver 

That is not just emotional advice. It is now part of the operating model.

---

## The final canonical changes I would make now

This is the actual synthesis.

### A. Remove the portable-DIR / USB implementation idea from the active plan

This is the biggest correction.

The execution guide currently still contains a literal **Portable Mode / SoulPrint Capsule** phase with `SOULPRINT_DATA_DIR`, relative-path rewiring, and USB/cloud/mounted-image framing. That appears both in the large execution guide and the standalone execution guide.  

Based on your clarification, that phase should be **removed from the near-term implementation prompts and from public-facing README/roadmap language**.

Not softened. Removed.

What survives is:

* **Memory Passport**
* **exportability**
* **continuity**
* **interoperability**
* **local ownership**

What dies is:

* portable dir
* USB framing
* carry it anywhere
* portable capsule
* `SOULPRINT_DATA_DIR` as an active roadmap item
* anything that makes SoulPrint sound like a thumb-drive product

### B. Keep Memory Passport, but rewrite its narrative

Do **not** remove Memory Passport.

Keep it as:

* provenance-and-validation construct
* exportable continuity layer
* inspectable artifact
* way to prevent platform captivity

Do **not** describe it as physical portability.

### C. Split the canon into two prompt layers

This is the right long-term fix.

**Layer 1 = Product / doctrine / implementation scope**
This controls:

* architecture
* lane honesty
* route behavior
* what is in scope
* what the surface must do
* anti-slop and anti-drift rules

**Layer 2 = Visual direction / aesthetic lens**
This controls:

* texture
* motion tone
* gradients
* micro-interaction feeling
* visual rhythm
* landing page atmosphere
* summary-page flavor

That split is already strongly supported by the two-layer prompt file and the algorithmic-art discussion.  

### D. Tighten the active roadmap

The execution guide should stop being a big “all futures at once” machine.

For now, the only active cleanup/implementation lane should be:

1. repo face cleanup
2. README + docs truth alignment
3. canonical workspace on `/`
4. later, import UI
5. later, ask surface
6. later, passport surface

And even that should be executed as one bounded prompt at a time.

---

## What is actually messy in repo truth right now

This is not theoretical. It is visible.

The public repo still has root-level clutter that should be stratified under docs, including `MEM0_BOUNDARY_DESIGN.md`, `REPAIR_NOTES.md`, `REPO_AUDIT.md`, and `SETUP.md`. ([GitHub][1])

The public README is still behind the actual product. It still describes a Milestone-1-style story centered on a first ChatGPT importer path and old CLI surfaces, rather than the broader current state. ([GitHub][1])

The uploaded repo snapshot confirms the same drift in local files: the root still contains `Additional Step.md`, `CONTEXT.md`, `POSITIONING.md`, `REPAIR_NOTES.md`, `REPO_AUDIT.md`, and `SETUP.md`, all competing too close to the front door. The same snapshot also shows the newer capabilities already exist in code and tests, which is exactly why the docs now look older than the product. ([GitHub][1])

So the current repo problem is still what the execution guide said it was:
**the code kept moving; the presentation did not consolidate at the same speed.** 

---

## The corrected long-range execution spine

Here is the cleaned version I would bless now.

### Active spine

1. Repo face cleanup
2. README and docs rewrite
3. Canonical Workspace on `/`
4. Import lifecycle UI
5. In-app Ask
6. Passport surface / integrity UX

### Deferred spine

7. Derived intelligence
8. Polish / responsive / onboarding
9. Growth experiments

### Removed from the active spine

* Portable data-root groundwork
* USB / capsule / physical portability framing
* portable-mode docs
* any public language that suggests “carry it on a stick”

That deletion is justified both by your clarification and by the corrective “remove portability” file. 

---

## The two-layer meta-prompt you asked for

This is the version I would keep as a reusable master prompt.

```text
Continue SoulPrint from current canonical repo truth.

You are working as a senior engineer, product architect, and project manager on an active product.
Do not treat SoulPrint as a vague idea.
Do not restart from philosophy unless explicitly asked.

SOURCE HIERARCHY
1. current repo truth first
2. corrected markdown/doctrine notes second
3. older execution-guide ideas third

LAYER 1 — PRODUCT / DOCTRINE / IMPLEMENTATION RULES
SoulPrint is a local-first memory continuity system for AI users.
Its purpose is to let a person import AI conversation history from multiple providers, preserve it in a canonical local ledger, inspect it with explicit provenance, search and browse it fluidly, answer from it conservatively, and export/validate it as a Memory Passport.

Core rules:
- canonical SQLite-backed local ledger remains authoritative
- native and imported lanes remain explicit unless composed read-only
- browsing/retrieval layers are read-only
- answering/traces are derived and non-canonical
- optional systems must never replace canonical truth
- no route sprawl
- no dashboard bloat
- no fake web execution for flows that are still CLI-only
- no broad new capability unless it strengthens product coherence
- no slop

Terminology correction:
- do not use “portable mode,” “USB memory,” “carry it anywhere,” or local-dir portability language
- use continuity, exportability, interoperability, and local ownership instead
- Memory Passport is a provenance-and-validation construct, not a physical portability metaphor

Current product priority:
The current problem is not missing capability breadth.
The current problem is product coherence.

Default execution mode:
- one active task at a time
- one bounded merge at a time
- do not propose future phases unless asked
- if a task is not in scope, leave it alone

LAYER 2 — VISUAL DIRECTION / AESTHETIC RULES
Leave doctrine files and product architecture unchanged.
Apply visual direction only to UI, interaction feel, empty states, brand surfaces, and aesthetic polish.

UI style rules:
- calm
- fluid
- Apple-like
- low-clutter
- readable whitespace
- subtle warmth
- obvious navigation
- continuity-first
- no metrics theater
- no noisy admin-panel energy
- no ornamental AI gimmicks

algorithmic-art usage:
- use it only as a secondary aesthetic lens
- use restrained generative texture, motion language, gradient rhythm, subtle background systems, and premium visual atmosphere
- do not let algorithmic-art drive route structure, layout doctrine, provenance rules, or product architecture
- treat it as lighting and atmosphere, not as the house

When implementing:
1. obey Layer 1 first
2. apply Layer 2 only if it improves finish without creating drift
3. if style conflicts with clarity, choose clarity
```

That is the clean split.

---

## The design-outlook rule to add

This is the additional rule I would add as a tiny standalone note or `VISUAL_DIRECTION.md`:

```text
SoulPrint visual-direction rule

Doctrine files are not aesthetic playgrounds.
Do not alter product architecture, lane honesty, provenance display rules, or workflow structure in the name of style.

Use aesthetic prompting only for:
- visual rhythm
- gradients
- subtle motion
- empty-state warmth
- brand atmosphere
- future summary/landing pages
- tasteful micro-interactions

Never use aesthetic prompting to redefine:
- route structure
- information architecture
- transcript explorer behavior
- import UX logic
- answer-trace trust model
- canonical vs derived boundaries
```

This is the rule that keeps algorithmic-art useful without letting it start a civil war.

---

## The next 4 small Codex-ready cleanup prompts

These are intentionally narrow, easy, and merge-sized.

### Clean the repo — Step 1

**Goal:** clean the public repo face without touching runtime behavior.

```text
Work from current main as source of truth.

Task:
Clean the public repo face and stratify documentation without changing runtime behavior.

Do:
1. Add LICENSE (Apache-2.0)
2. Add CONTRIBUTING.md
3. Add ROADMAP.md
4. Add CHANGELOG.md
5. Add GitHub Actions test workflow
6. Add bug and feature issue templates
7. Move root markdown clutter under docs/:
   - POSITIONING.md
   - CONTEXT.md
   - MEM0_BOUNDARY_DESIGN.md
   - REPO_AUDIT.md
   - REPAIR_NOTES.md
   - SETUP.md
   - Additional Step.md
8. Update internal links after file moves
9. Keep README.md and CLAUDE.md at root

Out of scope:
- no app behavior changes
- no route changes
- no schema changes
- no dependency changes except what is required for CI if pytest is used

Definition of done:
- root looks intentional and professional
- docs are stratified by role
- CI runs
- runtime behavior unchanged
```

### Clean the repo — Step 2

**Goal:** rewrite README and docs language to remove the USB/portable-dir ghost.

```text
Work from current repo truth first, then corrected doctrine notes.

Task:
Rewrite README and key product-language docs so SoulPrint no longer implies USB/portable-dir implementation.

Required language changes:
1. Remove or replace phrases like:
   - carry your memory anywhere
   - portable AI memory
   - USB/capsule/portable-dir framing
2. Replace with:
   - continuity
   - exportability
   - interoperability
   - local ownership
   - Memory Passport as provenance-and-validation construct
3. Update README front page to reflect actual current product state:
   - three-provider import
   - canonical ledger
   - transcript explorer
   - federated retrieval
   - grounded answering
   - answer traces
   - passport export/validation
4. Rewrite SETUP/getting-started language so it no longer describes a Milestone-1-only repo
5. Keep doctrine sharp and practical

Out of scope:
- no code changes
- no new routes
- no new product features

Definition of done:
- public docs match current repo truth
- portable-dir / USB interpretation is gone
- Memory Passport remains intact
```

### Clean the repo — Step 3

**Goal:** split canon from style.

```text
Task:
Create a two-layer prompt structure for SoulPrint and remove algorithmic-art contamination from canonical execution documents.

Do:
1. Create VISUAL_DIRECTION.md (or SOULPRINT_VISUAL_STYLE_PROMPT.md)
2. Put all algorithmic-art-inspired UI/style rules there:
   - restrained generative texture
   - subtle seed-like variation
   - calm motion language
   - premium atmosphere
3. Update the main execution guide so it no longer contains algorithmic-art material
4. Add a clear rule:
   - doctrine files and architecture prompts are Layer 1
   - aesthetic prompting is Layer 2
   - Layer 2 must never override Layer 1
5. Keep the execution guide focused on product order, doctrine, scope, and implementation governance

Out of scope:
- no runtime changes
- no UI implementation changes yet

Definition of done:
- execution guide is clean canon
- style guidance lives separately
- algorithmic-art is quarantined as aesthetic seasoning only
```

### Clean the repo — Step 4

**Goal:** narrow the active roadmap and freeze distracting futures.

```text
Task:
Produce a cleaned execution guide for the next active stretch only.

Rules:
- current repo truth first
- current active problem is coherence, not breadth
- one active phase
- one bounded task per merge
- do not plan beyond what is needed now

Required output:
1. Rewrite the execution guide so the active spine is only:
   - repo face cleanup
   - README/docs truth alignment
   - canonical workspace on /
   - import UI
   - ask surface
   - passport surface
2. Move later ideas into a clearly marked deferred appendix:
   - derived intelligence
   - polish
   - growth experiments
3. Remove portable-dir / USB implementation phase entirely from the active plan
4. Demote Visual Summary Dashboard from product identity to supporting workspace block
5. Keep growth / wrapped ideas out of the mainline execution spine

Definition of done:
- the guide feels governed, not sprawling
- near-term steps are reviewable and merge-sized
- distracting futures are preserved, but frozen
```

---

## My final recommendation

Do **not** try to execute the whole long-range plan right now.

Your own corrective materials already diagnose the real danger: too many concurrent futures, too many prompts, too many valid next moves, and agent velocity outrunning founder control. 

So the sane operating mode is:

* use the **two-layer prompt split**
* treat **portable-dir / USB implementation as removed**
* run **only the 4 small cleanup prompts above**
* then stop and reassess before touching import UI or Ask

That is the senior move.

The repo already has enough spine. What it lacks is not capability. It lacks a cleaned front door, a unified language, and a disciplined command surface. That is what these next four prompts fix.

If you want, next I’ll do the sharper follow-up: write the **actual replacement text** for `README.md`, `ROADMAP.md`, and `VISUAL_DIRECTION.md` so you can hand Codex exact content instead of just instructions.

[1]: https://github.com/Celestialchris/SoulPrint-Canonical "GitHub - Celestialchris/SoulPrint-Canonical: Canonical 2026 SoulPrint repo. Scope: import -> normalize -> store -> retrieve. Excludes archive, Archetype vault, and historical snapshots. · GitHub"
