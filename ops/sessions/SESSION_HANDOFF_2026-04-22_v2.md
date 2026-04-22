# Session handoff — April 22, 2026 (updated end-of-day)

Updates since last handoff: CP1 merged (PR #139), CP5.1 merged, two security patches landed (CodeQL #12-15 closed, lxml CVE-2026-41066 patched). Branch state clean on main. This doc supersedes the earlier April 22 handoff.

---

## Where things stand

**main HEAD:** `5667cbd` (merge of feat/starring-everywhere) plus the two security followups. CodeQL alerts #12-15 should close on next scan. Dependabot lxml alert #1 resolved by 6.1.0 floor bump.

**Tests:** 930 passing. No pending regressions.

**What shipped in CP1:** `is_starred` column on both `ImportedConversation` and `MemoryEntry`. Four POST routes: `/imported/<id>/star`, `/imported/<id>/unstar`, `/memory/<id>/star`, `/memory/<id>/unstar`. Idempotent, redirect via `_safe_next` back to the page you starred from. Star toggle UI on six surfaces: `/federated` browse rows (both lanes), `/imported` list rows, `/chats` notes list, imported_explorer page header, memory_detail page header, and the archived list stays intentionally untouched.

**Security patches landed:**
- `_safe_next` hardened with `urlparse`-based validation plus reject-on-backslash. Closes the real `/\evil.com` browser-normalization bypass. CodeQL-recognized idiom, pattern captured in `ops/learned/codeql-taint-vs-relative-to.md`.
- lxml floor bumped to `>=6.1.0` for CVE-2026-41066. Actual exposure was zero (HTML parser path, not XML parser path), but pre-launch hygiene matters.

---

## First task tomorrow: star glyph consistency fix

### The problem

On `/imported` the filled `★` (Unstar state) renders visually smaller than the hollow `☆` (Star state). Two reasons:

1. `★` (U+2605) and `☆` (U+2606) have different metrics in most sans-serif fonts. The hollow outline reads bulkier because its stroke weight is constant across the glyph.
2. "Unstar" is two characters longer than "Star". On narrow viewports or long row content, the first row wraps while others don't.

### The fix

Use `★` always, let color carry the state. Accent when starred, muted when not. Text toggles Star/Unstar unchanged. This matches how GitHub, Twitter, and every well-designed starring UI handles it. Five templates, one-line change each.

### Template H prompt

**MANDATORY READS (first, in order, no exploration):**

1. `CLAUDE.md`
2. `context/soul.md`
3. `src/app/templates/federated.html` — the star toggle block from CP1, around line 167-180.
4. `src/app/templates/imported_list.html` — the star form block, around line 99-107.
5. `src/app/templates/view.html` — the star form block, around line 77-85.
6. `src/app/templates/imported_explorer.html` — the `page_actions` block at top.
7. `src/app/templates/memory_detail.html` — the `page_actions` block at top.

**Objective**

Normalize the star glyph across all five template surfaces. Use `★` regardless of state. Preserve the color-conditional (`var(--accent)` when active, `var(--t3)` when not). Preserve the Star/Unstar text toggle.

**Target state**

In each of the five templates, replace:

```jinja
{{ "★ Unstar" if <flag> else "☆ Star" }}
```

with:

```jinja
★ {{ "Unstar" if <flag> else "Star" }}
```

Where `<flag>` is whatever the template already uses (`conversation.is_starred`, `entry.is_starred`, `result.starred`, `e.is_starred`).

Nothing else changes. Inline styles, form actions, hidden `next` fields, spans, separators all stay.

**Scope lock — DO NOT EDIT**

- Anything under `src/` outside the five named template files.
- `app.css` (no CSS class promotion this pass — tracked as tech debt).
- Any Python file.
- Tests, except: the existing rendering smoke test in `tests/test_starring.py` asserts `☆ Star` appears in the response body. That assertion needs to become `★ Star`. Update in the same commit.

**Stop conditions**

- If a template doesn't match the expected pattern, stop and report.
- If the `☆ Star` string appears anywhere else (fixture files, docs), grep for `☆` and report every hit.
- If the test suite drops below 930 passing.

**Git**

Single commit on `fix/star-glyph-unify`, branched from main:

```
fix(ui): unify star glyph, use color for state

Replaces conditional ★/☆ with always-★. Color carries the starred
state. Fixes visual size drift between filled and hollow star
glyphs in sans-serif fonts, and stabilizes line-wrap since glyph
width is constant across states.
```

No push until reviewed.

---

## Global tagging — deferred but specified

This is context for when tagging becomes the active work. Not tomorrow, probably not this week, but it's the next large feature after CP4.

### The current state of tagging

Tagging is partial and inconsistent across the app. Surfaces that currently have tags:

- **Clipped notes** auto-get `tags="clipped"` via `/api/clip` (see `src/app/__init__.py:526`).
- **Plain notes** created via `/save` get whatever the user types in the tag field, usually nothing.
- `/chats` filters by tag via `?tag=X` substring match on `MemoryEntry.tags`.

Surfaces that have no tags:

- `/federated` browse rows show no tag pills. Even rows that do have tags in the database don't surface them.
- `/imported` conversations have no tag column at all. Zero tagging on imported conversations.
- Search is keyword-FTS only, no tag filter.

You noticed this in the CP1 session when scrolling `/federated` and seeing only `clipped` tags on some items — everything else shows blank. That's accurate. Tagging as a global feature doesn't exist yet. It's been a per-row artifact of the clipping path.

### What "global tagging" should look like

Two separate concerns that share a data model:

**1. Imported conversations need a tagging surface.** Right now `ImportedConversation` has no tag column. Proposal:

- Add `tags: str` column to `ImportedConversation` (comma-separated, matching the `MemoryEntry.tags` convention).
- On import, auto-seed with the first meaningful word of the title as a suggestion. Skip stopwords (the, a, an, my, your). If the title is "Soulprint issue", tag seed is `soulprint`. If the title is "How do I bake carbonara", tag seed is `bake` or `carbonara` depending on how aggressive the stopword list is.
- Surface tags on `/imported` and `/federated` rows as editable chips (inline add/remove, same pattern as CP1 star).
- Bulk edit: select N conversations via the existing checkbox column, apply a tag to all at once. Same bulk-action shape as the existing export/delete flow.

**2. Native notes already have `tags`, but no bulk-edit and no tag cloud.** Lower priority; the per-note tag input already exists.

### Open questions to resolve before writing code

- **Schema shape.** Keep comma-separated string (matches current `MemoryEntry.tags`, one less migration) or promote to a proper `ConversationTag` table (normalized, supports tag renames across N rows atomically)? The plan in `soulprint-companion-layer-plan.md` CP3 argues for a separate table. Worth revisiting when this is active work.
- **Auto-tag source.** First word of title? Claude-Code auto-extract via the existing LLMProvider? Hybrid — naive word on import, Claude-Code enrichment on demand? The LLM option is slow but accurate. The first-word option is instant but noisy.
- **UX for bulk edit.** Where does the tag input live once N rows are selected? A modal? An inline editor at the top of the list? What happens to existing tags — append, replace, merge?
- **Tag normalization.** Lowercase on write? Strip whitespace? Reject empty? Max length?

These should be a spec session before a prompt session. Don't Template-H this one without settling the schema question first.

### Related deferred: auto-tag on `/save`

Plain notes created via `/save` currently get no auto-tag. Clipped notes get `clipped`. A symmetric auto-tag for plain notes (`authored`? `note`? `scratch`?) would make the tag vocabulary feel intentional instead of accidental.

This rolls into the tagging work. Don't do it in isolation.

---

## Design reference — for the tag work and beyond

Three dribbble shots saved for the tag-UI design session. Not prescriptions, just references.

- **Category picker on green/black** (Family & Friends screenshot). Interesting as a concept for the tag-creation or tag-edit modal. Rounded chip row, icon + color picker, clear action button. The green+black palette isn't SoulPrint's but the layout pattern is solid. https://dribbble.com/shots/24972600-finpal-AI-Finance-Assistant-App-Add-Category-Design-Pattern
- **Fill-style icon set 1.** https://dribbble.com/shots/20322285-UI-Icons-Exploration-Fill-style-02
- **Fill-style icon set 2.** https://dribbble.com/shots/20223813-UI-Icons-Exploration-Fill-style

The icon sets are reference material for the inevitable moment when SoulPrint needs a consistent icon vocabulary (currently: text glyphs and the occasional unicode symbol). When tags ship, tags with icons read more clearly than tags as plain text chips. Save for later; not a CP1-era concern.

---

## Known nits from CP1, not blocking

- Rendering smoke test only covers the unstarred state. The star-glyph fix above will rewrite the assertion. Add the starred-state assertion at the same time if the Claude Code session wants to go slightly over scope.
- `Query.get()` deprecation warnings in `test_starring.py` and `test_imported_archive.py`. Retrofit both to `db.session.get()` in one pass later.
- Inline styles on all star/archive buttons. Promote to `.row-action-btn` CSS class when tags ship and introduce a third row action. This is the natural moment to refactor.

---

## Next candidate queue, updated

In rough leverage order. Each sized for one-session-one-prompt.

1. **Star glyph fix** (above) — 15 minutes. Ships the CP1 polish cleanly.
2. **CP4 "Continue in X" clipboard buttons** — pure frontend, half day. High demo value for Reddit launch. Composes with Distill and Continuity Packets.
3. **Global tagging** (spec first, prompt second) — multi-session. Schema decision drives everything else. Don't start without a settled spec.
4. **CP7 Wrapped v2** — two to three days. Share-worthy feature for r/MyBoyfriendIsAI. Extends `/summary`.
5. **CP8 Persona Extract** — three to four days. Killer feature. Sequence after CP7.
6. **Landing page refresh** (`feat/landing-quiet-archive`) — longest-standing queued item. Remove USB-stick tagline, remove Google Fonts CDN, correct accent tokens.

Recommendation: star glyph first (unblocks the last visual nit from CP1), then CP4 (small, shippable, demo-worthy), then sit down with the tagging spec before writing any tagging code.

---

## CE:work workflow note

Retained from the earlier handoff because it's still true: `/compound-engineering:ce-work` runs a parallel-explore phase even when the prompt has an explicit mandatory-read file list. For file-list-driven prompts, plain `/plan` or direct execution saves ~150k tokens of exploration. Reserve `ce-work` for tasks that genuinely need codebase discovery.
