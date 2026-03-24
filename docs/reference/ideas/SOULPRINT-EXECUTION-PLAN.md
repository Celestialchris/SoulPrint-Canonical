# SoulPrint — Execution Plan (Final)

**Date:** March 17, 2026
**Author:** Chris (via Claude synthesis of all planning artifacts + skill inventory)
**Purpose:** Single paste-ready document for Claude Code. Contains repo reality, skill mappings, prioritized tasks, and surgical prompts.

---

## Part 1 — What Actually Exists (Code, Not Plans)

### Verified Repo State (from zip inspection March 17)

| Component | Files | Tests | Status |
|-----------|-------|-------|--------|
| Canonical SQLite ledger | `src/app/models/` | ✓ | Stable |
| ChatGPT importer | `src/importers/chatgpt.py` | 13 test files | Stable |
| Claude importer | `src/importers/claude.py` | (cross-LLM tests) | Stable |
| Gemini importer | `src/importers/gemini.py` | 17 test files | Stable |
| Importer contracts + registry | `src/importers/contracts.py`, `registry.py` | ✓ | Stable |
| Flask web app | `src/app/__init__.py` (641 lines, 18 routes) | ✓ | Stable |
| Federated retrieval | `src/retrieval/federated.py` | ✓ | Stable |
| Grounded answering | `src/answering/local.py` | ✓ | Stable |
| Answer trace audit | `src/answering/trace.py` | ✓ | Stable |
| Intelligence (summaries, topics, digests) | `src/intelligence/` | ✓ | Stable |
| Continuity engine (packets, bridge, lineage) | `src/intelligence/continuity/` | 39+ tests | Stable |
| Continuity surface (POST + GET routes) | Routes in `src/app/__init__.py` | ✓ | Stable |
| Memory Passport export + validation | `src/passport/` | ✓ | Stable |
| Landing page | `landing/index.html` (Torchlit Vault, correct) | — | Shipped |
| Design mock | `src/app/static/app-mock.html` (47KB) | — | Reference |
| **Total** | **93 Python files** | **43 test files, 367 methods** | |

### The 18 Live Routes

```
GET  /                                    Workspace
GET  /passport                            Passport surface
POST /save                                Save native memory
GET  /imported/<id>/explorer              Transcript explorer
GET  /imported                            Imported conversation list
GET  /import + POST /import               Import lifecycle
GET  /chats                               Native memory list
GET  /memory/<id>                         Memory detail
GET  /federated                           Federated browser
GET  /answer-traces                       Trace list
GET  /answer-traces/<trace_id>            Trace detail
GET  /ask + POST /ask                     Grounded answering
GET  /intelligence                        Intelligence dashboard
POST /intelligence/summarize/<id>         Per-conversation summary
POST /intelligence/scan-topics            Topic detection
POST /intelligence/digest/<topic>         Digest synthesis
POST /intelligence/continuity/<id>        Generate continuity packet
GET  /intelligence/continuity/<id>        View continuity packet
```

### The One Critical Divergence

The **live app CSS** (`src/app/static/app.css`, 1594 lines) and the **brand docs** describe two completely different products:

| Property | app.css (what users see) | Brand docs / app-mock.html (what it should be) |
|----------|------------------------|-------------------------------------------------|
| Background | Light parchment `#f2f0e9` | Dark `#0e0d0b` |
| Fonts | `-apple-system`, system stack | Forum, Cormorant Garamond, JetBrains Mono |
| Containers | Cards with `border-radius: 18px`, shadows | No cards, no shadows, no radius |
| Accents | Blue-grey `#3f5f73` | Wine `#6b3a3a` + Gold `#a08848` |
| Text hierarchy | `--text`, `--muted`, `--accent` | `--t1`, `--t2`, `--t3`, `--t4` (opacity-based) |
| Theme toggle | None | Specified in `dual-theme-spec.md`, not built |

**Zero** instances of `Forum`, `Cormorant`, `JetBrains`, `0e0d0b`, or `Torchlit` appear in the live CSS.

### README.md Accuracy

- Claims "41 test files, 365 test methods" → **actual: 43 files, 367 methods**
- Claims "10 web surfaces" → **actual: 18 routes across ~12 distinct surfaces**

