# Workspace Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the workspace landing page and introduce Discord-inspired containers, purple interactive accent, and trust-centered layout.

**Architecture:** CSS-first — add new tokens and `.container-card` component to app.css, then update templates to use them. Viewmodel gets one additive field. Existing `.surface-card` usages are untouched.

**Tech Stack:** Flask/Jinja2, CSS custom properties, SQLAlchemy, pytest

**Spec:** `docs/superpowers/specs/2026-03-25-workspace-redesign-design.md`

**Implementation notes from user:**
1. When narrowing the `border-radius:0` override on line ~109, take the minimal approach — just remove the classes that need radius from the existing selector. Don't restructure the whole rule.
2. The post-import continuity sentence must use the simplified version (imported count + provider count only), not the old `continuity_sentence` that includes native/trace counts.

---

### Task 1: Unfreeze accent rule in DECISIONS.md and brand.md

**Files:**
- Modify: `DECISIONS.md:33-34`
- Modify: `docs/product/brand.md:84-89`

- [ ] **Step 1: Update DECISIONS.md design section**

Replace lines 33-34:

```
| 2026-03 | Design direction: "Torchlit Vault." Dark warm background (#0e0d0b), Forum display font, Cormorant Garamond body, JetBrains Mono for forensic data. | Quiet, warm, confident. Not dashboard. Not vault cosplay. Not AI toy. |
| 2026-03 | Hierarchy through opacity, not color. Four text opacity levels (t1/t2/t3/t4). Two accent colors only: wine (#6b3a3a) and gold (#a08848). | Prevents color proliferation. Typography carries structure. |
```

With:

```
| 2026-03 | Design direction: "USB Drive." Dark neutral background (#0e0f11), system sans-serif body, JetBrains Mono for forensic data. | Calm, trustworthy, local-first. Not dashboard. Not AI toy. |
| 2026-03 | Hierarchy through opacity, not color. Four text opacity levels (t1/t2/t3/t4). Two accents: green (#4ade80) for actions, purple (#7c5cbf) for interactive feedback. | Green = "do this." Purple = "you're here." Typography carries structure. |
```

Also replace lines 35-38:

```
| 2026-03 | No cards, no badges, no borders around containers, no shadows, no icons in nav, no bold >500 weight. | Content sits on the dark background with typography and spacing creating structure. Apple deference principle. |
| 2026-03 | Wine appears only on: primary CTA borders, active nav indicator, action buttons. Gold appears only on: page headings, provenance citation borders, main stat number. | Accent restraint. If everything glows, nothing is sacred. |
| 2026-03 | Provider lane colors as 2px vertical stripes: ChatGPT sage (#5a8a6a), Claude gold, Gemini steel (#5a7a9a), Native steel. | Lane identity through material, not SaaS badges. |
| 2026-03 | Design is frozen. No further design exploration until continuity MVP ships. | Coherence erosion is the main engineering risk. Ship the spine first. |
```

With:

```
| 2026-03 | No box-shadows on content containers. Flat containers with border-dividers. `.container-card` uses border-radius for grouped containers. No icons in nav, no bold >500 weight. | Container grouping via `.container-card`; flat rows inside via `.record-card`. |
| 2026-03 | Green for actions only: CTAs, active nav border, success badges. Purple for interactive feedback: hover, selection, active sidebar background. | Two accents, two cognitive signals. If everything glows, nothing is sacred. |
| 2026-03 | Provider lane colors as 2px left-border stripes: ChatGPT green (#4ade80), Claude purple (#a78bfa), Gemini blue (#60a5fa), Native blue. | Lane identity through color stripe, not badges. |
```

- [ ] **Step 2: Update brand.md accent rules**

Replace lines 84-89 in `docs/product/brand.md`:

```
## Accent Rules

- Green (#4ade80) is the ONLY accent color
- No second accent. No wine. No gold.
- Green is used for: CTAs, active nav indicator, badges, lane stripes, links on hover, trust signals
- Never use green as a large background fill (only ghost/muted variants)
```

With:

```
## Accent Rules

- Two accents: green (#4ade80) for actions, purple (#7c5cbf) for interactive feedback
- Green is used for: CTAs, active nav border, success badges, links on hover, trust signals
- Purple is used for: row hover states, sidebar active background, selected items
- No third accent color
- Never use either accent as a large background fill (only ghost/muted variants)
```

