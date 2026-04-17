# Changelog

All notable changes to SoulPrint are documented here, backfilled from git history.

## Magenta Sanctum UI Chain (2026-04-17)
- **v0.6.0 release.** Six-phase UI revamp landing as a single authored product: Magenta Sanctum tokens + brand mark (Phase 1), local web fonts (Phase 1b), four-column shell (Phase 2), workspace as canonical spine (Phase 3), secondary pages coherence (Phase 4), workspace composition redesigned to mockup (Phase 5.6), and dead-code/doctrine/release finalize (Phase 5)
- Design doctrine now `docs/product/design-doctrine-magenta-sanctum.md`; supersedes the pre-0.6.0 "USB Drive" doctrine
- Shell reads editorial (pink brand accent, flat dark canvas, display serif wordmark); data reads flat (rows, hairline dividers, mono labels, tabular nums)
- Lane palette restored to vibrant pre-Phase-1 values: ChatGPT `#4ade80`, Claude `#a78bfa`, Gemini `#60a5fa`, Grok `#e879f9`
- CSS cachebust `?v=12 → ?v=13` — the release bump
- Version bump `0.5.0 → 0.6.0` in `pyproject.toml`
- `CLAUDE.md` Visual Direction section updated to name Magenta Sanctum v2 as the current doctrine

## Phase 5: Finalize (2026-04-17)
- Dead CSS removal: **391 lines, ~120 rules** deleted from `src/app/static/app.css` (1744 → 1353 lines, 22% reduction). Removed pre-Magenta sidebar BEM (`.sidebar__brand`, `.sidebar__wordmark`, `.sidebar__nav`, `.sidebar__footer`, etc.), sidebar drop-zone stack (`.drop-zone--compact`, `.sidebar__import*`), `.app-nav__link*`, `.mobile-bar*`, `.main-content*`, pre-Phase-5.6 workspace ruleset (`.workspace-welcome*`, `.workspace-grid`, `.workspace-block*`, `.workspace-counts*`, `.workspace-firstrun*`, unscoped `.workspace-stats`/`.stat-card*`), pre-Phase-5.6 workspace composition (`.conversation-list`, `.conversation-row*`, unscoped `.provider-list`/`.provider-row*`, `.workspace-section__title`), `.resume-grid*`, `.resume-list*`, `.dash-tile*`, `.dash-bar*`, `.dash-stats`, `.dash-provider-chart`, `.dash-chart__label`, `.provider-badges`, `.workspace-block__head`. Collapsed duplicate Phase 4 "Import + secondary coherence" block (82 lines). Cleaned transition selector list and responsive `@media` rules of dead-class references.
- Dead files deleted: `src/app/static/sidebar-import.js` (no-op after Phase 2 removed its sidebar drop-zone elements) and its `<script>` tag in `base.html`
- Dead Jinja macro removed: unused `nav_link` macro in `_ui.html` (its `.app-nav__link` CSS was removed above; all live nav links use `sidebar_item`)
- `CLAUDE.md` "Visual Direction" section rewritten to name Magenta Sanctum v2 as the current doctrine and declare the pre-0.6.0 "USB Drive" system superseded
- `CHANGELOG.md` backfilled with Phase 1, 1b, 2, 3, 5.6 entries (Phase 4 was already present) plus this finalize entry and the release meta-entry
- `README.md` top rewritten with two-audience framing ("Download" for non-devs, "Install from source" for devs); MCP server section moved below "Providers"; 4-layer architecture ASCII replaced with a one-line link to `CONTRIBUTING.md`
- `pyproject.toml` version `0.5.0 → 0.6.0`
- `base.html` CSS cachebust `?v=12 → ?v=13`
- First `app.css` header comment updated: `USB Drive Design System → Magenta Sanctum v2 Design System (v0.6.0)`

