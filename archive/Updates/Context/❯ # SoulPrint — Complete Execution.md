❯ # SoulPrint — Complete Execution Guide
## From Repo to Product: Step-by-Step

*Synthesized from full repo audit, architectural doctrine, competitive analysis, and forward product strategy.*

---

## Current State Assessment

**What exists and works (verified, 130+ tests passing):**

- Three-provider import pipeline (ChatGPT, Claude, Gemini) with auto-detection
- Canonical SQLite ledger with explicit native/imported lanes
- Transcript explorer with prompt-level TOC + minimap rail
- Federated cross-lane search
- Grounded local answering with citation provenance
- Answer Trace audit residue (JSONL, non-canonical)
- Citation-to-record handoff
- Memory Passport export + validation
- Shared app shell with warm, Apple-like CSS design language
- Visual Summary Dashboard (PR #37, just merged)

**What's messy:**

The repo's problem is not broken code — it's *unstratified truth*. Nine markdown files compete at the root level. SETUP.md and REPO_AUDIT.md still describe a
Milestone-1 baseline while the codebase has moved three phases ahead. There's no LICENSE, no CI badge, no CONTRIBUTING guide, no ROADMAP, no CHANGELOG. The repo
looks like a talented developer's work-in-progress, not a product someone should trust.

**The core diagnosis:**

The code kept moving. The presentation did not consolidate at the same speed.

---

## The System Model

Everything in SoulPrint follows this ordering. Never violate it.

```
Layer A — Truth        → Canonical ledger. SQLite. Explicit lanes. Stable provenance.
Layer B — Legibility   → Browse, search, inspect, trace, export. Derived never pretends to be truth.
Layer C — Portability  → Memory Passport, portable mode, capsule packaging.
Layer D — Intelligence → Summaries, topics, notes, digests. All derived. All provenance-bound.
Layer E — Distribution → Desktop wrapper, installer, responsive UI, mobile companion.
```

The build sequence is: **truth → legibility → portability → intelligence → distribution**

---

## Phase 1: Repo Face Cleanup

**Goal:** Make the GitHub page look like a senior-owned open product. Zero code changes.

### Claude Code Prompt:

```
You are working from the current main branch of the canonical SoulPrint repo.

Goal:
Make the public GitHub repo look like a serious senior-owned open product
repository without changing any runtime behavior.

Context:
SoulPrint is a local-first memory passport for AI users. The repo has
strong architecture but uneven documentation layering and root-level clutter.
Nine markdown files currently compete at the root level. Historical docs
(REPO_AUDIT.md, REPAIR_NOTES.md, SETUP.md) still describe an earlier
Milestone-1 baseline while the codebase has moved into cross-provider
continuity, retrieval, answering, and passport work.

Required outcomes:

1. Add LICENSE file (Apache-2.0)

2. Add CONTRIBUTING.md (short, serious):
   - run minimal install
   - run tests before submitting
   - no route without tests
   - no derived-to-canonical mutation
   - no lane unification without explicit decision
   - no heavy dependency creep without rationale

3. Add ROADMAP.md with these phases:
   - Coherence (current)
   - Canonical Workspace
   - In-app Ask surface
   - Desktop packaging (Tauri/PyWebView)
   - Portable Mode / SoulPrint Capsule
   - Derived Intelligence
   - Mobile companion

4. Add CHANGELOG.md starting from current state

5. Add .github/workflows/tests.yml that runs pytest on push/PR

6. Add .github/ISSUE_TEMPLATE/ with bug_report.md and feature_request.md

7. Move root clutter into docs/ subfolders:
   - POSITIONING.md → docs/product/positioning.md
   - CONTEXT.md → docs/product/context.md
   - MEM0_BOUNDARY_DESIGN.md → docs/architecture/mem0-boundary.md
   - SETUP.md → docs/getting-started.md (rewrite for current state)
   - REPO_AUDIT.md → docs/reference/history/repo-audit-baseline.md
   - REPAIR_NOTES.md → docs/reference/history/repair-notes.md
   - Additional Step.md → docs/reference/ideas/desktop-and-derived-intelligence.md

8. Organize docs/ like this:
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
         desktop-and-derived-intelligence.md

9. Update any internal cross-references in moved files

10. Keep CLAUDE.md at root (it's agent/operator guidance)
    Keep README.md at root (rewrite in next phase)

Out of scope:
- no app behavior changes
- no new routes
- no schema changes
- no dependency changes

Definition of done:
- root has: README, LICENSE, CONTRIBUTING, ROADMAP, CHANGELOG, CLAUDE.md,
  requirements files, .github/, src/, tests/, sample_data/, docs/
- historical/design docs are stratified under docs/
- CI runs and passes
- no runtime behavior changed
```

---

## Phase 2: README Rewrite

**Goal:** The README becomes a product front page, not an engineering changelog.

### Claude Code Prompt:

```
Rewrite README.md as a clean product-facing front page for SoulPrint.

Current problem: the README reads like accumulated engineering announcements.
It should read like one confident product page.

Structure (in this order):

1. ONE-LINER
   "Your AI conversations are scattered everywhere. SoulPrint brings them home."

2. WHAT IT IS (3 sentences max)
   Local-first memory passport. Import from ChatGPT, Claude, Gemini.
   Browse, search, answer from, and export your AI memory with provenance.

3. WHAT IT IS NOT (keep this — it's doctrine)
   Not hosted SaaS. Not a mem0 clone. Not an AI dashboard.

4. PRODUCT LOOP (visual)
   Import → Inspect → Search → Answer → Export

5. WHAT WORKS TODAY (honest list)
   - Three-provider import with auto-detection
   - Transcript explorer with TOC + minimap
   - Federated cross-lane search
   - Grounded answering with citation traces
   - Memory Passport export + validation
   - Visual summary dashboard

6. QUICKSTART (minimal, 5 lines)
   pip install, run, import sample, open browser

7. MAIN SURFACES (route table)
   / → Workspace
   /imported → conversation browser
   /imported/<id>/explorer → transcript explorer
   /federated → cross-lane search
   /answer-traces → audit traces

8. REPO MAP (folder structure, 10 lines max)

9. DOCS (link to docs/ subfolders)

10. LICENSE + CONTRIBUTING links

Remove all "Milestone 1" language from the front page.
Remove historical checkpoint language.
Remove CLI command reference (that belongs in docs/getting-started.md).
Keep it under 150 lines total.
Tone: confident, calm, technical but not cluttered.
```

---

## Phase 3: Canonical Workspace on `/`

**Goal:** The homepage becomes the center of gravity. Not a dashboard — a foyer.

### Claude Code Prompt:

```
Implement Phase 6.2 — Canonical Workspace on `/`.

Goal:
Evolve `/` from a summary page into the center-of-gravity workspace for
SoulPrint's product loop: Import → Inspect → Search → Answer → Export

Required outcomes:

1. Keep the route as `/`
2. Update nav label from "Home" to "Workspace"
3. Create src/app/viewmodels/workspace.py with a WorkspaceSummary object:
   - native_count, imported_count, total_messages
   - providers (list of distinct provider names from imported data)
   - recent_imported (last 5 imported conversations)
   - recent_native (last 5 native memory entries)
   - recent_traces (last 3 answer traces)
   - passport_ready (boolean: can we export?)
4. Route stays thin — build the summary, pass to template
5. Template shows six blocks:
   - Continuity Status (counts, "You have X conversations from Y providers")
   - Provider Coverage (badges per provider)
   - Resume Recent Work (clickable recent items)
   - Search handoff (link to /federated)
   - Passport Status (honest: ready to export, or "N conversations available")
   - Next Actions (clear links to import, browse, search, export)
6. Keep the Apple-like design: warm palette, lane-colored badges, no clutter
7. Empty state should be calm and welcoming, not sad

Guardrails:
- no schema changes
- no new persistence
- no upload/import execution UI yet
- no passport execution buttons yet
- no /ask route yet
- derive all data from existing tables/filesystem only

Tests required:
- workspace renders with counts
- provider coverage shows when imported data exists
- empty state is safe and intentional
- nav label says "Workspace"
- full regression suite passes

Definition of done:
- `/` feels like the center of the app
- user can clearly see what's here and resume from where they are
- page is calmer and more useful than previous version
```

---

## Phase 4: In-App Ask Surface

**Goal:** The answering layer becomes a first-class product surface.

### Claude Code Prompt:

```
Implement Phase 6.3 — In-app Ask surface at /ask.

Context:
SoulPrint already has grounded local answering (src/answering/local.py),
answer traces (src/answering/trace.py), and citation handoff
(src/app/citation_handoff.py). This phase surfaces it in the UI.

Required outcomes:

1. Add route /ask
2. Add nav item "Ask" after "Workspace"
3. Simple form: text input + submit
4. On submit: run existing answering pipeline
5. Display:
   - answer text
   - status badge (grounded / ambiguous / insufficient_evidence)
   - inline citations as clickable links to source records
   - "View full trace" link to /answer-traces/<id>
6. Auto-emit trace on every answer
7. Show recent questions below the form (last 5 traces)
8. Empty state: calm prompt explaining what Ask does

Guardrails:
- use existing answering logic only
- no new LLM integration
- no streaming
- no model selection UI
- keep it read-only over canonical data

Tests:
- /ask renders form
- POST /ask with valid question returns answer
- citations link to correct surfaces
- trace is emitted
- insufficient_evidence displays honestly

Definition of done:
- user can ask a question and get a grounded answer in the browser
- citations are clickable
- traces accumulate
- the experience is honest about what it can and cannot answer
```

---

## Phase 5: Import Lifecycle UI

**Goal:** Web-based import replaces CLI-only workflow.

### Claude Code Prompt:

```
Implement Phase 6.4 — Import lifecycle UI.

Context:
Import currently works via CLI only (python -m src.importers.cli).
The pipeline (auto-detect, parse, persist, deduplicate) is fully built.
This phase adds a web UI over the existing pipeline.

Required outcomes:

1. Add route /import
2. Add nav item "Import" after "Ask"
3. File upload form (drag-and-drop zone + file picker)
4. On upload:
   - save temp file
   - call parse_import_file() with auto-detection
   - call persist_normalized_conversations()
   - show results: provider detected, conversations imported, skipped, warnings
5. Provider badge on results
6. Post-import: "View imported conversations" link to /imported
7. Error handling:
   - malformed JSON → clear error message
   - unsupported format → suggest supported providers
   - duplicate skip → show count clearly
8. Keep the existing CLI path working unchanged

Guardrails:
- no new importer logic
- no streaming upload
- no batch/folder upload yet
- reuse existing pipeline functions exactly

Tests:
- /import renders upload form
- POST with valid ChatGPT fixture imports successfully
- POST with valid Gemini fixture imports successfully
- POST with invalid JSON shows error
- duplicate import shows skip count
- regression suite passes

Definition of done:
- user can import from the browser
- auto-detection works for all three providers
- errors are clear and helpful
- CLI still works
```

---

## Phase 6: Desktop Packaging (PyWebView First)

**Goal:** SoulPrint becomes a desktop app you can double-click.

### Claude Code Prompt:

```
Implement Phase 7.1 — PyWebView desktop wrapper (prototype).

Context:
SoulPrint is a Flask + SQLite app. PyWebView can wrap it in a native
desktop window with ~10 lines of code. This is the fastest path to
"double-click to open" before investing in Tauri.

Required outcomes:

1. Add desktop/ folder at repo root
2. Create desktop/launcher.py:
   - import webview
   - import create_app from src.app
   - start Flask in a thread
   - open webview window pointing to localhost
   - window title: "SoulPrint — Your AI Memory"
   - window size: 1200x800
3. Add pywebview to requirements.txt (not requirements-minimal.txt)
4. Add docs for running desktop mode:
   pip install pywebview
   python desktop/launcher.py
5. App should work exactly as web version
6. On window close, Flask server stops cleanly

Guardrails:
- no Tauri yet (that's Phase 7.2)
- no Electron
- no new routes or features
- no changes to existing Flask app
- desktop wrapper is purely additive

Tests:
- launcher.py imports without error
- create_app() works when called from launcher context
- all existing tests still pass

Definition of done:
- user can run one command and see SoulPrint in a desktop window
- everything works: workspace, import, browse, search, ask, traces
- closing window exits cleanly
```

---

## Phase 7: Portable Mode / SoulPrint Capsule

**Goal:** All state lives under one configurable directory. Carry it anywhere.

### Claude Code Prompt:

```
Implement Phase 8.1 — Portable data root.

Context:
SoulPrint currently hardcodes paths relative to the repo (instance/soulprint.db,
etc). Portable mode means all state can live under one directory that could be
on a USB drive, cloud sync folder, or mounted image.

Required outcomes:

1. Add SOULPRINT_DATA_DIR environment variable support
2. When set, all paths resolve relative to it:
   - database: $SOULPRINT_DATA_DIR/instance/soulprint.db
   - exports: $SOULPRINT_DATA_DIR/exports/
   - traces: $SOULPRINT_DATA_DIR/traces/
   - passports: $SOULPRINT_DATA_DIR/passports/
3. When not set, current behavior is unchanged (backward compatible)
4. Update src/config.py to resolve paths from data root
5. Update answering trace store path
6. Update passport export default paths
7. Add docs/portable-mode.md explaining:
   - default mode (current behavior)
   - portable mode (set SOULPRINT_DATA_DIR)
   - example USB/portable layout:
     SoulPrint-Capsule/
       app/
       data/
         instance/
         exports/
         traces/
         passports/

Guardrails:
- no encryption yet
- no mounted image format
- no auto-detection of removable media
- no changes to schema
- no changes to canonical vs derived separation

Tests:
- app boots with SOULPRINT_DATA_DIR set to temp directory
- import works against portable data root
- passport export writes to portable data root
- trace store uses portable data root
- default behavior unchanged when env var not set

Definition of done:
- SOULPRINT_DATA_DIR controls where all state lives
- all existing features work against portable root
- documented
- backward compatible
```

---

## Phase 8: Derived Intelligence Layer

**Goal:** NotebookLLM-style summaries and notes, always provenance-bound.

### Claude Code Prompt:

```
Implement Phase 9.1 — Per-conversation summarizer with LLM connection.

Context:
SoulPrint's Layer 3 (Answering/Audit) already produces derived artifacts
with provenance (answer traces). This phase extends that pattern into
richer derived intelligence: conversation summaries generated by the
user's preferred LLM.

Required outcomes:

1. Add src/intelligence/ package:
   - __init__.py
   - llm_provider.py (abstract LLM interface)
   - summarizer.py (per-conversation summary generation)
   - store.py (derived artifact persistence)

2. LLM provider interface:
   - supports "bring your own API key" model
   - initial providers: OpenAI, Anthropic
   - provider configured via SOULPRINT_LLM_PROVIDER and SOULPRINT_LLM_API_KEY
   - no API calls if not configured (feature is dormant)

3. Summarizer:
   - takes one ImportedConversation
   - sends message content to configured LLM
   - receives summary text
   - stores as derived artifact with:
     - source_conversation_stable_id
     - generation_timestamp
     - llm_provider_used
     - prompt_template_version
     - summary_text
   - clearly labeled "Derived / non-canonical"

4. Derived store:
   - JSONL append-only (same pattern as answer traces)
   - stored under data root (respects portable mode)
   - list and get operations

5. UI surface:
   - /intelligence or /notes route
   - show generated summaries with provenance links
   - "Generated from [conversation title]" with clickable link
   - "Generated by [provider] on [date]"
   - empty state: explain feature, prompt to configure LLM

6. Settings surface or docs for configuring LLM connection

Guardrails:
- derived artifacts NEVER replace canonical records
- all summaries trace back to stable IDs
- no summaries generated without explicit user action
- no automatic background processing
- no vector database
- no semantic search (yet)
- no cross-conversation synthesis (yet — that's Phase 9.2)

Tests:
- summarizer produces artifact with required fields
- store persists and retrieves
- UI renders summaries with provenance
- feature is dormant when LLM not configured
- canonical data unchanged after summarization

Definition of done:
- user can configure their LLM, generate a summary of any conversation,
  see it alongside the original with clear provenance
- nothing canonical is touched
```

---

## Phase 9: Polish & Ship

**Goal:** Make it irresistible.

### Key Tasks (each a separate Claude Code prompt):

1. **Responsive CSS pass** — make all surfaces work on tablet/mobile widths
2. **Keyboard navigation** — arrow keys between prompts in explorer, `/` to focus search
3. **Smooth scroll-spy** — TOC highlights current prompt as user scrolls
4. **Empty states** — every surface has a calm, helpful zero-data state
5. **Loading states** — import and ask operations show progress
6. **Error states** — every error is human-readable, not a stack trace
7. **Landing page** — `index.html` for GitHub Pages or landing site
8. **Installer** — PyInstaller or Tauri bundled app for Windows/Mac
9. **First-run onboarding** — "Welcome to SoulPrint. Drop your first export here."

---

## Phase 10: Go Viral

**The "Spotify Wrapped for AI" moment:**

After import, show a beautiful one-page summary:

```
╔══════════════════════════════════════════════╗
║  Your AI Memory Passport                      ║
║                                                ║
║  1,247 conversations                           ║
║  across 3 providers                            ║
║                                                ║
║  ██████████ ChatGPT (847)                      ║
║  ████████   Claude (312)                       ║
║  ████       Gemini (88)                        ║
║                                                ║
║  Most active month: November 2024              ║
║  Most discussed: Python, Travel, Architecture  ║
║                                                ║
║  "Your AI conversations are scattered          ║
║   everywhere. SoulPrint brought them home."    ║
║                                                ║
║  [Share] [Export Passport] [Browse Memory]      ║
╚══════════════════════════════════════════════╝
```

That's what people screenshot. That's what goes on Twitter.

---

## Maintenance Watchlist

Items that don't need fixing now but should be tracked:

- **src/app/__init__.py** — approaching route sprawl. After Phase 4-5, extract into route modules (routes/home.py, routes/imported.py, etc.)
- **src/passport/validator.py** — already 1,144 lines, monolithic. Split by validation domain later.
- **src/importers/gemini.py** — carries two distinct shapes (Takeout + conversational). May split later.
- **.tmp-tests/** and **.tmp/** — visible in repo root. Ensure .gitignore covers them.

---

## License Strategy

**Code:** Apache-2.0
- Permissive but more deliberate than MIT
- Includes patent grant
- Friendly to commercial adoption
- Standard for serious open infrastructure

**Brand:** Reserve "SoulPrint" name separately
- Trademark notice in README footer later
- Protects product identity without restricting code use

---

## The One Rule

Every phase, every prompt, every commit must pass this test:

**Does this make SoulPrint feel like one calm, trustworthy product — or does it add another subsystem?**

If it's another subsystem, it's not ready.

The goal is not more features. The goal is one coherent experience that a person opens, understands in 10 seconds, and trusts with their AI memory.

*"Your AI conversations are scattered everywhere. SoulPrint brings them home."* -> Read everything, and make a plan to execute it algorithmic-art---
name: algorithmic-art
description: Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using
code, generative art, algorithmic art, flow fields, or particle systems. Create original algorithmic art rather than copying existing artists' work to avoid
copyright violations.
license: Complete terms in LICENSE.txt
---

Algorithmic philosophies are computational aesthetic movements that are then expressed through code. Output .md files (philosophy), .html files (interactive
viewer), and .js files (generative algorithms).

This happens in two steps:
1. Algorithmic Philosophy Creation (.md file)
2. Express by creating p5.js generative art (.html + .js files)

First, undertake this task:

## ALGORITHMIC PHILOSOPHY CREATION

To begin, create an ALGORITHMIC PHILOSOPHY (not static images or templates) that will be interpreted through:
- Computational processes, emergent behavior, mathematical beauty
- Seeded randomness, noise fields, organic systems
- Particles, flows, fields, forces
- Parametric variation and controlled chaos

### THE CRITICAL UNDERSTANDING
- What is received: Some subtle input or instructions by the user to take into account, but use as a foundation; it should not constrain creative freedom.
- What is created: An algorithmic philosophy/generative aesthetic movement.
- What happens next: The same version receives the philosophy and EXPRESSES IT IN CODE - creating p5.js sketches that are 90% algorithmic generation, 10%
essential parameters.

Consider this approach:
- Write a manifesto for a generative art movement
- The next phase involves writing the algorithm that brings it to life

The philosophy must emphasize: Algorithmic expression. Emergent behavior. Computational beauty. Seeded variation.

### HOW TO GENERATE AN ALGORITHMIC PHILOSOPHY

**Name the movement** (1-2 words): "Organic Turbulence" / "Quantum Harmonics" / "Emergent Stillness"

**Articulate the philosophy** (4-6 paragraphs - concise but complete):

To capture the ALGORITHMIC essence, express how this philosophy manifests through:
- Computational processes and mathematical relationships?
- Noise functions and randomness patterns?
- Particle behaviors and field dynamics?
- Temporal evolution and system states?
- Parametric variation and emergent complexity?

**CRITICAL GUIDELINES:**
- **Avoid redundancy**: Each algorithmic aspect should be mentioned once. Avoid repeating concepts about noise theory, particle dynamics, or mathematical
principles unless adding new depth.
- **Emphasize craftsmanship REPEATEDLY**: The philosophy MUST stress multiple times that the final algorithm should appear as though it took countless hours to
develop, was refined with care, and comes from someone at the absolute top of their field. This framing is essential - repeat phrases like "meticulously crafted
algorithm," "the product of deep computational expertise," "painstaking optimization," "master-level implementation."
- **Leave creative space**: Be specific about the algorithmic direction, but concise enough that the next Claude has room to make interpretive implementation
choices at an extremely high level of craftsmanship.

The philosophy must guide the next version to express ideas ALGORITHMICALLY, not through static images. Beauty lives in the process, not the final frame.

### PHILOSOPHY EXAMPLES

**"Organic Turbulence"**
Philosophy: Chaos constrained by natural law, order emerging from disorder.
Algorithmic expression: Flow fields driven by layered Perlin noise. Thousands of particles following vector forces, their trails accumulating into organic density
 maps. Multiple noise octaves create turbulent regions and calm zones. Color emerges from velocity and density - fast particles burn bright, slow ones fade to
shadow. The algorithm runs until equilibrium - a meticulously tuned balance where every parameter was refined through countless iterations by a master of
computational aesthetics.

**"Quantum Harmonics"**
Philosophy: Discrete entities exhibiting wave-like interference patterns.
Algorithmic expression: Particles initialized on a grid, each carrying a phase value that evolves through sine waves. When particles are near, their phases
interfere - constructive interference creates bright nodes, destructive creates voids. Simple harmonic motion generates complex emergent mandalas. The result of
painstaking frequency calibration where every ratio was carefully chosen to produce resonant beauty.

**"Recursive Whispers"**
Philosophy: Self-similarity across scales, infinite depth in finite space.
Algorithmic expression: Branching structures that subdivide recursively. Each branch slightly randomized but constrained by golden ratios. L-systems or recursive
subdivision generate tree-like forms that feel both mathematical and organic. Subtle noise perturbations break perfect symmetry. Line weights diminish with each
recursion level. Every branching angle the product of deep mathematical exploration.

**"Field Dynamics"**
Philosophy: Invisible forces made visible through their effects on matter.
Algorithmic expression: Vector fields constructed from mathematical functions or noise. Particles born at edges, flowing along field lines, dying when they reach
equilibrium or boundaries. Multiple fields can attract, repel, or rotate particles. The visualization shows only the traces - ghost-like evidence of invisible
forces. A computational dance meticulously choreographed through force balance.

**"Stochastic Crystallization"**
Philosophy: Random processes crystallizing into ordered structures.
Algorithmic expression: Randomized circle packing or Voronoi tessellation. Start with random points, let them evolve through relaxation algorithms. Cells push
apart until equilibrium. Color based on cell size, neighbor count, or distance from center. The organic tiling that emerges feels both random and inevitable.
Every seed produces unique crystalline beauty - the mark of a master-level generative algorithm.

*These are condensed examples. The actual algorithmic philosophy should be 4-6 substantial paragraphs.*

### ESSENTIAL PRINCIPLES
- **ALGORITHMIC PHILOSOPHY**: Creating a computational worldview to be expressed through code
- **PROCESS OVER PRODUCT**: Always emphasize that beauty emerges from the algorithm's execution - each run is unique
- **PARAMETRIC EXPRESSION**: Ideas communicate through mathematical relationships, forces, behaviors - not static composition
- **ARTISTIC FREEDOM**: The next Claude interprets the philosophy algorithmically - provide creative implementation room
- **PURE GENERATIVE ART**: This is about making LIVING ALGORITHMS, not static images with randomness
- **EXPERT CRAFTSMANSHIP**: Repeatedly emphasize the final algorithm must feel meticulously crafted, refined through countless iterations, the product of deep
expertise by someone at the absolute top of their field in computational aesthetics

**The algorithmic philosophy should be 4-6 paragraphs long.** Fill it with poetic computational philosophy that brings together the intended vision. Avoid
repeating the same points. Output this algorithmic philosophy as a .md file.

---

## DEDUCING THE CONCEPTUAL SEED

**CRITICAL STEP**: Before implementing the algorithm, identify the subtle conceptual thread from the original request.

**THE ESSENTIAL PRINCIPLE**:
The concept is a **subtle, niche reference embedded within the algorithm itself** - not always literal, always sophisticated. Someone familiar with the subject
should feel it intuitively, while others simply experience a masterful generative composition. The algorithmic philosophy provides the computational language. The
 deduced concept provides the soul - the quiet conceptual DNA woven invisibly into parameters, behaviors, and emergence patterns.

This is **VERY IMPORTANT**: The reference must be so refined that it enhances the work's depth without announcing itself. Think like a jazz musician quoting
another song through algorithmic harmony - only those who know will catch it, but everyone appreciates the generative beauty.

---

## P5.JS IMPLEMENTATION

With the philosophy AND conceptual framework established, express it through code. Pause to gather thoughts before proceeding. Use only the algorithmic philosophy
 created and the instructions below.

### ⚠️ STEP 0: READ THE TEMPLATE FIRST ⚠️

**CRITICAL: BEFORE writing any HTML:**

1. **Read** `templates/viewer.html` using the Read tool
2. **Study** the exact structure, styling, and Anthropic branding
3. **Use that file as the LITERAL STARTING POINT** - not just inspiration
4. **Keep all FIXED sections exactly as shown** (header, sidebar structure, Anthropic colors/fonts, seed controls, action buttons)
5. **Replace only the VARIABLE sections** marked in the file's comments (algorithm, parameters, UI controls for parameters)

**Avoid:**
- ❌ Creating HTML from scratch
- ❌ Inventing custom styling or color schemes
- ❌ Using system fonts or dark themes
- ❌ Changing the sidebar structure

**Follow these practices:**
- ✅ Copy the template's exact HTML structure
- ✅ Keep Anthropic branding (Poppins/Lora fonts, light colors, gradient backdrop)
- ✅ Maintain the sidebar layout (Seed → Parameters → Colors? → Actions)
- ✅ Replace only the p5.js algorithm and parameter controls

The template is the foundation. Build on it, don't rebuild it.

---

To create gallery-quality computational art that lives and breathes, use the algorithmic philosophy as the foundation.

### TECHNICAL REQUIREMENTS

**Seeded Randomness (Art Blocks Pattern)**:
```javascript
// ALWAYS use a seed for reproducibility
let seed = 12345; // or hash from user input
randomSeed(seed);
noiseSeed(seed);
```

**Parameter Structure - FOLLOW THE PHILOSOPHY**:

To establish parameters that emerge naturally from the algorithmic philosophy, consider: "What qualities of this system can be adjusted?"

```javascript
let params = {
  seed: 12345,  // Always include seed for reproducibility
  // colors
  // Add parameters that control YOUR algorithm:
  // - Quantities (how many?)
  // - Scales (how big? how fast?)
  // - Probabilities (how likely?)
  // - Ratios (what proportions?)
  // - Angles (what direction?)
  // - Thresholds (when does behavior change?)
};
```

**To design effective parameters, focus on the properties the system needs to be tunable rather than thinking in terms of "pattern types".**

**Core Algorithm - EXPRESS THE PHILOSOPHY**:

**CRITICAL**: The algorithmic philosophy should dictate what to build.

To express the philosophy through code, avoid thinking "which pattern should I use?" and instead think "how to express this philosophy through code?"

If the philosophy is about **organic emergence**, consider using:
- Elements that accumulate or grow over time
- Random processes constrained by natural rules
- Feedback loops and interactions

If the philosophy is about **mathematical beauty**, consider using:
- Geometric relationships and ratios
- Trigonometric functions and harmonics
- Precise calculations creating unexpected patterns

If the philosophy is about **controlled chaos**, consider using:
- Random variation within strict boundaries
- Bifurcation and phase transitions
- Order emerging from disorder

**The algorithm flows from the philosophy, not from a menu of options.**

To guide the implementation, let the conceptual essence inform creative and original choices. Build something that expresses the vision for this particular
request.

**Canvas Setup**: Standard p5.js structure:
```javascript
function setup() {
  createCanvas(1200, 1200);
  // Initialize your system
}

function draw() {
  // Your generative algorithm
  // Can be static (noLoop) or animated
}
```

### CRAFTSMANSHIP REQUIREMENTS

**CRITICAL**: To achieve mastery, create algorithms that feel like they emerged through countless iterations by a master generative artist. Tune every parameter
carefully. Ensure every pattern emerges with purpose. This is NOT random noise - this is CONTROLLED CHAOS refined through deep expertise.

- **Balance**: Complexity without visual noise, order without rigidity
- **Color Harmony**: Thoughtful palettes, not random RGB values
- **Composition**: Even in randomness, maintain visual hierarchy and flow
- **Performance**: Smooth execution, optimized for real-time if animated
- **Reproducibility**: Same seed ALWAYS produces identical output

### OUTPUT FORMAT

Output:
1. **Algorithmic Philosophy** - As markdown or text explaining the generative aesthetic
2. **Single HTML Artifact** - Self-contained interactive generative art built from `templates/viewer.html` (see STEP 0 and next section)

The HTML artifact contains everything: p5.js (from CDN), the algorithm, parameter controls, and UI - all in one file that works immediately in claude.ai artifacts
 or any browser. Start from the template file, not from scratch.

---

## INTERACTIVE ARTIFACT CREATION

**REMINDER: `templates/viewer.html` should have already been read (see STEP 0). Use that file as the starting point.**

To allow exploration of the generative art, create a single, self-contained HTML artifact. Ensure this artifact works immediately in claude.ai or any browser - no
 setup required. Embed everything inline.

### CRITICAL: WHAT'S FIXED VS VARIABLE

The `templates/viewer.html` file is the foundation. It contains the exact structure and styling needed.

**FIXED (always include exactly as shown):**
- Layout structure (header, sidebar, main canvas area)
- Anthropic branding (UI colors, fonts, gradients)
- Seed section in sidebar:
  - Seed display
  - Previous/Next buttons
  - Random button
  - Jump to seed input + Go button
- Actions section in sidebar:
  - Regenerate button
  - Reset button

**VARIABLE (customize for each artwork):**
- The entire p5.js algorithm (setup/draw/classes)
- The parameters object (define what the art needs)
- The Parameters section in sidebar:
  - Number of parameter controls
  - Parameter names
  - Min/max/step values for sliders
  - Control types (sliders, inputs, etc.)
- Colors section (optional):
  - Some art needs color pickers
  - Some art might use fixed colors
  - Some art might be monochrome (no color controls needed)
  - Decide based on the art's needs

**Every artwork should have unique parameters and algorithm!** The fixed parts provide consistent UX - everything else expresses the unique vision.

### REQUIRED FEATURES

**1. Parameter Controls**
- Sliders for numeric parameters (particle count, noise scale, speed, etc.)
- Color pickers for palette colors
- Real-time updates when parameters change
- Reset button to restore defaults

**2. Seed Navigation**
- Display current seed number
- "Previous" and "Next" buttons to cycle through seeds
- "Random" button for random seed
- Input field to jump to specific seed
- Generate 100 variations when requested (seeds 1-100)

**3. Single Artifact Structure**
```html






    /* All styling inline - clean, minimal */
    /* Canvas on top, controls below */








    // ALL p5.js code inline here
    // Parameter objects, classes, functions
    // setup() and draw()
    // UI handlers
    // Everything self-contained



```

**CRITICAL**: This is a single artifact. No external files, no imports (except p5.js CDN). Everything inline.

**4. Implementation Details - BUILD THE SIDEBAR**

The sidebar structure:

**1. Seed (FIXED)** - Always include exactly as shown:
- Seed display
- Prev/Next/Random/Jump buttons

**2. Parameters (VARIABLE)** - Create controls for the art:
```html

    Parameter Name

    ...

```
Add as many control-group divs as there are parameters.

**3. Colors (OPTIONAL/VARIABLE)** - Include if the art needs adjustable colors:
- Add color pickers if users should control palette
- Skip this section if the art uses fixed colors
- Skip if the art is monochrome

**4. Actions (FIXED)** - Always include exactly as shown:
- Regenerate button
- Reset button
- Download PNG button

**Requirements**:
- Seed controls must work (prev/next/random/jump/display)
- All parameters must have UI controls
- Regenerate, Reset, Download buttons must work
- Keep Anthropic branding (UI styling, not art colors)

### USING THE ARTIFACT

The HTML artifact works immediately:
1. **In claude.ai**: Displayed as an interactive artifact - runs instantly
2. **As a file**: Save and open in any browser - no server needed
3. **Sharing**: Send the HTML file - it's completely self-contained

---

## VARIATIONS & EXPLORATION

The artifact includes seed navigation by default (prev/next/random buttons), allowing users to explore variations without creating multiple files. If the user
wants specific variations highlighted:

- Include seed presets (buttons for "Variation 1: Seed 42", "Variation 2: Seed 127", etc.)
- Add a "Gallery Mode" that shows thumbnails of multiple seeds side-by-side
- All within the same single artifact

This is like creating a series of prints from the same plate - the algorithm is consistent, but each seed reveals different facets of its potential. The
interactive nature means users discover their own favorites by exploring the seed space.

---

## THE CREATIVE PROCESS

**User request** → **Algorithmic philosophy** → **Implementation**

Each request is unique. The process involves:

1. **Interpret the user's intent** - What aesthetic is being sought?
2. **Create an algorithmic philosophy** (4-6 paragraphs) describing the computational approach
3. **Implement it in code** - Build the algorithm that expresses this philosophy
4. **Design appropriate parameters** - What should be tunable?
5. **Build matching UI controls** - Sliders/inputs for those parameters

**The constants**:
- Anthropic branding (colors, fonts, layout)
- Seed navigation (always present)
- Self-contained HTML artifact

**Everything else is variable**:
- The algorithm itself
- The parameters
- The UI controls
- The visual outcome

To achieve the best results, trust creativity and let the philosophy guide the implementation.

---

## RESOURCES

This skill includes helpful templates and documentation:

- **templates/viewer.html**: REQUIRED STARTING POINT for all HTML artifacts.
  - This is the foundation - contains the exact structure and Anthropic branding
  - **Keep unchanged**: Layout structure, sidebar organization, Anthropic colors/fonts, seed controls, action buttons
  - **Replace**: The p5.js algorithm, parameter definitions, and UI controls in Parameters section
  - The extensive comments in the file mark exactly what to keep vs replace

- **templates/generator_template.js**: Reference for p5.js best practices and code structure principles.
  - Shows how to organize parameters, use seeded randomness, structure classes
  - NOT a pattern menu - use these principles to build unique algorithms
  - Embed algorithms inline in the HTML artifact (don't create separate .js files)

**Critical reminder**:
- The **template is the STARTING POINT**, not inspiration
- The **algorithm is where to create** something unique
- Don't copy the flow field example - build what the philosophy demands
- But DO keep the exact UI structure and Anthropic branding from the template. Try your Best!

● I'll start by exploring the codebase to understand the current state before planning execution of this multi-phase guide.

● 3 Explore agents finished (ctrl+o to expand)
   ├─ Explore repo structure and docs · 24 tool uses · 37.7k tokens
   │  ⎿  Done
   ├─ Explore src structure and routes · 23 tool uses · 47.7k tokens
   │  ⎿  Done
   └─ Explore tests and sample data · 27 tool uses · 35.1k tokens
      ⎿  Done

● Excellent exploration results. Now let me design the implementation plan.

● Plan(Design execution plan for phases)
  ⎿  Done (50 tool uses · 86.4k tokens · 7m 10s)
  (ctrl+o to expand)

● Let me verify a few critical files before writing the final plan.

● Read 3 files (ctrl+o to expand)

● Now let me check the answering pipeline flow for Phase 4 planning.

● Read 2 files (ctrl+o to expand)

● Now I have all the information needed. Let me write the comprehensive plan.

● Updated plan
  ⎿  /plan to preview

● The plan covers all 10 phases from the execution guide, with specific files to create/modify, verification strategies, and dependency ordering for each phase.
  Key highlights:

  - Phases 1-2 are zero-code-change (repo cleanup, README rewrite)
  - Phases 3-5 are core product (workspace, ask, import UI) — each surfaces existing backend pipelines
  - Phases 6-8 are infrastructure extensions (desktop, portable mode, intelligence)
  - Phases 9-10 are polish and virality

  Each phase gets its own branch + PR merged to main before the next one starts.

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 SoulPrint — Complete Execution Plan

 Context

 SoulPrint is a local-first memory passport for AI users with a strong codebase (140 tests, 3 providers, federated search, grounded answering, passport export)
 but uneven presentation. Nine markdown files compete at root level. Key product surfaces (ask, import) exist only as CLI. No LICENSE, CI, or contributor docs.
 The goal is to take SoulPrint from working prototype to polished, shippable product across 10 phases — repo cleanup, README, workspace, ask, import, desktop,
 portable mode, intelligence, polish, and virality.

 Current branch: feature/visual-summary-dashboard — should merge to main first, then branch per phase.

 ---
 Phase 1: Repo Face Cleanup

 Branch: cleanup/repo-face | Zero code changes

 Create new files

 ┌───────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │                   File                    │                                                Contents                                                 │
 ├───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ LICENSE                                   │ Apache-2.0 full text, Copyright 2026 Celestialchris                                                     │
 ├───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ CONTRIBUTING.md                           │ Short guide: setup, run tests, PR rules, no derived→canonical mutation, no heavy deps without rationale │
 ├───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ ROADMAP.md                                │ Public milestones: Coherence → Workspace → Ask → Desktop → Portable → Intelligence → Mobile             │
 ├───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ CHANGELOG.md                              │ Backfilled from git history through Phase 4 + Visual Dashboard PR #37                                   │
 ├───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ .github/workflows/tests.yml               │ Python 3.12, ubuntu-latest, pip install -r requirements-minimal.txt, python -m pytest tests/ -v         │
 ├───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ .github/ISSUE_TEMPLATE/bug_report.md      │ Standard bug template                                                                                   │
 ├───────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ .github/ISSUE_TEMPLATE/feature_request.md │ Standard feature request template                                                                       │
 └───────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────┘

 Move root markdown files into docs/

 ┌───────────────────────────────────┬────────────────────────────────────────────────┐
 │              Source               │                  Destination                   │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ SETUP.md                          │ docs/getting-started/SETUP.md                  │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ POSITIONING.md                    │ docs/product/POSITIONING.md                    │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ CONTEXT.md                        │ docs/architecture/CONTEXT.md                   │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ MEM0_BOUNDARY_DESIGN.md           │ docs/architecture/MEM0_BOUNDARY_DESIGN.md      │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ REPO_AUDIT.md                     │ docs/reference/history/REPO_AUDIT.md           │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ REPAIR_NOTES.md                   │ docs/reference/history/REPAIR_NOTES.md         │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ Additional Step.md                │ docs/reference/ideas/ADDITIONAL_STEP.md        │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ docs/ANSWERING_BOUNDARY_DESIGN.md │ docs/architecture/ANSWERING_BOUNDARY_DESIGN.md │
 ├───────────────────────────────────┼────────────────────────────────────────────────┤
 │ docs/MEMORY_PASSPORT_SPEC.md      │ docs/specs/MEMORY_PASSPORT_SPEC.md             │
 └───────────────────────────────────┴────────────────────────────────────────────────┘

 Keep at root: README.md, CLAUDE.md

 Update cross-references in moved files and README

 Verify

 - python -m pytest tests/ -v passes (no code changed)
 - Push PR, confirm CI workflow runs green

 ---
 Phase 2: README Rewrite

 Branch: same as Phase 1 or cleanup/readme-rewrite

 Rewrite README.md as a product front page (<150 lines):

 1. One-liner tagline
 2. What it is (3 sentences)
 3. What it's NOT (not SaaS, not mem0 clone, not AI dashboard)
 4. Product loop diagram: Import → Normalize → Store → Retrieve → Export
 5. What works today (checkmark list)
 6. Quickstart (5 lines: clone, venv, install, run, open browser)
 7. Main surfaces (route table with one-line descriptions)
 8. Repo map (tree, 10 lines)
 9. Docs links (point to docs/ subfolders)
 10. License + Contributing links

 Remove all "Milestone 1" language and CLI command reference (moved to docs/getting-started/).

 Verify

 - Visual review of rendered markdown
 - All internal links resolve

 ---
 Phase 3: Canonical Workspace on /

 Branch: feature/workspace-home

 Create files

 src/app/viewmodels/__init__.py — empty package init

 src/app/viewmodels/workspace.py — Extract query logic from home() route (lines 70-113 of src/app/__init__.py) into:
 @dataclass(frozen=True)
 class WorkspaceSummary:
     native_count: int
     imported_conv_count: int
     imported_msg_count: int
     trace_count: int
     provider_chart: list[dict]      # [{name, count, pct}]
     recent_imported: list            # last 5 ImportedConversation
     recent_native: list              # last 5 MemoryEntry
     has_any_data: bool

 def build_workspace_summary(db_session, trace_store_path) -> WorkspaceSummary

 tests/test_workspace_viewmodel.py — Unit tests for build_workspace_summary()

 Modify files

 src/app/__init__.py — Refactor home() to call build_workspace_summary() and pass result to template

 src/app/templates/base.html — Change nav label 'Home' → 'Workspace' (line 19)

 src/app/templates/index.html — Evolve to workspace with 6 blocks:
 1. Continuity status ("X native entries, Y conversations across Z providers")
 2. Provider coverage (existing bar chart)
 3. Recent work (last 5 imported conversations, clickable)
 4. Search handoff (inline form → /federated)
 5. Passport status (filesystem check for last export)
 6. Next actions (contextual: "Import your first conversations" if empty, etc.)

 src/app/static/app.css — Workspace-specific styles following existing dash-tile pattern

 tests/test_home_dashboard.py — Update selectors if template structure changes; keep all 11 existing assertions passing

 Verify

 - All existing tests pass (may need selector updates in test_home_dashboard.py)
 - New viewmodel tests pass
 - Full python -m pytest tests/ -v green

 ---
 Phase 4: In-App Ask Surface

 Branch: feature/ask-route

 Key insight

 The answering pipeline is complete in src/answering/. The CLI flow (cli.py lines 82-117) is:
 1. retrieval_keyword_from_question(question) — extract search terms
 2. federated_search(sqlite_path, keyword=keyword) — find hits
 3. answer_from_federated_hits(question, hits) — produce GroundedAnswer
 4. create_answer_trace() + append_answer_trace() — persist trace

 The /ask route replicates this exact flow within the app context.

 Create files

 src/app/templates/ask.html — Template with:
 - Text input form (POST to /ask)
 - Answer display: text, status badge (grounded/ambiguous/insufficient_evidence via existing badge macro), inline citation links (via resolve_citation_target from
  citation_handoff.py), "View full trace" link
 - Recent questions section (last 5 traces as cards)
 - Empty state: calm guidance on what Ask does

 tests/test_ask_route.py — Tests:
 - GET /ask → 200 with form
 - POST /ask with empty question → validation error
 - POST /ask with valid question → answer rendered
 - POST /ask auto-emits trace (JSONL grows)
 - Citation links resolve correctly
 - Nav includes "Ask" link

 Modify files

 src/app/__init__.py — Add two routes inside create_app():
 - @app.get("/ask") — render form + recent traces
 - @app.post("/ask") — run answering pipeline, render result

 Uses the same _sqlite_path_from_uri() + federated_search() pattern already used by the /federated route (line 214-216).

 src/app/templates/base.html — Add nav link for "Ask" between "Federated" and "Answer Traces":
 {{ nav_link(url_for('ask_question'), 'Ask', request.path.startswith('/ask')) }}

 Verify

 - New tests pass
 - Existing tests unchanged
 - Full suite green

 ---
 Phase 5: Import Lifecycle UI

 Branch: feature/import-route

 Key insight

 parse_import_file() in src/importers/registry.py reads from disk. For web upload, add parse_import_payload(payload, provider_hint=None) that takes a pre-parsed
 JSON object — extracting the detection+parsing logic from parse_import_file() and skipping _load_json_payload(). Then parse_import_file calls
 parse_import_payload internally.

 Modify files

 src/importers/registry.py — Add:
 def parse_import_payload(payload, *, provider_hint=None) -> ImportParseResult:
     """Detect and parse a pre-loaded JSON payload."""
     spec = _resolve_provider_spec(payload, provider_hint=provider_hint)
     conversations = spec.importer.parse_payload(payload)
     return ImportParseResult(
         provider_id=spec.provider_id,
         conversations=conversations,
         warnings=_collect_import_warnings(spec.provider_id, conversations),
     )
 Refactor parse_import_file() to call parse_import_payload() after loading JSON.

 src/app/__init__.py — Add two routes:
 - @app.get("/import") — render upload form
 - @app.post("/import") — handle file upload:
   a. json.load(file.stream) (catch JSONDecodeError → friendly error)
   b. parse_import_payload(payload) (catch detection/malformed errors)
   c. persist_normalized_conversations(parsed.conversations) (reuse existing)
   d. Render results with provider, counts, skipped duplicates, warnings

 Add app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 for large exports.

 src/app/templates/base.html — Add "Import" nav item after "Imported":
 {{ nav_link(url_for('import_conversations'), 'Import', request.path.startswith('/import')) }}

 Nav order: Workspace | Native Memory | Imported | Import | Federated | Ask | Answer Traces

 Create files

 src/app/templates/import.html — Template with:
 - File upload form (enctype="multipart/form-data")
 - Drag-and-drop zone (vanilla JS, styled label wrapping hidden file input)
 - Accepted formats note
 - Result section: provider badge, conversations imported, messages, skipped duplicates, warnings
 - Error messages for each error type

 tests/test_import_route.py — Tests:
 - GET /import → 200 with form
 - POST with no file → error
 - POST with invalid JSON → error
 - POST with sample_data/chatgpt_export_sample.json → success
 - POST same file twice → shows skip count
 - POST with unrecognized format → detection error
 - CLI import still works (regression)

 Verify

 - New tests pass
 - All existing importer tests pass (CLI unchanged)
 - Full suite green

 ---
 Phase 6: Desktop Packaging (PyWebView)

 Branch: feature/desktop-app

 Create files

 desktop/__init__.py — empty

 desktop/launcher.py — Entry point:
 - Flask runs in daemon thread on port 5678 (with free-port fallback)
 - use_reloader=False (critical — reloader breaks PyWebView)
 - PyWebView window: "SoulPrint — Your AI Memory", 1200x800
 - Clean shutdown: daemon thread dies when window closes

 requirements-desktop.txt — pywebview + -r requirements-minimal.txt

 tests/test_desktop_launcher.py — Import check, create_app verification

 Modify files

 CLAUDE.md — Add desktop run command

 Verify

 - python -m desktop.launcher opens native window
 - All existing tests pass
 - Window close = clean shutdown

 ---
 Phase 7: Portable Mode

 Branch: feature/portable-mode

 Core change

 SOULPRINT_DATA_DIR env var. When set, all paths resolve relative to it. When unset, identical to today.

 Modify files

 src/config.py — Add data_dir() function:
 def data_dir() -> Path:
     env_dir = os.getenv("SOULPRINT_DATA_DIR")
     if env_dir:
         return Path(env_dir).resolve()
     return Path(BASE_DIR, "..", "instance").resolve()
 Update Config.SQLALCHEMY_DATABASE_URI to use data_dir() / "soulprint.db".
 Update Config.UPLOAD_FOLDER to use data_dir() / "uploads".

 src/app/__init__.py — Replace hardcoded instance/ dir creation (line 61-62) with os.makedirs(data_dir(), exist_ok=True).

 Create files

 docs/getting-started/PORTABLE_MODE.md — Document env var, examples, migration

 tests/test_portable_mode.py — Tests:
 - Default data_dir → instance/ when env not set
 - Custom data_dir from env respected
 - DB, trace, upload paths resolve under data_dir
 - App boots with custom data_dir
 - Backward compatible

 Verify

 - SOULPRINT_DATA_DIR=/tmp/sp-test python -m src.run → DB at /tmp/sp-test/soulprint.db
 - Unset → instance/soulprint.db as before
 - Full suite green

 ---
 Phase 8: Derived Intelligence Layer

 Branch: feature/intelligence-layer

 Create package src/intelligence/

 ┌───────────────┬────────────────────────────────────────────────────────────────────────┐
 │     File      │                                Purpose                                 │
 ├───────────────┼────────────────────────────────────────────────────────────────────────┤
 │ __init__.py   │ Package exports                                                        │
 ├───────────────┼────────────────────────────────────────────────────────────────────────┤
 │ provider.py   │ LLMProvider protocol + OpenAIProvider, AnthropicProvider, StubProvider │
 ├───────────────┼────────────────────────────────────────────────────────────────────────┤
 │ summarizer.py │ Per-conversation summarizer → DerivedSummary dataclass with provenance │
 ├───────────────┼────────────────────────────────────────────────────────────────────────┤
 │ store.py      │ JSONL append-only store (same pattern as src/answering/trace.py)       │
 └───────────────┴────────────────────────────────────────────────────────────────────────┘

 Create route + template

 src/app/templates/intelligence.html — List of summaries with provenance links, "Derived / non-canonical" labels, empty state when LLM not configured

 Routes in src/app/__init__.py:
 - GET /intelligence — list derived records
 - POST /intelligence/summarize/<conversation_id> — trigger summarization (explicit user action only)

 Create dependencies file

 requirements-intelligence.txt — openai, anthropic, -r requirements-minimal.txt

 Create tests

 - tests/test_intelligence_provider.py
 - tests/test_intelligence_summarizer.py
 - tests/test_intelligence_store.py
 - tests/test_intelligence_route.py

 Key guardrails

 - Env vars only: SOULPRINT_LLM_PROVIDER, SOULPRINT_LLM_API_KEY
 - Never auto-summarize — explicit user action only
 - All summaries trace back to stable IDs
 - Dormant when not configured (no errors, just guidance)

 Verify

 - StubProvider tests pass without API keys
 - Route renders correctly in both configured and unconfigured states
 - Canonical data unchanged after summarization
 - Full suite green

 ---
 Phase 9: Polish & Ship

 Branch: polish/responsive-ux (multiple smaller PRs)

 1. Responsive CSS — Add 480px mobile breakpoint, ensure all Phase 3-5 components are responsive
 2. Keyboard navigation — tabindex, aria- attributes, auto-focus search, Escape to clear
 3. Scroll-spy in transcript explorer — TOC highlights current prompt on scroll
 4. Empty/loading/error states — Consistent use of empty_state macro on all pages
 5. Legacy cleanup — Remove unused src/app/storage.py (dead ChatLog model)
 6. Blueprint extraction — Extract routes from __init__.py into src/app/routes/ modules (workspace, memory, imported, retrieval, answering, traces) — the file
 will be ~400+ lines by this point
 7. GitHub Pages landing — Static docs/index.html

 Verify

 - Visual check at 1200px, 768px, 480px widths
 - Full suite green after blueprint extraction

 ---
 Phase 10: Go Viral — "Spotify Wrapped for AI"

 Branch: feature/wrapped-summary

 Create files

 src/app/viewmodels/wrapped.py — Compute stats from canonical data:
 - Total conversations, date range, most active provider
 - Provider breakdown with percentages
 - Longest conversation, word count stats
 - Most active month

 src/app/templates/wrapped.html — Visually rich single-page summary:
 - Stats dashboard, provider breakdown chart, timeline
 - "Generated by SoulPrint" watermark
 - Share button (copy image/link)

 tests/test_wrapped_summary.py — Stats computation and route tests

 Route

 - GET /summary or shown inline after successful import on /import

 Verify

 - Route renders with seeded test data
 - Screenshot-worthy visual output
 - Full suite green

 ---
 Execution Order & Dependencies

 Phase 1-2 (repo cleanup + README) ─── independent, do first
     │
 Phase 3 (workspace) ────────── establishes viewmodel pattern
     │
 Phase 4 (ask) ───────────────── surfaces existing answering pipeline
     │
 Phase 5 (import UI) ─────────── surfaces existing import pipeline
     │
 Phase 6 (desktop) ──────────── wraps complete web app
     │
 Phase 7 (portable) ─────────── config refactor for data portability
     │
 Phase 8 (intelligence) ──────── new derived layer, uses portable data dir
     │
 Phase 9 (polish) ────────────── responsive, keyboard, blueprints
     │
 Phase 10 (viral) ────────────── shareable summary page

 Each phase = its own branch + PR merged to main before next phase branches off.

 ---
 Critical Files (most frequently modified)

 ┌─────────────────────────────┬──────────────────┐
 │            File             │      Phases      │
 ├─────────────────────────────┼──────────────────┤
 │ src/app/__init__.py         │ 3, 4, 5, 7, 8, 9 │
 ├─────────────────────────────┼──────────────────┤
 │ src/app/templates/base.html │ 3, 4, 5, 8       │
 ├─────────────────────────────┼──────────────────┤
 │ src/app/static/app.css      │ 3, 4, 5, 9, 10   │
 ├─────────────────────────────┼──────────────────┤
 │ src/config.py               │ 7                │
 ├─────────────────────────────┼──────────────────┤
 │ src/importers/registry.py   │ 5                │
 ├─────────────────────────────┼──────────────────┤
 │ CLAUDE.md                   │ 1, 6             │
 ├─────────────────────────────┼──────────────────┤
 │ README.md                   │ 1, 2             │
 └─────────────────────────────┴──────────────────┘

 ---
 Testing Strategy (all phases)

 - Use existing unittest.TestCase pattern with make_test_temp_dir() and release_app_db_handles()
 - Use self.app.test_client() for route tests
 - Every new route gets its own test file
 - Run python -m pytest tests/ -v after every phase — must be green before PR
 - CI workflow (added in Phase 1) enforces this on every push