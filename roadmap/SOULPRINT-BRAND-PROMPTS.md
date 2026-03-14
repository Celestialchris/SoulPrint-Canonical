# SoulPrint — Claude Code Prompts: Brand, Landing Page & Distribution

Use these prompts one at a time. Branch, paste, test, merge. Same rhythm as always.

---

## Prompt 1 — Brand Identity & Logo

```
git checkout -b feature/brand-identity
```

```
Read CLAUDE.md and docs/product/visual-direction.md.

Task:
Create SoulPrint's brand identity assets and formalize the visual system.

Required outcomes:

1. Create docs/product/brand.md with:
   - Mission: "Every person should own their AI memory."
   - Tagline: "Your AI conversations are scattered everywhere. SoulPrint brings them home."
   - Voice: calm, confident, technical but not cold, trustworthy, never corporate
   - Primary palette:
     - Parchment background: #f2f0e9
     - Surface white: rgba(255,253,248,0.94)
     - Accent blue-grey: #3f5f73
     - Accent hover: #294656
     - Text primary: #1f2933
     - Text muted: #667085
     - Native lane: #eef5fa / #c2d6e3
     - Imported lane: #eff6f0 / #c4d8c4
     - Derived lane: #f9f2e8 / #e0c6a5
   - Typography: -apple-system, BlinkMacSystemFont, "SF Pro Text", 
     "Segoe UI", "Helvetica Neue", Arial, sans-serif
   - Logo usage rules

2. Create an SVG logo at src/app/static/logo.svg:
   - Concept: a stylized fingerprint that subtly suggests conversation 
     bubbles or layered memory
   - Keep it simple — must work at 24px favicon size and 200px hero size
   - Use the accent blue-grey (#3f5f73) as primary color
   - No text in the logo itself (wordmark is separate)
   - Clean vector paths, no gradients

3. Create a favicon at src/app/static/favicon.svg:
   - Simplified version of the logo for browser tabs
   - 16x16 and 32x32 should both be legible

4. Update src/app/templates/base.html:
   - Add favicon link in <head>
   - Replace text "SoulPrint" in brand-block with logo SVG + text
   - Keep the text alongside the logo (not logo-only)

5. Do not change any route behavior, tests, or backend logic.

Definition of done:
- Logo SVG exists and renders cleanly
- Favicon appears in browser tab
- Brand guide documents the full visual system
- All 216 tests still pass
```

---

## Prompt 2 — Landing Page

```
git checkout main && git pull
git checkout -b feature/landing-page
```

```
Read CLAUDE.md, docs/product/visual-direction.md, and docs/product/brand.md.
Also read .claude/skills/soulprint-design/SKILL.md if it exists.

Task:
Create a static landing page for SoulPrint that can be deployed 
to GitHub Pages or Netlify.

Context:
SoulPrint is a local-first memory continuity system for AI users.
The landing page is the first thing a potential user will ever see.
It must communicate what SoulPrint does in 10 seconds and make them 
want to try it.

Required outcomes:

1. Create landing/ folder at repo root with:
   - index.html (self-contained, no build step required)
   - style.css
   - assets/ folder for images and logo

2. Landing page structure (single page, scroll-based):

   HERO SECTION:
   - Logo + "SoulPrint" wordmark
   - Tagline: "Your AI conversations are scattered everywhere. 
     SoulPrint brings them home."
   - Subtitle: "A local-first memory continuity system. Import from 
     ChatGPT, Claude, and Gemini. Browse, search, discover, and export 
     your AI memory with provenance. Nothing leaves your machine."
   - Primary CTA: "Download for Windows" (link to GitHub releases)
   - Secondary CTA: "View on GitHub"
   - Hero screenshot placeholder (will replace with real screenshot later)

   PRODUCT LOOP SECTION:
   - Visual flow: Import → Browse → Search → Ask → Discover → Export
   - One sentence per step
   - Clean icons or simple illustrations for each

   WHAT IT IS NOT SECTION:
   - "Not a hosted SaaS — your data never leaves your machine"
   - "Not a mem0 clone — SoulPrint is for users, not developers"  
   - "Not an AI dashboard — no metrics theater, no admin panels"
   - "Not a wrapper — SoulPrint has its own canonical ledger"
   - This section is the differentiator. Make it feel confident, not defensive.

   FEATURES SECTION:
   - Three-provider import with auto-detection
   - Transcript explorer with prompt-level TOC
   - Cross-conversation topic discovery
   - AI-powered summaries and digests (with your own API key)
   - Memory Passport export with validation
   - Grounded answering with citation provenance

   TRUST SECTION:
   - "Everything stays local"
   - "Canonical records remain authoritative"
   - "Derived intelligence is always labeled and traceable"
   - "Apache-2.0 licensed — inspect the code yourself"

   EMAIL SECTION:
   - "Get notified when SoulPrint launches"
   - Simple email input + subscribe button
   - Note: use a placeholder action URL — we'll connect Buttondown later

   FOOTER:
   - Apache-2.0 license
   - GitHub link
   - "Built with local-first principles"

3. Design requirements:
   - Use the SoulPrint palette from brand.md
   - Responsive: looks great at 1440px, 1024px, 768px, 480px
   - Typography: use one distinctive display font from Google Fonts 
     for headings (suggest: "DM Serif Display" or "Fraunces"), 
     system stack for body text
   - Smooth scroll between sections
   - Subtle animations on scroll (fade-in, not flashy)
   - No JavaScript frameworks — vanilla JS only for scroll behavior
   - Must feel premium, calm, and trustworthy — not startup-flashy
   - Dark background for hero (contrast with the app's light theme),
     light background for feature sections

4. Do not modify any existing app code, templates, or tests.

Definition of done:
- landing/index.html opens in a browser and looks like a real product page
- Responsive at all breakpoints
- All sections present and properly styled
- No build step required — pure HTML/CSS/vanilla JS
- Existing 216 tests unaffected
```