---

## Part 2 — Skill Inventory (Step 0 ✅ Complete)

### Available Skills

| # | Skill | Use For | Task Mapping |
|---|-------|---------|-------------|
| 1 | executing-plans | Execute written plans with review checkpoints | All tasks |
| 2 | verification-before-completion | Evidence-based verification before claiming done | All tasks (end) |
| 3 | finishing-a-development-branch | Merge/PR/cleanup workflow after implementation | All tasks (end) |
| 4 | dispatching-parallel-agents | Run 2+ independent tasks simultaneously | Tasks 1+2 (parallel) |
| 5 | brainstorming | Collaborative design exploration before creative work | Tasks 3, 4 |
| 6 | writing-plans | Create bite-sized implementation plans before coding | Tasks 3, 4 |
| 7 | test-driven-development | Red-Green-Refactor cycle for features/bugfixes | Tasks 3, 4 |
| 8 | subagent-driven-development | Execute plans via isolated subagents with review loops | Tasks 1, 3, 4 |
| 9 | using-git-worktrees | Isolated git worktrees for feature work | Tasks 3, 4 |
| 10 | requesting-code-review | Dispatch code review subagents after implementation | All tasks (end) |
| 11 | systematic-debugging | Four-phase debugging before proposing fixes | Any (if bugs) |

### Skill Loading Per Task