- [ ] **Step 3: Commit**

```bash
git add DECISIONS.md docs/product/brand.md
git commit -m "docs: unfreeze accent rule — two accents (green action, purple interactive)"
```

---

### Task 2: Add new CSS tokens and `.container-card` component

**Files:**
- Modify: `src/app/static/app.css:4-36` (token block)
- Modify: `src/app/static/app.css:109` (narrow border-radius override)
- Modify: `src/app/static/app.css` (add new rules after line ~191, the empty-state section)

- [ ] **Step 1: Add purple accent tokens to dark theme (line 12)**

After `--selection: rgba(74,222,128,0.20); --input-focus: var(--accent);` on line 12, add on the same line:

```
--accent-secondary: #7c5cbf; --accent-secondary-dim: #6b4dab; --accent-secondary-muted: rgba(124,92,191,0.15);
--radius-sm: 6px; --radius-md: 10px; --radius-lg: 14px;
--space-container: 16px;
```

- [ ] **Step 2: Add purple accent tokens to light theme (after line 32)**

After `--selection: rgba(22,163,74,0.15);` on line 32, add:

```
--accent-secondary: #6b4dab; --accent-secondary-dim: #5a3d96; --accent-secondary-muted: rgba(107,77,171,0.12);
```

No need to repeat radius/space tokens — they're theme-independent.

- [ ] **Step 3: Narrow the border-radius:0 override on line 109**

Current line 109:
```css
.page-header,.surface-card,.record-card,.content-block,.rail-panel,.transcript-panel,.route-card,.intelligence-section,.config-guidance{border-radius:0;box-shadow:none}
```

Remove `.record-card` from this selector (it needs hover radius inside `.container-card`). Result:
```css
.page-header,.surface-card,.content-block,.rail-panel,.transcript-panel,.route-card,.intelligence-section,.config-guidance{border-radius:0;box-shadow:none}
```

Minimal change — just remove `,. record-card` from the selector list.

- [ ] **Step 4: Add `.container-card` and scoped `.record-card` hover rules**

Add after the empty-state section (after line ~191), before the Grid section comment:

```css
/* Container card — grouped containers with background + radius */
.container-card{background:var(--surface);border-radius:var(--radius-md);padding:var(--space-container);border:1px solid var(--line)}
.container-card .record-card{padding:12px var(--space-container);margin:0 calc(-1 * var(--space-container));border-bottom:1px solid var(--line);border-radius:var(--radius-sm);background:transparent;transition:background var(--duration-fast) ease}
.container-card .record-card:last-child{border-bottom:none}
.container-card .record-card:hover{background:var(--accent-secondary-muted)}
.container-card__eyebrow{color:var(--t3);font-family:var(--font-mono);font-size:11px;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:12px}
.container-card__footer{margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}
```

- [ ] **Step 5: Add sidebar active background and hover rules**

Replace line 67:
```css
.app-nav__link--active{color:var(--t1);border-left-color:var(--accent)}
```

With:
```css
.app-nav__link--active{color:var(--t1);border-left-color:var(--accent);background:var(--accent-secondary-muted)}
.app-nav__link:hover:not(.app-nav__link--active){background:rgba(124,92,191,0.08)}
```

- [ ] **Step 6: Update empty-state to use container styling**

Replace line 187:
```css
.empty-state{padding:32px 20px;border:1px dashed var(--t4);border-radius:8px;background:none;text-align:center}
```

With:
```css
.empty-state{padding:32px 20px;background:var(--surface);border-radius:var(--radius-md);border:1px solid var(--line);text-align:center}
```

Note: padding stays at `32px 20px` (not `var(--space-container)`) because empty states need more breathing room than regular containers. This is an intentional deviation from the spec's `var(--space-container)` suggestion.

- [ ] **Step 7: Add mobile rules for container-card**

Add inside the `@media(max-width:760px)` block (line ~326), before the closing `}`:

```css
.container-card{border-radius:0;border-left:none;border-right:none;padding:12px}
```

