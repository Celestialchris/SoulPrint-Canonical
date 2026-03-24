# SoulPrint Repo Audit — March 24, 2026

## Executive Summary

The architecture is sound. The code is real. The product is complete enough to ship. But the repo's public face has debris, inaccurate counts, missing visual proof, and organizational inconsistencies that undermine the "senior engineer built this" impression you need for launch. None of these issues are hard to fix — they're all hygiene. The problem is that every GitHub visitor makes a trust judgment in 10 seconds, and right now several things break that trust before they even read the README.

---

## Tier 1 — Embarrassing (Fix Before Any Public Post)

### 1. Two empty orphan files at repo root

| File | Size | Problem |
|------|------|---------|
| `answer_trace_list.html` | 0 bytes | Empty HTML file. Looks like abandoned scaffolding. |
| `test_answer_trace_browser.py` | 0 bytes | Empty test file. Signals incomplete work. |

**Fix:** Delete both. They add nothing and actively hurt credibility. If they were meant to become something, they never did.

### 2. README test counts are stale

The README says **"41 test files, 365 test methods"** in two places (Repo Map section and Tests section). The execution plan from March 17 already identified the actual count as **43 files, 367 methods**. The memory indicates it may now be as high as **93 Python files with ~390 test methods** (likely counting all Python files, not just test files).

**Fix:** Run `python -m pytest tests/ -v --co -q | tail -5` to get the actual count. Update both occurrences in README. From now on, use a rough range ("390+ test methods across 40+ files") rather than exact numbers that go stale, or commit to updating after every test addition.

### 3. README surface count mismatch

The README's "Surfaces" table lists 10 routes. The "Project Status" table says "10 web surfaces." The execution plan documents **18 live routes across ~12 distinct surfaces**. The Surfaces table is actually fine as a user-facing summary (users don't need to know about POST endpoints), but the "10 web surfaces" claim in Project Status should say "12 app surfaces" or just be removed since the table already communicates this.

**Fix:** Either update the Project Status row to match reality or remove it since the Surfaces table is the source of truth.

---

## Tier 2 — Looks Unpolished (Fix Before Week 1 Posts)

### 4. No screenshots in README

For a visual product with a carefully designed brand system (Torchlit Vault), the README has zero embedded images. The `docs/screenshots/` directory has workspace.png, explorer.png, federated.png, and passport.png — but none are referenced in the README. GitHub renders images inline. Every serious open-source project with a UI shows it.

**Fix:** Add at least one hero screenshot after the tagline, and a second after the "What SoulPrint Does" section. Use relative paths: `![Workspace](docs/screenshots/workspace.png)`. The screenshots currently show the old light parchment design — once the CSS alignment task ships Torchlit Vault to the live app, retake all screenshots.

### 5. `docs/manifesto.md` is a 6-line placeholder

From the execution plan: the manifesto is "6 lines, raw." A file called "manifesto" that contains almost nothing is worse than not having one. It signals abandonment.

**Fix:** Either expand to 10-15 lines in the brand voice (personal, direct, warm — matching the "Why I Built This" section in the README), or delete it and remove from `docs/README.md`. The README's "Why I Built This" section is already a better manifesto than a 6-line file.

### 6. `docs/executable-packaging-overview.md` describes an unshipped feature

This file sits at the top level of `docs/` and describes desktop packaging approaches that haven't been implemented yet. A casual reader might think it's documentation for existing functionality.

**Fix:** Move to `docs/reference/ideas/executable-packaging-overview.md`. Add a header line: `> **Status:** Speculative reference. Not yet implemented.`

### 7. `docs/reference/ideas/future-directions.md` is a pasted conversation

From the execution plan: "starts with 'Good — you're thinking about the right thing'" — reads like a raw Claude conversation dump, not a document. This is the kind of thing that makes someone think the repo is AI-generated slop rather than a considered engineering project.

**Fix:** Rewrite as a proper speculative-ideas memo. Keep the architectural substance (desktop packaging options, NotebookLLM-style intelligence, LLM architecture decisions). Strip all conversational tone. Add a non-authoritative header. Should read like an architecture memo, not a chat transcript.

### 8. ROADMAP.md Detail References may point to missing files

The ROADMAP references:
- `roadmap/UPGRADE-CONTINUITY.md`
- `roadmap/SOULPRINT-30-DAY-VISION.md`
- `DECISIONS.md`

The planning docs (SOULPRINT-EXECUTION-PLAN.md, SOULPRINT-30-DAY-VISION.md) are confirmed intentionally untracked/gitignored. If `roadmap/SOULPRINT-30-DAY-VISION.md` is gitignored, the ROADMAP is linking to a file that doesn't exist in the repo for any visitor.

**Fix:** Verify every reference. Remove links to gitignored/nonexistent files. Only reference files that exist in the committed repo.

---

## Tier 3 — Strategic Polish (Elevates Perception)

### 9. Repo Map section is incomplete

