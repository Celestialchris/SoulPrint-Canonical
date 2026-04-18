# SoulPrint — Quiet Archive Coherence Pass

**Scope:** Close the documentation half of the Quiet Archive v3 migration. Single PR, no code or schema changes.
**Branch name (suggested):** `docs/quiet-archive-coherence-pass`
**Estimated size:** ~8 files touched, one directory added, three files archived, three files deleted.
**Preconditions:** v0.7.0-alpha.1 is the current `pyproject.toml` version; `src/app/static/app.css` is on Quiet Archive v3; `DECISIONS.md` 2026-04-17 row already supersedes Magenta.

---

## Why this PR exists now

`DECISIONS.md` explicitly notes that the Magenta Sanctum doctrine file "stays in-repo until Phase 4 archival." Phase 11 (soft launch) is the current milestone per `ROADMAP.md`, and Phase 11 includes "Fresh screenshots" and "Landing page refresh" — both of which require the documentation to be coherent with the live CSS first. Closing the archival now, one PR before the soft launch, means every contributor and AI agent doing Phase 11 work reads correct brand/visual tokens instead of stale ones.

The single highest-leverage problem this PR does **not** fix is the landing page, which is still dressed in USB Drive era tokens and loads Google Fonts from CDN. That needs its own PR (`feat/landing-quiet-archive`) because it requires visual judgment and fresh screenshots.

---

## Priority 1 — contributor-facing doctrine drift

### 1.1 — `docs/product/visual-direction.md` says "Current system: Magenta Sanctum"

**Evidence:** Line 11 of current file: `Current system: "Magenta Sanctum" — see docs/product/design-doctrine-magenta-sanctum.md for the authoritative doctrine.`

**Fix:** Replace file with the new version. The two-layer principle at the bottom is doctrinally correct and should survive unchanged; the supersession line is what flips.

**Deliverable:** `visual-direction.md` (produced alongside this plan).

### 1.2 — `docs/product/brand.md` still describes USB Drive

**Evidence:** Line 49 of current file: `## Design System: USB Drive` followed by the full USB Drive color table with `--accent: #4ade80` and `--lane-claude: #a78bfa`. Two doctrine generations behind.

**Impact:** Any agent (Claude Code, Codex, or human) told "consult the brand guide before touching UI" will be pointed at retired tokens. This is the most likely source of future stale-reference regressions.

**Fix:** Full rewrite. The Mission, Product Voice, Product Name, and Warm Nav Labels sections at the top are still correct — they're orthogonal to the visual system — and are preserved. The Design System section below them is replaced with Quiet Archive v3 content that matches `src/app/static/app.css` exactly.

**Deliverable:** `brand.md` (produced alongside this plan).

### 1.3 — Retired Magenta doctrine file still in `docs/product/`

**Evidence:** `docs/product/design-doctrine-magenta-sanctum.md` (16KB) sits next to the live doctrine. Its own header (line 3) already says `Status: Active` — which is now false. `DECISIONS.md` 2026-04-17 row says "Magenta Sanctum is retired; the doc stays in-repo until Phase 4 archival."

**Fix:** Move to archive and prepend retired-status header.

```bash
git mv docs/product/design-doctrine-magenta-sanctum.md docs/archive/
# Edit top of archived file: change line 3 header to:
#   **Status:** Retired as of 2026-04-17. Superseded by `docs/product/design-doctrine-quiet-archive.md`.
#   This file is preserved under `docs/archive/` for institutional memory only.
```

### 1.4 — Retired reference mockup still in `docs/product/mockups/`

**Evidence:** `docs/product/mockups/soulprint-discord-bun-mockup.html` is named as the Magenta Sanctum "visual ground truth" in the retired doctrine. Not authoritative anymore.

**Fix:**

```bash
mkdir -p docs/archive/mockups
git mv docs/product/mockups/soulprint-discord-bun-mockup.html docs/archive/mockups/
# If docs/product/mockups/ is now empty:
rmdir docs/product/mockups  # or: git rm -r docs/product/mockups (if tracked empty)
```

---

## Priority 2 — hygiene and discoverability

### 2.1 — `docs/README.md` has no Design section

**Evidence:** The docs index covers Getting Started, Product, Architecture, Specs, Reference, Releases, and Archive — but nowhere does it answer "what's the active design system?" A contributor has to `ls docs/product/` and guess between two doctrine filenames.

**Fix:** Add a Design section to the docs index between Product and Architecture:

```markdown
## Design
- [Quiet Archive v3 doctrine (active)](product/design-doctrine-quiet-archive.md)
- [Brand guide](product/brand.md)
- [Visual direction](product/visual-direction.md)
```