---

## Prompt 3 — Desktop App (PyWebView)

```
git checkout main && git pull
git checkout -b feature/desktop-app
```

```
Read CLAUDE.md.

Task:
Create a PyWebView desktop wrapper for SoulPrint.

Context:
SoulPrint is a Flask + SQLite app. PyWebView wraps it in a native 
desktop window. This is the fastest path to "double-click to open" 
before investing in Tauri.

Required outcomes:

1. Create desktop/ folder at repo root:
   - desktop/__init__.py (empty)
   - desktop/launcher.py

2. launcher.py must:
   - Import create_app from src.app
   - Start Flask in a daemon thread on a free port (try 5678 first, 
     fall back to random available port)
   - Set use_reloader=False (critical — reloader breaks PyWebView)
   - Open a PyWebView window:
     - Title: "SoulPrint — Your AI Memory"
     - Size: 1200x800
     - URL: http://127.0.0.1:{port}
   - On window close: daemon thread dies automatically (daemon=True)
   - Print "SoulPrint is running at http://127.0.0.1:{port}" to console

3. Create requirements-desktop.txt:
   - pywebview
   - -r requirements-minimal.txt

4. Add desktop instructions to docs/getting-started.md:
   ```
   ## Desktop mode
   pip install -r requirements-desktop.txt
   python -m desktop.launcher
   ```

5. Create tests/test_desktop_launcher.py:
   - Test that desktop.launcher imports without error
   - Test that create_app() works when called from launcher context
   - Do NOT test PyWebView window creation (that requires a display)

6. Do not change any existing Flask app behavior, routes, or templates.

Definition of done:
- python -m desktop.launcher opens SoulPrint in a native window
- All app features work identically to browser mode
- Window close exits the process cleanly
- All existing tests still pass
- New launcher test passes
```

---

## Prompt 4 — Freemium Gate

```
git checkout main && git pull
git checkout -b feature/freemium-gate
```