- **Task 1 (CSS):** `executing-plans` → `verification-before-completion` → `finishing-a-development-branch`
- **Task 2 (Docs):** `executing-plans` → `verification-before-completion`
- **Tasks 1+2 together:** Use `dispatching-parallel-agents` (they touch zero overlapping files)
- **Task 3 (Wrapped):** `brainstorming` → `writing-plans` → `test-driven-development` → `using-git-worktrees` → `subagent-driven-development` → `verification-before-completion` → `finishing-a-development-branch`
- **Task 4 (Freemium):** Same chain as Task 3 (Task 4 wraps Task 3's route, so must be sequential)

---

## Part 3 — Execution Sequence

```
Step 0: Skill Discovery        ✅ DONE
Task 1+2: CSS + Docs           → parallel via dispatching-parallel-agents
Task 3: Wrapped Summary Page   → sequential (most complex)
Task 4: Freemium Gate          → sequential (wraps Task 3's route)
Tag v0.1.0 → push → screenshot → post
```

---

## Task 1 — CSS Alignment (Highest Impact)

**Skills:** `executing-plans` → `verification-before-completion` → `finishing-a-development-branch`

### Claude Code Prompt

```
Use skills: executing-plans, verification-before-completion, finishing-a-development-branch

git checkout main && git pull
git checkout -b fix/css-brand-alignment

Read these files carefully before making any changes:
- docs/product/brand.md (frozen design tokens, both themes)
- docs/product/dual-theme-spec.md (exact CSS variable values, toggle spec)
- src/app/static/app-mock.html (canonical visual reference — 47KB)
- src/app/static/app.css (current CSS — this is what we're replacing)
- src/app/templates/base.html (template structure, nav, head)
- src/app/templates/_ui.html (Jinja macros)

Context:
The live app.css uses a light parchment palette (#f2f0e9), system fonts
(-apple-system), card components with border-radius and shadows, and a
blue-grey accent (#3f5f73). This contradicts every brand document.

The target is app-mock.html: Torchlit Vault dark theme with Forum,
Cormorant Garamond, JetBrains Mono fonts; opacity-based hierarchy
(t1/t2/t3/t4); wine + gold accents only; no cards, no shadows, no
border-radius on containers.

The landing page (landing/index.html) already uses the correct
Torchlit Vault palette. The app must match.

Objective:
Rewrite src/app/static/app.css to implement the Torchlit Vault
design system as the default theme, with Parchment Observatory
light theme as a data-theme="light" variant.

Starting State:
- app.css: 1594 lines, old light palette, system fonts, card-based
- app-mock.html: 47KB, correct Torchlit Vault, all 9+ surfaces mocked
- base.html: loads app.css, has nav with warm labels, no Google Fonts link
- 15 HTML templates consume the CSS
- 0 instances of Forum/Cormorant/JetBrains in current app.css

Target State:
- app.css implements Torchlit Vault (dark) as default
- All CSS variables match docs/product/brand.md exactly
- Google Fonts loaded in base.html <head>: Forum, Cormorant Garamond, JetBrains Mono
- data-theme="light" variant uses Parchment Observatory values from brand.md
- Theme toggle button in nav footer per dual-theme-spec.md
- localStorage persistence for theme choice, default: dark
- No cards, no badges, no box-shadows, no border-radius on containers
- Hierarchy through opacity (t1/t2/t3/t4)
- Wine (#6b3a3a) for CTAs/actions, gold (#a08848) for headings/provenance
- 2px vertical lane stripes for provider identity
- Body atmosphere (grain overlay, vignette, radial gradients) from dual-theme-spec.md
- Selection color: rgba(107, 58, 58, 0.30) dark / rgba(107, 58, 58, 0.18) light
- Wordmark glow text-shadow from dual-theme-spec.md (dark only)
- All 15 templates render correctly

Allowed Actions:
- Rewrite src/app/static/app.css entirely
- Edit src/app/templates/base.html (add Google Fonts link, theme toggle, data-theme on html)
- Edit src/app/templates/_ui.html if macro changes needed
- Minor class name adjustments in templates if CSS structure requires
- Add <script> in base.html for theme toggle (inline, no external JS)

Forbidden Actions:
- Do NOT change any Python code
- Do NOT change any route behavior or logic
- Do NOT modify app-mock.html (it is the reference)
- Do NOT add npm, webpack, or build tooling
- Do NOT change nav link text (warm labels are frozen)
- Do NOT change nav link order or route structure

Stop Conditions:
Pause and ask before:
- Removing any Jinja block or macro from templates
- Changing the nav structure or adding new nav items
- Adding any file outside src/app/static/ or src/app/templates/

Checkpoints:
After each major step output: ✅ [what was completed]
Final output: list every file changed, confirm all templates verified.

Verification (per verification-before-completion skill):
Before claiming done, provide evidence:
- Confirm Google Fonts link present in base.html
- Confirm 0 remaining instances of -apple-system in app.css
- Confirm 0 remaining instances of #f2f0e9 as default (should only appear in light variant)
- Confirm python -m pytest tests/ -v output (all green)

Then use finishing-a-development-branch to merge.
```

---

## Task 2 — README + Docs Cleanup

**Skills:** `executing-plans` → `verification-before-completion`

**Note:** Run in parallel with Task 1 via `dispatching-parallel-agents` — zero file overlap.

### Claude Code Prompt

```
Use skills: executing-plans, verification-before-completion

git checkout main && git pull
git checkout -b fix/docs-accuracy

Read:
- README.md
- ROADMAP.md
- docs/README.md
- docs/manifesto.md
- docs/executable-packaging-overview.md
- docs/reference/ideas/future-directions.md

Tasks (do all in this branch):

1. README.md — fix inaccurate counts:
   - "41 test files" → "43 test files"
   - "365 test methods" → "367 test methods"
   - "10 web surfaces" → review actual route count and update
   - Verify every doc link resolves to a real file
   - Verify screenshot filenames match docs/screenshots/

2. docs/manifesto.md — expand to 10-15 lines matching brand voice
   from docs/product/brand.md. Keep it personal and direct.

3. docs/executable-packaging-overview.md — relocate:
   Move to docs/reference/ideas/executable-packaging-overview.md
   Add header: "Status: Not yet shipped. Speculative reference."
   Update docs/README.md index.

4. docs/reference/ideas/future-directions.md — clean up:
   Strip conversational tone. Keep architectural substance.
   Result should read like an architecture memo, not a chat transcript.

5. ROADMAP.md — verify all file references exist. Remove any that don't.

6. docs/README.md — update index to match actual file tree.

Forbidden: Do NOT edit Python code, tests, CLAUDE.md, DECISIONS.md, CONTRIBUTING.md, CHANGELOG.md

Verification (per verification-before-completion skill):
- Every link in README.md resolves to a real file
- Every link in docs/README.md resolves to a real file
- future-directions.md contains no conversational tone
- No file in docs/ is missing from docs/README.md index
```

---

## Task 3 — Wrapped Summary Page (Growth Hook)

**Skills:** `brainstorming` → `writing-plans` → `test-driven-development` → `using-git-worktrees` → `subagent-driven-development` → `verification-before-completion` → `finishing-a-development-branch`

### Claude Code Prompt

```
Use skills: brainstorming, writing-plans, test-driven-development,
using-git-worktrees, subagent-driven-development,
verification-before-completion, finishing-a-development-branch

Phase 1 — Plan (writing-plans): produce implementation plan first.
Phase 2 — Execute (test-driven-development): write tests FIRST, then implement.

git checkout main && git pull
git checkout -b feature/wrapped-summary

Read:
- docs/product/brand.md (both palettes, typography, accent rules)
- docs/product/visual-direction.md
- src/app/static/app-mock.html (workspace hero treatment)
- src/app/viewmodels/workspace.py (existing viewmodel pattern)
- src/intelligence/continuity/store.py (for open_loops detection)

Context:
SoulPrint's "Spotify Wrapped for AI." The page people screenshot and share.
ALWAYS dark Torchlit Vault. Strongest glow surface in the product.

Required outcomes:

1. Create src/app/viewmodels/wrapped.py:
   - total_conversations (imported + native)
   - total_messages (headline number)
   - providers (list of dicts: name, count, percentage)
   - dominant_provider (name + count)
   - date_range (earliest to latest timestamps)
   - most_active_month
   - longest_conversation (title + message count)
   - topic_highlights (top 5 if topic data exists)
   - average_messages_per_conversation
   - unfinished_threads: count + top 3 titles

2. Add route: GET /summary in src/app/__init__.py
   Add "View your summary →" to workspace.

3. Post-first-import redirect:
   If DB had 0 conversations before import and now has >0 → redirect /summary
   Incremental imports: stay on import page + "See your updated summary →"

4. Create src/app/templates/wrapped.html (standalone, NOT extends base.html):
   - Background: #0a0908 with cinematic layered gradients + grain
   - Full viewport, no sidebar, no nav, max-width ~800px centered
   - HERO: wordmark with glow text-shadow + "Your AI Memory" + date range
   - HEADLINE STAT: total messages, Forum clamp(4rem,10vw,8rem), gold
   - SUPPORTING STATS: grid of 3 (providers, avg msgs, total convos)
   - PROVIDER BREAKDOWN: horizontal bars with lane colors
   - MOST ACTIVE MONTH + LONGEST THREAD
   - TOPICS (only if data exists — skip entirely if not)
   - UNFINISHED THREADS (always show, "Continue one →" link)
   - WATERMARK: "Generated by SoulPrint" + "soulprint.dev"
   - FOOTER: "Back to Workspace" + screenshot encouragement

5. Empty state: wordmark + "Import your first conversation" + wine CTA

6. FREE TIER. No license gate.

7. Tests (write FIRST): tests/test_wrapped_summary.py
   - Viewmodel stats correct from seeded data
   - GET /summary returns 200
   - Provider percentages sum to ~100
   - Empty DB renders graceful empty state
   - "Generated by SoulPrint" present
   - Topic section absent when no topic data
   - Unfinished threads count present even when zero
   - Post-first-import redirect to /summary

Strict rules:
- Only Wrapped. No licensing. No landing changes.
- ALWAYS dark. Does not respect theme preference.
- Do not modify existing test files.

Verification (per verification-before-completion):
- python -m pytest tests/test_wrapped_summary.py -v all green
- python -m pytest tests/ -v all green
- GET /summary returns 200
- Empty DB returns 200 with "Import your first conversation"

Then finishing-a-development-branch to merge.
```

---

## Task 4 — Freemium Gate

**Skills:** `brainstorming` → `writing-plans` → `test-driven-development` → `using-git-worktrees` → `subagent-driven-development` → `verification-before-completion` → `finishing-a-development-branch`

### Claude Code Prompt

```
Use skills: brainstorming, writing-plans, test-driven-development,
using-git-worktrees, subagent-driven-development,
verification-before-completion, finishing-a-development-branch

Phase 1 — Plan (writing-plans): produce plan first.
Phase 2 — Execute (test-driven-development): write tests FIRST.

git checkout main && git pull
git checkout -b feature/freemium-gate

Read:
- CLAUDE.md
- docs/product/brand.md
- src/app/__init__.py (all routes)
- src/app/templates/base.html
- src/app/templates/ask.html
- src/app/templates/intelligence.html
- src/app/templates/imported_explorer.html

Context:
Free tier must feel complete, not crippled. Pro adds depth, not access.
No accounts. No server auth. No network calls.

Free tier (no key): imports, browsing, passport, traces, summary, native memory
Paid tier (SP- key): Ask, Intelligence, Summarize on explorer

Required outcomes:

1. Create src/app/licensing.py:
   - is_licensed() → bool (file exists + starts with "SP-")
   - get_license_status() → {"licensed": bool, "tier": "free"|"pro"}
   - Dev override: SOULPRINT_LICENSE_OVERRIDE=true

2. Route gating:
   - GET /ask → upgrade.html if not licensed
   - POST /ask → 403 if not licensed
   - All intelligence POSTs → 403 if not licensed
   - Explorer → hide Summarize if not licensed
   - Free routes → completely unaffected

3. Create upgrade.html: "Go deeper" heading, warm invitation tone

4. Workspace tier indicator: "Free" or "Pro" badge

5. conftest.py: SOULPRINT_LICENSE_OVERRIDE=true (all existing tests pass)

6. New tests (write FIRST):
   - tests/test_licensing.py (5 cases)
   - tests/test_freemium_gate.py (6 cases)

Strict rules:
- No server auth. No accounts. No network calls.
- Free tier stays complete. Do not modify Wrapped feature.
- Only add conftest override to existing tests.

Verification:
- python -m pytest tests/ -v all green
- GET /ask without key returns upgrade page
- GET / shows "Free" tier badge
- All free routes return 200 without license key

Then finishing-a-development-branch to merge.
```

---

## Part 4 — Post-Execution Checklist

```bash
git tag v0.1.0
git push origin main --tags
cmd /c "scripts\build_windows.bat"    # Windows exe
```

Screenshot: workspace, explorer, federated, wrapped, import (all dark theme)
Update docs/screenshots/ with new images
README final pass with updated test counts

Launch: LAUNCH-PLAYBOOK.md has posts for r/ChatGPT, r/ClaudeAI, X, r/LocalLLaMA, r/selfhosted, HN
Timing: Tuesday–Thursday, 9–11am EST for Reddit

---

## Part 5 — Postpone List

SoulPrint Cloud, browser extension, desktop polish, additional providers, analytics, gamification, ambient recall, mem0, vector DB, cloud sync.

**First victory:** old chat in → conversations organized → Wrapped screenshot → posted online.

---

## Part 6 — Brand Quick Reference

**Fonts:** Forum (wordmark) · Cormorant Garamond (body) · JetBrains Mono (mono)

**Dark (Torchlit Vault, default):**
`--bg: #0e0d0b` · `--surface: #161513` · `--raised: #1d1b18`
`--wine: #6b3a3a` · `--gold-dim: #a08848` · `--gold: #c9a84c`
`--t1: rgba(210,200,185,0.90)` · `--t2: 0.55` · `--t3: 0.30` · `--t4: 0.12`

**Light (Parchment Observatory):**
`--bg: #f2f0e9` · `--surface: rgba(255,253,248,0.94)` · `--raised: #ffffff`
`--wine: #6b3a3a` · `--gold-dim: #7a6528` · `--gold: #8a7230`
`--t1: #1f2933` · `--t2: #3d4f5f` · `--t3: #667085` · `--t4: #a0a8b4`

**Rules:** Wine for CTAs only. Gold for headings only. No cards. No badges. No shadows. No icons in nav. No weight > 500.
Lane stripes: ChatGPT `#5a8a6a`, Claude `#a08848`, Gemini `#5a7a9a`
Wordmark glow: multi-layer text-shadow, dark mode only, wordmark only.

---

*The product is built. The architecture is clean. The brand is defined. The skills are loaded.*
*Run the four prompts. Tag v0.1.0. Post it. Ship today.*