And remove Brand/Visual from the Product section (they live in Design now). Keep Manifesto and Positioning under Product.

### 2.2 — `AGENTS.md` references `ops/` directories that don't exist

**Evidence:** Lines from `AGENTS.md`:
- `6. Store session state in ops/sessions/.`
- `7. Store learned reusable patterns in ops/learned/.`

`ls ops` returns "No such file or directory."

**Fix:** Create the directories with one-line READMEs that formalize what goes in each. This makes AGENTS.md enforceable and gives Codex-style agents a real target.

```bash
mkdir -p ops/sessions ops/learned
cat > ops/sessions/README.md << 'EOF'
# Agent Session State

AI agents working on SoulPrint write their per-session state here —
one markdown file per session, named `YYYY-MM-DD-<short-slug>.md`.
Session state should capture: task scope, decisions made, open questions.

This directory is tracked for cross-session continuity. Files older than
six months may be moved to `docs/archive/ops-sessions/` during periodic cleanup.
EOF

cat > ops/learned/README.md << 'EOF'
# Agent Learned Patterns

Reusable patterns discovered during agent work — scoped, small, and
actionable. One file per pattern, named `<pattern-name>.md`.
Good candidates: naming conventions, common refactors, pitfalls to avoid.

Promoted from here into formal docs (`docs/architecture/` or
`DECISIONS.md`) once a pattern has stabilized across three or more uses.
EOF
```

Add `ops/` to the relevant `.gitignore` exclusion list (if any), but keep the directories themselves tracked.

### 2.3 — Unused `SP-drive.svg` assets (USB Drive era dead weight)

**Evidence:** `grep -rl "SP-drive"` returns zero references across `*.html`, `*.py`, `*.css`, `*.md`. These are orphan files.

**Files to delete:**

```bash
git rm src/app/static/SP-drive.svg
git rm sample_data/SP-drive.svg
git rm sample_data/SP-drive_q.svg
```

The `sample_data/` ones are the more urgent delete because `pyproject.toml`'s `include-package-data = true` would bundle them into `pip install` builds if they were ever referenced, and because the directory's stated purpose is test fixtures, not brand assets.

### 2.4 — `app.css` has two stale Magenta Sanctum comments

**Evidence:**
- Line 574: `/* Magenta Sanctum Shell — Phase 2. Scoped under .shell so the four-column [...] */`
- Line 1032: `/* cta-alive tokens were green (USB Drive / Magenta Sanctum era); Quiet Archive v3 repoints [...] */`

Line 1032 is already self-documenting and correct — it's literally explaining the migration. Leave it.

Line 574 should lose the "Magenta Sanctum Shell" phrasing and become:

```css
/* Four-column app shell — Phase 2. Scoped under .shell so the structure [...] */
```

The shell structure is invariant across doctrines; only the accent colors changed. Naming it by its structural role (four-column) rather than by its era-specific design system is more future-proof.

### 2.5 — Stale Torchlit references in active docs

**Evidence:**
- `docs/specs/obsidian-bridge-spec.md` — contains "torchlit" reference but the Obsidian Bridge shipped per `ROADMAP.md` Phase 12. Any styling guidance in the spec is now inconsistent with live CSS.
- `docs/releases/LAUNCH-PLAYBOOK.md` (26KB) — contains "torchlit" and "USB drive" references; being actively used for Phase 11 soft launch.

**Fix:** Grep and reconcile:

```bash
grep -niE "torchlit|usb drive|wine.gold" docs/specs/obsidian-bridge-spec.md docs/releases/LAUNCH-PLAYBOOK.md
```

For each hit: if it's a historical reference (e.g., "previously known as USB Drive"), leave it with a clarifying phrase. If it's prescriptive guidance ("use wine accent for identity surfaces"), replace with "use clay accent (`--accent`) for identity surfaces per `design-doctrine-quiet-archive.md`."

---

## Priority 3 — separate PR, but flag it now

### 3.1 — Landing page is two doctrines behind (soft-launch blocker)

**Evidence from `landing/index.html`:**

- Line 6: `<title>SoulPrint — A virtual USB stick for your AI life</title>` — USB Drive era tagline.
- Line 11: `<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">` — loads Google Fonts from CDN on every visit. **This directly contradicts the product's "nothing leaves your machine" promise.** The strongest thing SoulPrint sells, violated on its own marketing page.
- Line 15: `--accent:#4ade80` — USB Drive green, two doctrine generations out of date.
- Line 17: `--font-heading:'Outfit'` — not the bundled Playfair Display used by the app.
- `landing/assets/workspace.png` (404KB) — screenshot of the Magenta Sanctum workspace, not the current Quiet Archive look.

