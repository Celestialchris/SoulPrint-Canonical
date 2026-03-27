# SoulPrint Cleanup Checklist

*Generated March 27, 2026 from full surface audit (10 screenshots + 19 repo files).*

---

## Status: Three products pretending to be one

The repo docs describe Torchlit Vault (wine/gold, Forum/Cormorant). The live CSS implements USB Drive (green, system sans-serif). The workspace copy says "virtual USB stick" while governance docs ban it. This checklist reconciles everything to match the live product.

---

## Files to UPDATE (content changes needed)

### 1. brand.md → rewrite entirely
**Problem:** Describes Torchlit Vault tokens, wine/gold accents, Forum/Cormorant/JetBrains font stack, opacity-based hierarchy. None of this matches the live CSS.
**Fix:** Replace with USB Drive documentation. See `brand.md` in this package.

### 2. CLAUDE.md → update visual direction section
**Problem:** Line 75 says `Design system: "Torchlit Vault."` References dead docs.
**Fix:** Change to USB Drive reference. See `CLAUDE.md` in this package.

### 3. DECISIONS.md → update design section
**Problem:** Design section (lines 31-38) freezes Torchlit Vault with specific hex values.
**Fix:** Update to reflect USB Drive switch. See `DECISIONS.md` in this package.

### 4. visual-direction.md → simplify
**Problem:** References dead aesthetic system.
**Fix:** Keep design-system-agnostic principles. See `visual-direction.md` in this package.

### 5. README.md → accuracy pass
**Problem:** Claims "41 test files, 365 test methods" (now 48/504). Says "10 web surfaces" (actually 15+ routes, 12+ surfaces). Status table says "Brand system (Torchlit Vault) ✓ Frozen". Says "Freemium gate: Planned" but it's shipped.
**Fix:** Update all counts and references. See `README.md` in this package.

### 6. .claude/skills/soulprint-design/SKILL.md → rewrite tokens section
**Problem:** This is the file Claude Code reads before every frontend change. It contains full Torchlit Vault tokens, wine/gold colors, Cormorant Garamond references, and wordmark glow specs — all dead. This is the single most dangerous stale file.
**Fix:** See `soulprint-design-SKILL.md` in this package.

### 7. SOULPRINT-EXECUTION-PLAN.md → archive
**Problem:** Contains a 100-line Claude Code prompt to implement Torchlit Vault CSS. If pasted into Claude Code, it will destroy the current design. Also 27KB of planning that never became code.
**Fix:** Move to `docs/archive/execution-plan-march-2026.md` with archival header.

### 8. SOULPRINT-30-DAY-VISION.md → archive
**Problem:** Written March 13, targeted "mid-April 2026". Week 1 done, weeks 2-4 not. Contains stale parchment palette references. Historical, not operational.
**Fix:** Move to `docs/archive/30-day-vision-march-2026.md` with archival header.

### 9. LAUNCH-PLAYBOOK.md → update references
**Problem:** Several posts reference "Torchlit Vault" palette and stale screenshots. Pre-launch checklist references "Landing page matches brand — Torchlit Vault palette if dark, or Parchment if light".
**Fix:** Find-and-replace "Torchlit Vault" → remove or genericize. Update screenshot references.

### 10. PRODUCT-GRAMMAR-LOCK.md → reconcile with live app
**Problem:** Grammar lock bans "USB" language but the live workspace uses "A virtual USB stick for your AI life".
**Fix:** No doc changes needed — the grammar lock is correct. The APP needs the copy fix. See template fixes below.

---

## Files to DELETE

### answer_trace_list.html (project root)
- 0 bytes. Ghost file. The real template is at `src/app/templates/answer_trace_list.html`.

### test_answer_trace_browser.py (project root)
- 0 bytes. Ghost file. The real tests are in `tests/`.

---

## Files to MOVE

### SOULPRINT-EXECUTION-PLAN.md → docs/archive/
### SOULPRINT-30-DAY-VISION.md → docs/archive/

These are historical planning documents, not operational references. Keeping them in the project root makes the repo look cluttered and creates confusion about what's current.

---

## Template/CSS fixes (in the live app, not in this project)

### Workspace tagline
**File:** `src/app/templates/index.html`
**Current:** "A virtual USB stick for your AI life."
**Replace with:** "Your AI conversations are scattered everywhere. SoulPrint brings them home."
**Rationale:** CLAUDE.md line 70 and PRODUCT-GRAMMAR-LOCK.md both ban "USB" language. The locked tagline is the correct one.

### Answer traces file path
**File:** `src/app/templates/answer_trace_list.html`
**Current:** Shows `C:\Users\chr\SoulPrint-Canonical\instance\answer_traces.jsonl`
**Fix:** Show relative path or just "Local store: answer_traces.jsonl". Windows absolute paths expose personal directory structure.

### Provider pluralization
**File:** `src/app/templates/index.html` (workspace with data)
**Current:** "You have 41 conversations across 1 providers."
**Fix:** Handle singular/plural: "1 provider" vs "3 providers"

### Green button intensity
**Not a blocker, but:** The #4ade80 buttons are very bright on the dark background. Consider softening to ~#38d976 or reducing opacity slightly on non-hover state. This is a refinement, not a fix.

---

## Surface-by-surface audit (from 10 screenshots)

### 1. Workspace (empty state) ⚠️
- Banned tagline "A virtual USB stick for your AI life"
- Card container with border around CTA — minor, acceptable for hero
- Green CTA reads well: "Bring your first conversation home"
- Centered layout is good

### 2. Import ✅
- "Bring conversations home" heading matches grammar lock
- Drag-drop zone is clear
- "Your file is processed locally. Nothing leaves your machine." — good trust copy
- Green "Import now" button is clear

### 3. Ask your memory → Go deeper ✅
- Upgrade gate is warm, not hostile
- Copy is good: "Your imported conversations... always free"
- License instructions are clear
- "The free tier is complete, not a trial" — excellent

### 4. What you've discussed (empty) ✅
- Tabs "Your archive" / "Imported" — consistent
- Green search button
- Empty state message is helpful

### 5. Your own notes (empty) ✅
- Same pattern, consistent
- "Notes and entries you've created directly in SoulPrint" — clear

### 6. Everything, together (empty) ✅
- Good: "Results from all providers appear here together, each showing its source"

### 7. Themes & patterns ✅
- "Generated" badge (green outline) — correct derived labeling
- LLM not configured notice is helpful
- "Topic detection uses keyword fallback when no LLM is configured" — good
- "Scan topics→" button works

### 8. Distill → Go deeper ✅
- Same upgrade page as Ask — consistent gating

### 9. How answers were found ⚠️
- Shows Windows absolute path to answer_traces.jsonl — fix
- "Generated" badge — correct

### 10. Take it with you (Passport) ✅
- Most content-rich page
- Explains export and validation clearly
- CLI commands shown — appropriate for this audience
- "Current web inspection: not active" — honest
- Could benefit from an "Export now" button in the web UI eventually