The "Repo Map" in README shows `src/`, `tests/`, `sample_data/`, `docs/`, `landing/` but omits:
- `roadmap/` — contains launch playbook, release notes, continuity docs
- `scripts/` — contains build scripts (Windows packaging)
- `.github/` — contains CI workflows, issue templates

**Fix:** Add these to the Repo Map for completeness. A complete map signals the author knows their own repo.

### 10. CHANGELOG lacks version headers

All entries are dated March 2026 with descriptive names ("Coherence Pass," "Lineage Suggestions") but no version numbers. This is fine for development, but before v0.1.0 ships, add `## v0.1.0 (2026-03-XX)` at the top as a release marker. Conventional changelogs group by version.

### 11. No SECURITY.md

For an open-source project handling people's conversation history, a SECURITY.md signals you take data handling seriously. Doesn't need to be long — just "how to report vulnerabilities" and a note that all data stays local.

### 12. Live CSS contradicts brand docs

This is the biggest UX gap, already documented in the execution plan. The live `app.css` uses light parchment, system fonts, card components — while every brand document, the landing page, and the design mock specify Torchlit Vault dark theme with Forum/Cormorant Garamond/JetBrains Mono.

**Fix:** Task 1 in the execution plan (CSS Alignment) addresses this. It's the highest-impact single change.

### 13. README Quick Start could be tighter

The current Quick Start is good but doesn't mention Python version requirement or virtual environment. A fresh clone might fail on Python 3.11 or hit package conflicts.

**Fix:** Add `python3.12 -m venv .venv && source .venv/bin/activate` before the pip install, or at minimum note "Requires Python 3.12+".

---

## Proposed File Actions (Concrete)

### Delete
```
answer_trace_list.html          # 0 bytes, orphaned
test_answer_trace_browser.py    # 0 bytes, orphaned
```

### Move
```
docs/executable-packaging-overview.md
  → docs/reference/ideas/executable-packaging-overview.md
```

### Rewrite
```
docs/reference/ideas/future-directions.md    # Strip conversational tone
docs/manifesto.md                            # Expand or delete
```

### Update
```
README.md                       # Fix counts, add screenshots, complete repo map, add Python version
ROADMAP.md                      # Remove dead references to gitignored files
CHANGELOG.md                    # Add v0.1.0 header when tagging
docs/README.md                  # Update index after file moves
```

### Create
```
SECURITY.md                     # Minimal vulnerability reporting + local-data note
```

---

## README Rewrite Priorities

The current README is 80% good. The structure is sound, the voice matches the brand, the CLI examples are accurate. The specific fixes are:

1. **Add a hero screenshot** — immediately after the tagline, before Quick Start
2. **Fix test counts** — both occurrences (Repo Map + Tests section)
3. **Fix surface count** — in Project Status table
4. **Add Python version to Quick Start** — mention 3.12+ requirement
5. **Complete the Repo Map** — add roadmap/, scripts/, .github/
6. **Add screenshot after "What SoulPrint Does"** — show the transcript explorer
7. **Remove or update "Desktop wrapper: Planned"** from Project Status if it's not in the current milestone

Everything else in the README is clean and well-written. Don't over-edit.

---

## The One Structural Problem Nobody Mentions

The repo has a `roadmap/` directory for planning docs, a `docs/` directory for architecture and product docs, and several root-level governance files (CHANGELOG, CLAUDE, CONTRIBUTING, DECISIONS, ROADMAP, README). This is fine and standard.

But the **Claude Project context** (what I'm looking at in `/mnt/project/`) is a flat dump of files from multiple repo directories. This means every time you start a Claude session for SoulPrint work, the AI sees brand.md, answering-boundary.md, positioning.md etc. as if they're root-level files — which can create confusion about where things actually live in the repo. The screenshots sitting here with timestamp names (`20260317_19_19_58.png`) add to the mess.

**Recommendation for Claude Project hygiene:**
- Remove the two empty orphan files from the project context
- Rename screenshots to descriptive names (`landing-page-hero.png`, `workspace-wordmark-glow.png`)
- Consider organizing the project files to mirror the repo structure, or at least group them mentally: root governance → architecture → product → planning

---

## Execution Order

```
Step 1:  Delete orphan files (2 minutes)
Step 2:  Fix README counts + add screenshots (15 minutes)
Step 3:  Move/rewrite docs debris (30 minutes)
Step 4:  Fix ROADMAP dead references (5 minutes)
Step 5:  Add SECURITY.md (10 minutes)
Step 6:  Complete Quick Start with Python version (5 minutes)
Step 7:  Run full test suite, verify CI green
Step 8:  Commit: "repo hygiene: fix counts, remove orphans, clean docs"
```

Total estimated time: under 90 minutes of Claude Code work.

After this, the repo looks like a senior engineer maintains it. Then you run the four execution plan tasks (CSS alignment, docs cleanup, Wrapped page, freemium gate) and you're launch-ready.