## Phase 5.6: Workspace Redesigned to Mockup Composition (2026-04-17)
- Workspace (`/`) replaces the Phase 3 five-section flat spine with the mockup's composition: greeting, three stat cards, three quick-action cards, recent conversations list
- Right context panel populated on workspace: Providers, Top Themes, Recent Activity
- Lane palette restored to pre-Phase-1 vibrant values (Grok `#e879f9` joined as 4th lane, dormant)
- Ambient gradient and grain overlay removed from main canvas — main is flat dark `--bg`, rail and sidebar lifted to `--bg-dark` for separation
- Topbar Export / Import actions added on workspace via `main-header__actions`
- Rail placeholders tinted with lane colors (Claude violet, ChatGPT green, Gemini blue)
- Phase 3 `.spine-*` CSS block deleted (superseded by the new composition)
- **CSS collision fix** ([5f0e26c](../../commit/5f0e26c)): Phase 5.6 rules for `.workspace-stats` / `.stat-card` / `.action-card` / `.recent-list` scoped under `.workspace-canvas` ancestor to beat pre-Phase-4 unscoped rules with the same class names that leaked padding, background, and column count through to the new layout. The unscoped rules themselves are removed in Phase 5 finalize (above)
- `base.html`: greeting "Chris" marked as placeholder until OAuth username ships ([e75670a](../../commit/e75670a))

## Phase 4: Secondary Pages Coherence Pass (2026-04-16)
- 15 non-workspace templates now populate the Phase 2 shell's `page_title` and `page_desc` blocks instead of duplicating the page title inside the body. Topbar carries identity; body carries content.
- Removed duplicate `<h1>` heroes from every secondary template (imported list/explorer, federated, ask, intelligence, distill, distill_result, passport, answer traces list/detail, continuity detail, notes list, memory detail, import, import_flash)
- `/import` rebuilt with the pre-Magenta warm-welcome design inside the new shell: centered trust line, dashed dropzone with lane-colored format chips (ChatGPT green, Claude gold, Gemini blue), and a green "local-first" CTA (`.cta-primary` — documented doctrine carve-out per Magenta Sanctum §2)
- Topbar title (`.main-header__title`) promoted from `<span>` to `<h1>` so every page has exactly one page landmark for screen readers (a11y regression fix caught in pre-landing review)
- New CSS tokens namespaced as `--cta-alive-bg/fg/bg-hover` so the green import CTA doesn't shadow the app-wide magenta `--cta-bg` family
- CSS cachebust bumped `?v=8 → ?v=10`
- Test assertions updated for the page-title restructure: `test_imported_explorer_falls_back_for_blank_title` now asserts the topbar `<h1 class="main-header__title">` instead of a body `<h1>`; `test_nav_includes_notes` now asserts the actual nav label "Your own notes" instead of the retired `<title>Notes · SoulPrint</title>` string

## Phase 3: Workspace as Canonical Spine (2026-04-16)
- Workspace (`/`) rebuilt as the five-section canonical spine: resume thread, provider lanes, recent memories, interpretation entry, continuity CTA. Every live workspace affordance returns to the workspace; no dead-end stats row
- Workspace is the authoritative "what am I looking at" surface — all other pages are entered from here or from the sidebar
- Workspace view model (`src/app/viewmodels/workspace.py`) extracted to pre-compute every section from the canonical ledger with explicit provenance
- Pre-Phase-5.6 composition: `.workspace-stats`, `.stat-card`, `.provider-list`, `.conversation-list`, `.conversation-row`, `.workspace-section__title` — later replaced by the mockup composition in Phase 5.6
- Passport manifest handling hardened for robustness against missing fields; distill count uncapped ([73472a6](../../commit/73472a6))

## Phase 2: Four-Column Shell (2026-04-16)
- Four-column shell per Magenta Sanctum doctrine v2: Rail (64px) + Sidebar (240px) + Main + Context panel (260px, auto-hidden via `:empty`)
- Sidebar nav groups finalized: Sanctum / Memory / Interpretation / Continuity — replaces pre-Phase-2 flat nav
- `sidebar_item` macro added to `_ui.html` with active state, lane accent, optional badge, and unread indicator
- Wordmark rendered as a magenta gradient chip — brand chip is the only branded decoration in the app shell
- `.shell` scoped block in `app.css` owns the four-column layout; legacy unscoped sidebar/main-content selectors left in place for the phase but superseded (cleaned up in Phase 5 finalize)
- Grok added as 4th provider lane (dormant) — `--lane-grok: #a78bfa` in Phase 2, revised to `#e879f9` in Phase 5.6 lane-palette restoration
- CSS cachebust `?v=7 → ?v=8`