**Why it's a separate PR:** The landing page needs a full visual pass with fresh screenshots and likely some copy work. `ROADMAP.md` already names it as Phase 11 milestone work. Doing it alongside the coherence pass would make the review too visually loaded. Keep scopes separate.

**Seed for `feat/landing-quiet-archive`:**

1. Bundle Playfair Display and DM Sans locally under `landing/assets/fonts/` (same WOFF2 files that `src/app/static/fonts/` already has — copy them).
2. Delete the `<link>` to fonts.googleapis.com. Add `@font-face` declarations at the top of the `<style>` block pointing at the local fonts.
3. Retire the "virtual USB stick" tagline in the `<title>` and `<meta name="description">`. Candidate replacements that match the app's "Your AI conversations, home." line: *"SoulPrint — Your AI conversations, home."*
4. Swap the CSS tokens at the top of the `<style>` block to match Quiet Archive v3. The landing can mirror `src/app/static/app.css` tokens directly, or it can use a slightly bolder clay-gold presentation since it's "outside voice" marketing chrome (vs. the app shell's "inside voice"). The Quiet Archive doctrine already permits this — see its note on the wordmark Torchlit glow recipe being "outside voice" language.
5. Replace `landing/assets/workspace.png` with a fresh screenshot of the Quiet Archive workspace (Phase 11 already calls for fresh screenshots anyway — take one good shot and reuse it in both `docs/screenshots/` and `landing/assets/`).

**Verify before merging the landing PR:**

```bash
# No CDN phone-home:
grep -iE "googleapis|gstatic|cdn" landing/index.html
# Expected: zero matches.

# No stale accent:
grep "#4ade80" landing/index.html
# Expected: zero matches (it may legitimately appear as --green for status dots;
# if so, rename that token usage to match the app's --green #23955D).
```

---

## Execution checklist

Before opening the PR, run through this checklist:

1. Branch from latest main. Confirm `git log --oneline -1` matches your expected tip.
2. Apply Priority 1 changes in order 1.1 → 1.4. Run `pytest` after 1.4 to confirm no test references the moved doctrine filename (there shouldn't be any, but verify).
3. Apply Priority 2 changes in order 2.1 → 2.5. For 2.3 (the SVG deletes), confirm one more time with a fresh grep: `grep -rl "SP-drive" .` Expected: zero results.
4. Commit in logical groups. Suggested commit messages:
   - `docs: archive Magenta Sanctum doctrine and mockup (Phase 4 archival)`
   - `docs: rewrite brand.md and visual-direction.md for Quiet Archive v3`
   - `docs: add Design section to docs/README.md index`
   - `chore: create ops/sessions and ops/learned per AGENTS.md`
   - `chore: remove unused SP-drive.svg assets (USB Drive era)`
   - `style: retire stale Magenta Sanctum comment in app.css`
   - `docs: scrub Torchlit references from active specs and playbook`
5. Open PR titled `docs/quiet-archive-coherence-pass`. Body: one-paragraph summary + "Closes Phase 4 archival deferred in `DECISIONS.md` 2026-04-17 row."
6. Before merging: confirm `grep -rli "Current system.*Magenta" docs/` returns zero results and `grep -rli "Design System.*USB Drive" docs/` returns zero results.

---

## What this PR does not change

- No code in `src/`. No tests. No schemas. No imports, no retrieval, no passport, no answering.
- No landing page (separate PR).
- No `README.md` at root (already good post-v0.6.0 rewrite; a one-line "Active design system" pointer is optional polish, not required).
- No `CHANGELOG.md` historical entries (the v0.6.0 entry correctly records that Magenta shipped — rewriting history would be worse than leaving it).

---

## After the PR merges

Two small follow-ups worth flagging but not blocking:

**First**, `README.md` could optionally gain a small "Design" line in the `Architecture` / `For developers` section pointing to `docs/product/design-doctrine-quiet-archive.md`. It would read naturally as: *"Design doctrine: [Quiet Archive v3](docs/product/design-doctrine-quiet-archive.md)."* One line, high discoverability payoff for UI contributors. Skip if the README is already at a length you're happy with.

**Second**, consider adding a `CONTRIBUTING.md` section titled "Design contributions" that walks a would-be PR author through the authority order: *CSS is authority. Doctrine documents describe authority. Brand guide summarizes doctrine for humans. If you see disagreement, file an issue rather than editing freely.* This formalizes the doctrine culture that `DECISIONS.md` and the doctrine files already practice implicitly, and it is the kind of "pro senior user" signal a stranger picks up on immediately.