```
Read CLAUDE.md.

Task:
Implement a simple local freemium gate for SoulPrint.

Context:
SoulPrint is local-first. There are no user accounts or servers.
The freemium gate uses a local license key file.

Free tier (always available, no key needed):
- All imports (ChatGPT, Claude, Gemini)
- All browsing (workspace, imported, native memory, federated, explorer)
- Memory Passport export + validation
- Answer traces browsing

Paid tier (requires valid license key):
- In-app Ask (/ask)
- Intelligence layer (/intelligence) — summaries, topics, digests
- Summarize button on explorer pages

Required outcomes:

1. Create src/app/licensing.py:
   - LICENSE_FILE_PATH = instance/license.key (or under data dir)
   - is_licensed() -> bool: checks if license key file exists and 
     contains a valid-looking key (non-empty, starts with "SP-")
   - get_license_status() -> dict with:
     - licensed: bool
     - tier: "free" or "pro"
   - For now, any key starting with "SP-" is valid
     (later: add online validation via LemonSqueezy API)

2. Update routes:
   - /ask: if not licensed, render a friendly upgrade page instead 
     of the ask form. Show what Ask does, show how to get a key.
   - /intelligence: if not licensed, show summaries/topics/digests 
     sections as locked with upgrade prompt. Keep the page visible 
     but actions disabled.
   - POST routes for ask, summarize, scan-topics, digest: return 
     403 with friendly message if not licensed.
   - /imported/<id>/explorer: hide "Summarize" button if not licensed.

3. Create src/app/templates/upgrade.html:
   - Clean page explaining what Pro tier unlocks
   - Instructions: "Place your license key in instance/license.key"
   - Link to purchase (placeholder URL for now)
   - "Already have a key? Restart SoulPrint to activate."

4. Add license status to workspace:
   - Show "Free tier" or "Pro" badge in workspace header
   - If free: subtle prompt "Unlock Ask and Intelligence features"

5. Add a dev/testing convenience:
   - SOULPRINT_LICENSE_OVERRIDE=true env var bypasses the gate
   - This lets developers and testers access everything

Guardrails:
- No server-side validation (local-first)
- No account creation
- No login flow
- No network calls for license validation (yet)
- No changes to import, browsing, passport, or trace behavior
- Free tier must feel complete and useful, not crippled

Tests required:
- test_licensing.py:
  - is_licensed returns False when no key file
  - is_licensed returns True with valid key
  - is_licensed returns False with empty file
  - license override env var works
- test_freemium_gate.py:
  - /ask renders upgrade page when not licensed
  - /ask renders form when licensed
  - /intelligence shows locked state when not licensed
  - POST /ask returns 403 when not licensed
  - POST summarize returns 403 when not licensed
  - workspace shows tier badge
  - free tier surfaces (import, browse, passport) work without key

Definition of done:
- App works fully without a license key (free tier)
- Ask and Intelligence are gated behind a key
- Upgrade prompts are clear and friendly, not hostile
- Dev override works for testing
- All existing tests pass (use override in test setup)
- New tests pass
```

---

## Prompt 5 — "Wrapped" Summary Page (Growth Hook)

```
git checkout main && git pull
git checkout -b feature/wrapped-summary
```

```
Read CLAUDE.md, docs/product/visual-direction.md, and 
docs/product/brand.md.

Task:
Create SoulPrint's "Wrapped" — a beautiful, shareable one-page 
summary of the user's AI memory.

Context:
This is the growth hook. When a user imports their AI conversations,
they should be able to generate a visual summary they'll want to 
screenshot and share. Think Spotify Wrapped but for AI conversations.

Required outcomes:

1. Create src/app/viewmodels/wrapped.py:
   - Compute stats from canonical data:
     - total_conversations (imported + native)
     - total_messages
     - providers (list with counts and percentages)
     - dominant_provider (name + count)
     - date_range (earliest to latest conversation)
     - most_active_month (month with most conversations)
     - longest_conversation (title + message count)
     - topic_highlights (top 5 from most recent topic scan, if any)
     - average_messages_per_conversation

2. Add route GET /summary
3. Add nav item "Summary" (or make it accessible from workspace)

4. Create src/app/templates/wrapped.html:
   - Full-page visual layout (not inside the normal app shell)
   - Dark gradient background (contrast with normal light app)
   - Large typography for headline stats
   - Provider breakdown with colored bars
   - Timeline or month chart
   - Topic highlights (if intelligence data exists)
   - "Generated by SoulPrint" watermark at bottom
   - "Share" button: downloads the page as an image 
     (use html2canvas from CDN, or just tell user to screenshot)
   - "Back to Workspace" link
   - "Get SoulPrint" link (for when someone sees a shared screenshot)

5. Design this to be screenshot-worthy:
   - Use the brand palette but with a dark/premium treatment
   - Bold stat numbers, refined labels
   - Smooth, minimal, magazine-like layout
   - Should look impressive in a Twitter/Reddit post
   - Must work at 1200px (desktop screenshot) and 768px (tablet)

6. This route is available on the free tier (it's a growth tool).

Tests required:
- test_wrapped_summary.py:
  - wrapped viewmodel computes correct stats from seeded data
  - /summary renders without error
  - provider breakdown percentages sum to ~100
  - empty database renders graceful empty state
  - page includes "Generated by SoulPrint" watermark

Definition of done:
- /summary shows a beautiful visual summary of the user's AI memory
- Stats are accurate and computed from canonical data
- The page looks premium enough to screenshot and share
- Free tier accessible (no license gate)
- All existing tests pass
```

---

## Execution Order

```
Prompt 1 (brand)     → merge to main
Prompt 2 (landing)   → merge to main  
Prompt 3 (desktop)   → merge to main
Prompt 4 (freemium)  → merge to main
Prompt 5 (wrapped)   → merge to main
```

Each one is self-contained. Each gets its own branch and PR.
Do not start the next until the current one is merged and tested.

---

## After All Five

You'll have:
- A branded product with a logo and visual identity
- A landing page people can visit
- A desktop app people can download
- A freemium model that feels fair
- A shareable growth hook that generates organic screenshots

That's a launchable product.