Add after the 760px media block:
```css
@media(hover:none){.container-card .record-card:hover{background:transparent}}
```

- [ ] **Step 8: Run tests**

Run: `python -m pytest tests/ -v`
Expected: All pass (CSS changes don't break Python tests)

- [ ] **Step 9: Commit**

```bash
git add src/app/static/app.css
git commit -m "feat(css): add purple accent, container-card, sidebar active bg, empty-state restyle"
```

---

### Task 3: Add Forum font import to base.html

**Files:**
- Modify: `src/app/templates/base.html:11`

- [ ] **Step 1: Add Forum to Google Fonts import**

Replace line 11:
```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
```

With:
```html
<link href="https://fonts.googleapis.com/css2?family=Forum&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Commit**

```bash
git add src/app/templates/base.html
git commit -m "feat: add Forum font import for wordmark"
```

---

### Task 4: Add `provider_recent` to WorkspaceSummary viewmodel

**Files:**
- Modify: `src/app/viewmodels/workspace.py`
- Modify: `tests/test_workspace_viewmodel.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_workspace_viewmodel.py`, inside the `WorkspaceViewmodelTest` class:

```python
def test_provider_recent_includes_most_recent_per_provider(self):
    with self.app.app_context():
        # Seed 3 chatgpt conversations
        for i in range(3):
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id=f"chatgpt-{i}",
                title=f"ChatGPT conv {i}",
            )
            db.session.add(conv)
        # Seed 1 claude conversation
        conv_claude = ImportedConversation(
            source="claude",
            source_conversation_id="claude-0",
            title="Claude conv 0",
        )
        db.session.add(conv_claude)
        db.session.commit()

        summary = build_workspace_summary(trace_store_path=self._trace_path())

        self.assertEqual(len(summary.provider_recent), 2)
        # Ordered by count desc
        chatgpt_entry = summary.provider_recent[0]
        self.assertEqual(chatgpt_entry["provider"], "chatgpt")
        self.assertEqual(chatgpt_entry["count"], 3)
        self.assertEqual(chatgpt_entry["recent_title"], "ChatGPT conv 2")
        self.assertIsNotNone(chatgpt_entry["recent_id"])

        claude_entry = summary.provider_recent[1]
        self.assertEqual(claude_entry["provider"], "claude")
        self.assertEqual(claude_entry["count"], 1)
        self.assertEqual(claude_entry["recent_title"], "Claude conv 0")