## Phase 1b: Local Web Fonts (2026-04-16)
- Bundled Playfair Display (500, 700), DM Sans (400, 500, 600, 400-italic), and JetBrains Mono (400, 500) as local woff2 files in `src/app/static/fonts/`
- `@font-face` declarations added at the top of `app.css` with `font-display: swap` — no CDN requests, no Google Fonts dependency on the wire
- Magenta Sanctum typography tokens now resolve to the bundled fonts instead of the prior CDN stack
- Keeps the local-first promise intact: first run is self-contained, no outbound font requests

## Phase 1: Magenta Sanctum Tokens + Brand Mark (2026-04-16)
- New design token system — dark-first background scale (`--bg-darkest` through `--bg-hover`, Discord-derived grays), hot-pink accent (`--accent: #f472b6`), soft/glow accent variants, light-theme counterpart (`--accent: #db2777`)
- Magenta wordmark on a solid pink brand chip — `--brand-mark-bg/fg/radius` introduced
- CTA tokens route through `--accent` automatically (`--cta-bg`, `--cta-hover-bg`, `--cta-border`, `--cta-outline-text`)
- Display serif introduced (`--font-display: Playfair Display`) for personality in the shell; body remains `DM Sans`; mono remains `JetBrains Mono`
- Design doctrine v2 document added at `docs/product/design-doctrine-magenta-sanctum.md`, along with the reference mockup
- Grok (xAI) importer landed in the same window ([#101](../../pull/101)) — imported provider count goes from 3 to 4, prompting the lane palette to gain a 4th color

## Manifesto Rewrite (2026-04-09)
- Rewrote `docs/manifesto.md` with expanded positioning: extended cognition framing, security argument, and explicit principles (custody not access, provenance over convenience, local by architecture, intelligence without surveillance)
- README "Why This Exists" now links to the full manifesto
- Patch release 0.4.1 (docs-only; no behavioral or API changes)

## Gemini Takeout Parser (2026-03-30)
- Added Google Takeout MyActivity.json parser for Gemini conversations
- Time-proximity grouping reconstructs conversation boundaries from activity entries
- HTML-to-text extraction for Gemini model responses (safeHtmlItem)
- Deterministic synthetic conversation IDs for idempotent re-import
- Canvas and non-conversation activity entries silently filtered
- 31 new tests covering detection, parsing, grouping, persistence, edge cases
- beautifulsoup4 and lxml added to requirements

## FTS5 Message-Level Search (2026-03-28)
- SQLite FTS5 full-text search over imported messages and native notes
- BM25 ranking with Porter stemming and unicode61 tokenization
- `snippet()` with highlighted `<mark>` tags showing exact matches
- Deep links from search results to exact messages in explorer
- Auto-index on import, backfill CLI: `python -m src.retrieval.fts`
- Federated page: FTS mode when query present, browse mode when not

## Clip from Explorer (2026-03-28)
- Text selection in transcript explorer → floating "Clip to notes" button
- Saves note with automatic citation: conversation title, provider, message index
- Citation includes clickable source link back to exact message
- Auto-tagged "clipped" for easy filtering
- User stays on explorer page (no redirect)

## Handoff Briefing + File Proof (2026-03-28)
- Distill result: "Copy handoff to clipboard" produces AI-consumable briefing
- Briefing format: thread stats, decisions, open loops, key context
- Ends with "Please continue from this context." for immediate AI handoff
- Passport page: database file path disclosure ("It's yours")

## Repo Audit Reconciliation (2026-03-28)
- README: requirements-minimal.txt → requirements.txt
- README: test counts updated, surface count updated, obsidian/ added to repo map
- LAUNCH-PLAYBOOK: Torchlit Vault → USB Drive reference fixed
- PRODUCT-GRAMMAR-LOCK.md: noted as merged into brand.md and CLAUDE.md
- Freemium gate tests: investigated root cause (instance/license.key)

## Post-Import Flash Page (2026-03-27)
- New `/import/complete` route: post-import confirmation page with conversation stats
- Shows count of imported conversations and messages after a successful import

## Workspace Revamp (2026-03-27)
- Redesigned workspace (`/`) with hero section, stats row, and provider summary
- Cleaner layout with at-a-glance metrics for imported conversations

## Multi-Conversation Distillation (2026-03-24)
- New `/distill` route: select N conversations, condense into one paste-ready markdown handoff
- Core module: `src/intelligence/distill.py` with structured prompt, bounded output, provenance
- JSONL store for distillation results (`derived_distillations.jsonl`)
- Selection UI with checkboxes, select-all, count indicator
- Result page with copy-to-clipboard, full provenance, and source conversation links
- Pro-gated (requires license key)
- 20 test methods in `tests/test_distillation.py`

## Obsidian Bridge (2026-03-17)
- One-way export from SoulPrint canonical ledger to an Obsidian vault
- Structured markdown notes with frontmatter, wiki-links, and auto-markers
- Theme notes from topic scans, daily-note anchors, provider notes, category notes
- Incremental export (skips existing files) and refresh mode (updates auto-blocks, preserves user content)
- Dry-run flag for preview without writing
- CLI: `python -m src.obsidian.cli --db <path> --vault <path>`
- Full renderer with slugification, Obsidian-native linking, and configurable vault structure
- 96 test methods across 3 test files

## Product Grammar Lock (2026-03-17)
- Locked user-facing language system for SoulPrint 0.1
- Two-layer promise: "brings them home" (archive hook) + "never start from scratch" (continuation hook)
- Warm nav labels frozen: "What you've discussed", "Ask your memory", "Everything, together", etc.
- CTA language: "Go deeper" for upgrade, "Bring conversations home" for import
- PRODUCT-GRAMMAR-LOCK.md added as implementation-ready language reference
  (Note: file was later merged into brand.md and CLAUDE.md)

## Freemium Gate (2026-03-16)
- Local-only license key validation (`instance/license.key`, prefix `SP-`)
- Free tier: all imports, browsing, search, export, passport, traces, wrapped summary
- Pro tier: Ask, Intelligence (summaries, topics, digests)
- Upgrade page with warm "Go deeper" messaging
- Dev override via `SOULPRINT_LICENSE_OVERRIDE=true`
- No server auth, no accounts, no network calls
- 14 new test methods across licensing and freemium gate test files

## Wrapped Summary Page (2026-03-16)
- Cinematic visual summary at `/summary` — always dark, standalone template
- Stats: total messages, conversations, providers, dominant provider, most active month, longest conversation
- Topic highlights from latest scan, unfinished threads detection
- Post-first-import redirect to `/summary` as onboarding wow moment
- "Generated by SoulPrint" watermark, screenshot-ready design
- Free tier — no license gate

## Brand Shell + CSS Alignment (2026-03-15)
- Complete CSS rewrite: Torchlit Vault dark default with Parchment Observatory light toggle
- Google Fonts: Forum, Cormorant Garamond, JetBrains Mono
- Opacity-based text hierarchy (t1/t2/t3/t4), wine + gold accents only
- Theme toggle with localStorage persistence
- Body atmosphere: grain overlay, vignette, layered radial gradients
- Wordmark glow treatment (dark mode only)
- All 17 templates verified against new design system

## Packaging Infrastructure (2026-03-15)
- Added `src/runtime.py` for centralized resource-path resolution (dev, editable install, frozen build)
- Added `src/main.py` as production launcher with browser auto-open
- Updated `src/config.py` and `src/app/__init__.py` to use runtime path resolution
- Full `pyproject.toml` with build-system, optional dependencies, and `soulprint` entry point
- Added `tests/conftest.py` and `pytest.ini` for stable test imports
- PyInstaller spec file (`SoulPrint.spec`) and Windows build script (`scripts/build_windows.bat`)
- Added `docs/executable-packaging-overview.md`
- Fixed ROADMAP.md dead references to gitignored files
- Fixed docs/getting-started.md test command (unittest → pytest)

## Coherence Pass (2026-03-15)
- Fixed `src/run.py` entrypoint: `python -m src.run` now actually starts the server
- Added `roadmap/` directory with 30-day vision and continuity architecture docs
- Updated ROADMAP.md to reflect completed continuity phases and fix broken references
- Removed phantom `chromadb` and `sentence-transformers` from requirements.txt
- Aligned CI to pytest (matching README, CONTRIBUTING, CLAUDE.md)

## Lineage Suggestions (2026-03-14)
- Implemented inspectable lineage suggestions: continuation, fork, revisit, supersede
- Lineage links are derived and non-authoritative — canonical ledger never mutated
- Added lineage surface in conversation detail views

## Bridge Assembly (2026-03-14)
- Bridge assembly for next-chat handoff from continuity packets and cited canonical snippets
- Bounded handoff payload size for real chat restarts
- Copy-to-clipboard workflow for pasting into next conversation

## Continuity Packet MVP (2026-03-13)
- Typed continuity artifacts: summary, decisions, open loops, entity map, bridge packet
- JSONL append-only persistence with full provenance metadata
- Generation through existing intelligence/provider boundary (BYOK)
- Continuity service with store, models, and generation pipeline
- POST endpoint for generation + GET for inspection + copy handoff

## Continuity Surface (2026-03-13)
- Added continuity detail page at conversation level
- Generation trigger, artifact inspection, and clipboard handoff

## Landing Page (2026-03-13)
- Static landing page in `landing/` directory
- Hero section, product loop visual, positioning sections
- GitHub Pages / Netlify ready

## CSS Restyle (2026-03-12)
- Full UI restyle: "Torchlit Vault" design system
- Dark warm palette, Forum/Cormorant Garamond/JetBrains Mono typography
- Hierarchy through opacity, wine and gold accents
- All 10 surfaces covered

## Repo Governance (2026-03-12)
- Added DECISIONS.md with frozen architectural, engineering, design, and product decisions
- Design system specification locked

## Intelligence Layer (2026-03-11)
- Per-conversation summaries via BYOK LLM provider
- Cross-conversation topic detection with keyword fallback
- Multi-conversation digest synthesis
- Intelligence routes and CLI tools

## Two-Layer Doctrine (2026-03-11)
- Rewrote CLAUDE.md with two-layer operator instructions (product/doctrine + visual direction)
- Added execution guide and visual direction docs

## Visual Summary Dashboard (2026-03-11)
- Added visual summary dashboard to home page with lane stats and recent activity

## CONTEXT.md (2026-03-11)
- Added project history and architectural decisions document

## Cross-LLM Importers (2026-03-10)
- Added Gemini importer with Google Takeout and Chrome extension support
- Three-provider story complete: ChatGPT, Claude, Gemini
- Provider-agnostic importer contract with auto-detection registry

## Memory Passport Validation (2026-03-10)
- Implemented passport validation logic with manifest, lane, and provenance checks
- Validation reports: `valid`, `valid_with_warnings`, `invalid`

## Citation Handoff (2026-03-10)
- Added Answer Trace citation handoff links to canonical views
- `memory:<id>` resolves to `/memory/<id>`, `imported_conversation:<id>` to `/imported/<id>/explorer`
- Hardened trace citation handoff mapping

## Answer Trace Browser (2026-03-10)
- Added read-only web answer trace browser at `/answer-traces`
- Per-trace detail view at `/answer-traces/<trace_id>` with derived labeling

## Browsing Layer (2026-03-10)
- Native memory detail page at `/memory/<id>` with federated handoff
- Read-only federated browser at `/federated` composing both lanes
- Imported conversation list at `/imported` with explorer handoff
- Transcript explorer at `/imported/<id>/explorer` with TOC and minimap

## Answering Layer (2026-03-09)
- Local grounded answering over federated retrieval
- Answer statuses: `grounded`, `ambiguous`, `insufficient_evidence`
- Compact lexical query term extraction
- CLI with `--emit-trace` and `--list-traces`

## Memory Passport Export (2026-03-09)
- v1 Memory Passport specification
- Export CLI producing manifest, JSONL lanes, provenance index
- Product positioning document

## mem0 Adapter Boundary (2026-03-09)
- Optional mem0 adapter with no-op defaults (`SOULPRINT_MEM0_ENABLED=false`)
- Boundary design memo

## Federated Retrieval (2026-03-09)
- Minimal federated retrieval composing native + imported lanes read-only
- Developer CLI for local inspection

## ChatGPT Importer (2026-03-09)
- ChatGPT export importer with normalized SQLite persistence
- Duplicate guard on `(source, source_conversation_id)`
- Query CLI: list, search, show, export-md
- Keyword search for imported conversations

## Milestone 1 Baseline (2026-03-08)
- Initial Flask app with SQLite canonical ledger
- Routes: `/`, `/save`, `/chats`
- `MemoryEntry` model with stable IDs
- Minimal requirements and setup docs
- Repo audit and smoke tests