def test_provider_recent_empty_when_no_imports(self):
    with self.app.app_context():
        summary = build_workspace_summary(trace_store_path=self._trace_path())
        self.assertEqual(summary.provider_recent, [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workspace_viewmodel.py -v`
Expected: FAIL — `WorkspaceSummary` has no `provider_recent` attribute

- [ ] **Step 3: Add `provider_recent` field to WorkspaceSummary**

In `src/app/viewmodels/workspace.py`, add to the `WorkspaceSummary` dataclass (after line 27, the `continuity_sentence` field):

```python
provider_recent: list[dict[str, object]]
```

- [ ] **Step 4: Build `provider_recent` in `build_workspace_summary`**

In `build_workspace_summary`, after the `providers` list is built (after line 58), add:

```python
# Per-provider most recent conversation
provider_recent = []
for source, conversation_count in provider_rows:
    most_recent = (
        ImportedConversation.query
        .filter_by(source=source)
        .order_by(ImportedConversation.id.desc())
        .first()
    )
    provider_recent.append({
        "provider": source,
        "count": conversation_count,
        "recent_title": most_recent.title if most_recent else "",
        "recent_id": most_recent.id if most_recent else None,
    })
```

Then add `provider_recent=provider_recent,` to the `WorkspaceSummary(...)` constructor call (after `providers=providers,`).

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_workspace_viewmodel.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All PASS (additive field, existing tests untouched)

- [ ] **Step 7: Commit**

```bash
git add src/app/viewmodels/workspace.py tests/test_workspace_viewmodel.py
git commit -m "feat: add provider_recent to WorkspaceSummary (additive)"
```

---

### Task 5: Rewrite workspace landing page template

**Files:**
- Modify: `src/app/templates/index.html` (complete rewrite)
- Modify: `tests/test_workspace_home.py`

- [ ] **Step 1: Write new tests for the redesigned landing page**

Replace `tests/test_workspace_home.py` content. The new tests must check:

```python
"""Tests for the redesigned workspace landing page."""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class WorkspaceHomeTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "workspace-home")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _get_workspace_html(self) -> str:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def _seed_conv(self, source: str, title: str = "Test") -> ImportedConversation:
        conv = ImportedConversation(
            source=source,
            source_conversation_id=f"{source}-{title}-{id(object())}",
            title=title,
        )
        db.session.add(conv)
        db.session.flush()
        return conv

    # ── First-run state ──

    def test_first_run_shows_trust_block_and_cta(self):
        html = self._get_workspace_html()
        self.assertIn("SoulPrint", html)
        self.assertIn("Bring your first conversation home", html)
        self.assertIn("Nothing is sent anywhere", html)
        self.assertIn("Everything stays on your machine", html)

    def test_first_run_does_not_show_provider_stack(self):
        html = self._get_workspace_html()
        self.assertNotIn("YOUR ARCHIVE", html)
        self.assertNotIn("CONTINUITY", html)

    # ── Post-import state ──

    def test_post_import_shows_trust_oneliner(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test conv")
            db.session.commit()
        html = self._get_workspace_html()
        # Trust one-liner is present (case-insensitive content check)
        self.assertIn("nothing leaves your machine", html.lower())

    def test_post_import_shows_continuity_card_with_simplified_sentence(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Conv1")
            self._seed_conv("claude", "Conv2")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("2 conversations", html)
        self.assertIn("2 providers", html)
        self.assertIn("Import more conversations", html)
        # Must NOT contain the old verbose sentence with native/trace counts
        self.assertNotIn("native memory entries", html)

    def test_post_import_shows_provider_stack_with_lane_colors(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "GPT conversation")
            self._seed_conv("claude", "Claude conversation")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("chatgpt", html.lower())
        self.assertIn("claude", html.lower())
        self.assertIn("GPT conversation", html)
        self.assertIn("Claude conversation", html)

    def test_post_import_shows_browse_everything_link(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("Browse everything together", html)
        self.assertIn("/federated", html)

    def test_post_import_does_not_show_stats_grid(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        # Old elements removed
        self.assertNotIn("workspace-counts", html)
        self.assertNotIn("Next Actions", html)
        self.assertNotIn("Resume Recent Work", html)

    def test_post_import_uses_container_card_class(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Test")
            db.session.commit()
        html = self._get_workspace_html()
        self.assertIn("container-card", html)

    def test_post_import_provider_row_links_to_explorer(self):
        with self.app.app_context():
            conv = self._seed_conv("chatgpt", "Linked conversation")
            db.session.commit()
            conv_id = conv.id
        html = self._get_workspace_html()
        self.assertIn(f'/imported/{conv_id}/explorer', html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_workspace_home.py -v`
Expected: Several FAIL — old template doesn't match new assertions

- [ ] **Step 3: Rewrite index.html**

Replace `src/app/templates/index.html` with:

```html
{% extends "base.html" %}

{% block title %}SoulPrint Workspace{% endblock %}

{% block content %}
  {% if not workspace.has_any_data %}
    {# ── First-run: trust hero, centered ── #}
    <section class="workspace-firstrun">
      <h1 class="workspace-firstrun__wordmark">SoulPrint</h1>
      <p class="workspace-firstrun__tagline">
        A virtual USB stick for your AI life.
      </p>
      <div class="container-card workspace-firstrun__trust">
        <p>
          Your files are processed locally.
          Nothing is sent anywhere. No account.
          No cloud. Everything stays on your machine.
        </p>
        <a class="workspace-firstrun__cta" href="{{ url_for('import_conversations') }}">
          Bring your first conversation home
        </a>
      </div>
    </section>

  {% else %}
    {# ── Post-import: trust line + continuity card + archive card ── #}
    <p class="workspace-trust-line">Local-only · nothing leaves your machine</p>

    <div class="workspace-post">
      <div class="container-card">
        <p class="container-card__eyebrow">Continuity</p>
        <p class="workspace-continuity-sentence">
          You have {{ workspace.imported_conversation_count }} conversations
          across {{ workspace.provider_recent|length }} providers.
        </p>
        <a class="workspace-import-cta" href="{{ url_for('import_conversations') }}">
          Import more conversations
        </a>
      </div>

      {% if workspace.provider_recent %}
        <div class="container-card">
          <p class="container-card__eyebrow">Your Archive</p>
          {% for entry in workspace.provider_recent %}
            <div class="record-card workspace-provider-row workspace-provider-row--{{ entry.provider }}">
              <div class="workspace-provider-row__header">
                <span class="workspace-provider-row__name">{{ entry.provider }}</span>
                <span class="workspace-provider-row__count">{{ entry.count }} conversations</span>
              </div>
              {% if entry.recent_title and entry.recent_id %}
                <a class="ghost-link workspace-provider-row__recent"
                   href="{{ url_for('imported_explorer', conversation_id=entry.recent_id) }}">
                  last: "{{ entry.recent_title }}"
                </a>
              {% endif %}
            </div>
          {% endfor %}
          <div class="container-card__footer">
            <a class="ghost-link" href="{{ url_for('federated_browser') }}">Browse everything together</a>
          </div>
        </div>
      {% endif %}
    </div>
  {% endif %}
{% endblock %}
```

- [ ] **Step 4: Add workspace-specific CSS**

Add to `app.css`, replacing the existing workspace-welcome and workspace-grid sections (lines ~231-263, starting from the `/* Welcome */` comment). Remove ALL old rules for: `.workspace-welcome`, `.workspace-welcome--compact`, `.workspace-welcome__tagline`, `.workspace-welcome__cta`, `.workspace-welcome__trust`, `.workspace-grid`, `.workspace-block`, `.workspace-block--wide`, `.workspace-block h2`, `.workspace-block h3`, `.workspace-summary`, `.workspace-counts`, `.workspace-counts div`, `.workspace-counts span`, `.workspace-counts strong`, `.provider-badges`, `.workspace-block__head`, `.resume-grid`, `.resume-grid section`, `.resume-list`, `.resume-list li`, `.resume-list li a`, `.resume-list li span`.

Also clean up dead CSS references in other sections:
- In the `@media(max-width:760px)` block (~line 333-334): remove `.workspace-counts{...}` and `.resume-grid{...}` rules
- In the transition rule (~line 321): remove `.workspace-block h2` from the selector list

**Note:** `_ui.html` does NOT need modification despite the spec listing it — the empty-state styling change is CSS-only; the macro HTML structure stays the same.

Replace with:

```css
/* Workspace — first-run */
.workspace-firstrun{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:calc(100vh - 200px);text-align:center;max-width:420px;margin:0 auto}
.workspace-firstrun__wordmark{font-family:var(--font-display);font-size:clamp(2rem,4vw,2.8rem);font-weight:400;color:var(--t1);margin-bottom:12px;letter-spacing:-0.5px}
.workspace-firstrun__tagline{color:var(--t2);font-family:var(--font-body);font-size:16px;line-height:1.7;margin-bottom:24px}
.workspace-firstrun__trust{text-align:center}
.workspace-firstrun__trust p{color:var(--t2);font-size:14px;line-height:1.6;margin-bottom:20px}
.workspace-firstrun__cta{display:block;width:100%;padding:12px 24px;background:var(--cta-bg);border:none;border-radius:var(--radius-sm);color:var(--cta-text);font-family:var(--font-body);font-size:14px;font-weight:600;text-align:center;text-decoration:none;transition:background .2s ease}
.workspace-firstrun__cta:hover{background:var(--cta-hover-bg);color:var(--cta-hover-text)}

/* Workspace — post-import */
.workspace-trust-line{color:var(--t3);font-family:var(--font-mono);font-size:11px;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:16px}
.workspace-post{display:flex;flex-direction:column;gap:16px;max-width:560px;margin:0 auto}
.workspace-continuity-sentence{color:var(--t1);font-family:var(--font-body);font-size:16px;font-weight:500;line-height:1.5;margin-bottom:16px}
.workspace-import-cta{display:block;width:100%;padding:12px 24px;background:var(--cta-bg);border:none;border-radius:var(--radius-sm);color:var(--cta-text);font-family:var(--font-body);font-size:14px;font-weight:600;text-align:center;text-decoration:none;transition:background .2s ease}
.workspace-import-cta:hover{background:var(--cta-hover-bg);color:var(--cta-hover-text)}

/* Provider rows */
.workspace-provider-row{display:flex;flex-direction:column;gap:4px}
.workspace-provider-row--chatgpt{border-left:2px solid var(--lane-chatgpt);padding-left:12px}
.workspace-provider-row--claude{border-left:2px solid var(--lane-claude);padding-left:12px}
.workspace-provider-row--gemini{border-left:2px solid var(--lane-gemini);padding-left:12px}
.workspace-provider-row__header{display:flex;align-items:baseline;gap:12px}
.workspace-provider-row__name{color:var(--t1);font-family:var(--font-body);font-size:15px;font-weight:500;text-transform:capitalize}
.workspace-provider-row__count{color:var(--t3);font-family:var(--font-mono);font-size:12px}
.workspace-provider-row__recent{color:var(--t2);font-size:14px}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_workspace_home.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add src/app/templates/index.html src/app/static/app.css tests/test_workspace_home.py
git commit -m "feat: redesign workspace landing page — trust hero, provider stack, container-card"
```

---

### Task 6: Wrap content list pages in `.container-card`

**Files:**
- Modify: `src/app/templates/imported_list.html`
- Modify: `src/app/templates/answer_trace_list.html`
- Modify: `src/app/templates/federated.html`
- Modify: `src/app/templates/view.html`

- [ ] **Step 1: Read each template to find the record-card list**

Read all four templates. Find the section where `.record-card` elements are listed (usually inside a `{% for %}` loop). Wrap that loop in a `<div class="container-card">` without changing any inner HTML.

Pattern for each file:

**Before:**
```html
{% for item in items %}
  <div class="record-card ...">...</div>
{% endfor %}
```

**After:**
```html
<div class="container-card">
  {% for item in items %}
    <div class="record-card ...">...</div>
  {% endfor %}
</div>
```

Apply this to:
- `imported_list.html` — the `{% for conv in conversations %}` loop
- `answer_trace_list.html` — the `{% for trace in traces %}` loop
- `federated.html` — the `{% for result in results %}` loop
- `view.html` — the `{% for entry in entries %}` loop

If the loop has an `{% else %}` clause (empty state), keep the empty state inside the same wrapper, or move it outside — use judgment per template.

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Visual check at 3 breakpoints**

Open the app (`python -m src.run`) and check each modified page at 1200px, 768px, and 480px. Verify:
- Record lists have a rounded container background
- Records inside are flat with bottom-border dividers
- Hover shows purple tint on records
- Mobile: container goes flush to edges (no border-radius)

- [ ] **Step 4: Commit**

```bash
git add src/app/templates/imported_list.html src/app/templates/answer_trace_list.html src/app/templates/federated.html src/app/templates/view.html
git commit -m "feat: wrap content list pages in container-card"
```

---

### Task 7: Final verification and cleanup

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: Visual verification checklist**

Open `python -m src.run` and check:

| Page | Check |
|------|-------|
| `/` (empty DB) | Centered wordmark + tagline + trust card with CTA |
| `/` (with data) | Trust one-liner + continuity card + provider stack |
| `/imported` | Record list wrapped in container-card |
| `/answer-traces` | Record list wrapped in container-card |
| `/federated` | Record list wrapped in container-card |
| `/chats` | Record list wrapped in container-card |
| Sidebar (any page) | Active link has purple background tint |
| Sidebar hover | Inactive links show subtle purple on hover |
| `/passport` | Existing `.surface-card` usages unchanged |
| `/ask` | Existing `.surface-card` usages unchanged |

Check each at 1200px, 768px, 480px.

- [ ] **Step 3: Verify accent split**

- Green appears on: CTA buttons, active nav left border, badge accents, ghost-link hover
- Purple appears on: sidebar active background, sidebar hover, record-card hover inside container-card
- No other colors used as accents

- [ ] **Step 4: Final commit if any touch-ups needed**

```bash
git add -A
git commit -m "fix: workspace redesign touch-ups"
```
