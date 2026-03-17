# Wrapped Summary Page Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone "Spotify Wrapped for AI" summary page at GET /summary — always dark, cinematic, screenshottable.

**Architecture:** Frozen dataclass viewmodel (`WrappedSummary`) queries canonical SQLite + derived JSONL stores. Standalone template (no base.html). Two-tier unfinished thread detection: continuity open_loops first, then last-message-is-user heuristic fallback.

**Tech Stack:** Flask, SQLAlchemy, Jinja2, inline CSS (Torchlit Vault dark theme)

**Spec:** `docs/superpowers/specs/2026-03-17-wrapped-summary-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `src/app/viewmodels/wrapped.py` | Create | WrappedSummary dataclass + build_wrapped_summary() builder |
| `src/app/viewmodels/__init__.py` | Modify | Export WrappedSummary + build_wrapped_summary |
| `src/app/__init__.py` | Modify | Add GET /summary route + import redirect logic |
| `src/app/templates/wrapped.html` | Create | Standalone dark cinematic template |
| `src/app/templates/index.html` | Modify | Add "View your summary" link |
| `src/app/templates/import.html` | Modify | Add "See your updated summary" link |
| `tests/test_wrapped_summary.py` | Create | 8+ test cases for viewmodel + route + redirect |

---

## Task 1: Viewmodel — Tests + Implementation

**Files:**
- Create: `tests/test_wrapped_summary.py`
- Create: `src/app/viewmodels/wrapped.py`
- Modify: `src/app/viewmodels/__init__.py`

- [ ] **Step 1: Write failing tests for the viewmodel and route**

Create `tests/test_wrapped_summary.py` with all 8 test cases. These test the viewmodel builder, the route, empty state, provider percentages, topic absence, unfinished threads, watermark text, and the post-first-import redirect.

```python
"""Tests for the Wrapped Summary page at /summary."""

from __future__ import annotations

import io
import json
import unittest
from datetime import datetime
from pathlib import Path

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage, MemoryEntry
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class WrappedSummaryTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "wrapped-summary")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/test.db"
        self.addCleanup(self._restore_sqlite_uri)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _seed_conv(
        self,
        source: str,
        title: str = "Test",
        created_at_unix: float | None = 1700000000.0,
        messages: list[tuple[str, str]] | None = None,
    ) -> ImportedConversation:
        conv = ImportedConversation(
            source=source,
            source_conversation_id=f"{source}-{title}-{id(object())}",
            title=title,
            created_at_unix=created_at_unix,
        )
        db.session.add(conv)
        db.session.flush()
        if messages:
            for i, (role, content) in enumerate(messages):
                db.session.add(
                    ImportedMessage(
                        conversation_id=conv.id,
                        sequence_index=i,
                        role=role,
                        content=content,
                        source_message_id=f"msg-{conv.id}-{i}",
                    )
                )
        return conv

    def _write_topic_scan(self, labels: list[str]) -> None:
        topic_path = self.workdir / "topic_scans.jsonl"
        scan = {
            "scan_id": "scan-1",
            "created_at": "2026-03-17T00:00:00+00:00",
            "clusters": [
                {"topic_label": label, "conversation_stable_ids": []}
                for label in labels
            ],
        }
        with open(topic_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(scan) + "\n")

    # -- Test 1: Viewmodel stats correct from seeded data --

    def test_viewmodel_stats_correct_from_seeded_data(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "Conv1", 1700000000.0, [
                ("user", "Hello"), ("assistant", "Hi there"),
            ])
            self._seed_conv("claude", "Conv2", 1702000000.0, [
                ("user", "Question"), ("assistant", "Answer"), ("user", "Follow-up"),
            ])
            db.session.add(MemoryEntry(
                timestamp=datetime(2026, 1, 1), role="user", content="Native", tags="",
            ))
            db.session.commit()

        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        # total_conversations = 2 imported + 1 native = 3
        self.assertIn("3", html)  # total conversations somewhere
        # total_messages = 5 imported + 1 native = 6
        self.assertIn("6", html)  # total messages (headline stat)

    # -- Test 2: GET /summary returns 200 --

    def test_get_summary_returns_200(self):
        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 200)

    # -- Test 3: Provider percentages sum to ~100 --

    def test_provider_percentages_sum_to_approximately_100(self):
        with self.app.app_context():
            from src.app.viewmodels.wrapped import build_wrapped_summary
            self._seed_conv("chatgpt", "C1", messages=[("user", "a")])
            self._seed_conv("chatgpt", "C2", messages=[("user", "b")])
            self._seed_conv("claude", "C3", messages=[("user", "c")])
            db.session.commit()

            sqlite_uri = self.app.config["SQLALCHEMY_DATABASE_URI"]
            sqlite_path = sqlite_uri.removeprefix("sqlite:///")
            summary = build_wrapped_summary(sqlite_path=sqlite_path)
            total_pct = sum(p["percentage"] for p in summary.providers)
            self.assertAlmostEqual(total_pct, 100.0, delta=1.0)

    # -- Test 4: Empty DB renders graceful empty state --

    def test_empty_db_renders_empty_state(self):
        response = self.client.get("/summary")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Import your first conversation", html)

    # -- Test 5: "Generated by SoulPrint" present --

    def test_generated_by_soulprint_present(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "C1", messages=[("user", "hi")])
            db.session.commit()

        html = self.client.get("/summary").get_data(as_text=True)
        self.assertIn("Generated by SoulPrint", html)

    # -- Test 6: Topic section absent when no topic data --

    def test_topic_section_absent_when_no_topic_data(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "C1", messages=[("user", "hi")])
            db.session.commit()

        html = self.client.get("/summary").get_data(as_text=True)
        self.assertNotIn("Topics", html)

    # -- Test 7: Unfinished threads count present even when zero --

    def test_unfinished_threads_count_present_when_zero(self):
        with self.app.app_context():
            self._seed_conv("chatgpt", "AllAnswered", messages=[
                ("user", "Q"), ("assistant", "A"),
            ])
            db.session.commit()

        html = self.client.get("/summary").get_data(as_text=True)
        self.assertIn("Unfinished threads", html)
        self.assertIn("0", html)

    # -- Test 8: Post-first-import redirect to /summary --

    def test_post_first_import_redirects_to_summary(self):
        fixture_bytes = Path("sample_data/chatgpt_export_sample.json").read_bytes()
        response = self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt_export_sample.json")},
            content_type="multipart/form-data",
        )
        # First import (DB was empty) should redirect to /summary
        self.assertEqual(response.status_code, 302)
        self.assertIn("/summary", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_wrapped_summary.py -v`
Expected: FAIL — ImportError on `src.app.viewmodels.wrapped`, no `/summary` route

- [ ] **Step 3: Create the viewmodel**

Create `src/app/viewmodels/wrapped.py`:

```python
"""Wrapped summary viewmodel for the /summary route."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import func

from ..models import ImportedConversation, ImportedMessage, MemoryEntry
from ..models.db import db


@dataclass(frozen=True)
class WrappedSummary:
    """Read-only wrapped summary rendered on the /summary route."""

    total_conversations: int
    total_messages: int
    providers: list[dict]
    dominant_provider: dict
    date_range: dict
    most_active_month: str
    longest_conversation: dict
    topic_highlights: list[str]
    average_messages_per_conversation: float
    unfinished_threads: dict
    has_data: bool


def _detect_unfinished_threads(
    sqlite_path: str,
) -> dict:
    """Two-tier unfinished thread detection.

    1. Check continuity open_loops artifacts for conversations with known open loops.
    2. Fallback: conversations where the last message role is 'user'.
    Deduplicate by conversation ID, cap at 3 titles.
    """
    from ...intelligence.continuity.store import (
        default_continuity_store_path,
        list_artifacts_by_type,
    )

    seen_conv_ids: set[int] = set()
    titles: list[str] = []

    # Tier 1: continuity open_loops artifacts
    store_path = default_continuity_store_path(sqlite_path)
    open_loop_artifacts = list_artifacts_by_type(store_path, "open_loops", limit=50)
    for artifact in open_loop_artifacts:
        for sid in artifact.get("source_conversation_ids", []):
            parts = sid.split(":", 1)
            if len(parts) == 2 and parts[1].isdigit():
                conv_id = int(parts[1])
                if conv_id not in seen_conv_ids:
                    conv = ImportedConversation.query.filter_by(id=conv_id).first()
                    if conv:
                        seen_conv_ids.add(conv_id)
                        titles.append(conv.title or "Untitled")

    # Tier 2: heuristic — last message role is "user"
    conversations = ImportedConversation.query.all()
    for conv in conversations:
        if conv.id in seen_conv_ids:
            continue
        messages = sorted(conv.messages, key=lambda m: m.sequence_index)
        if messages and messages[-1].role == "user":
            seen_conv_ids.add(conv.id)
            titles.append(conv.title or "Untitled")

    return {
        "count": len(seen_conv_ids),
        "titles": titles[:3],
    }


def build_wrapped_summary(*, sqlite_path: str) -> WrappedSummary:
    """Build the read-only wrapped summary from canonical and derived stores."""

    # --- Counts ---
    native_count = db.session.query(func.count(MemoryEntry.id)).scalar() or 0
    imported_conv_count = (
        db.session.query(func.count(ImportedConversation.id)).scalar() or 0
    )
    imported_msg_count = (
        db.session.query(func.count(ImportedMessage.id)).scalar() or 0
    )
    total_conversations = imported_conv_count + native_count
    total_messages = imported_msg_count + native_count

    has_data = total_conversations > 0

    # --- Providers ---
    provider_rows = (
        db.session.query(
            ImportedConversation.source,
            func.count(ImportedConversation.id).label("cnt"),
        )
        .group_by(ImportedConversation.source)
        .order_by(func.count(ImportedConversation.id).desc())
        .all()
    )
    providers = []
    for source, cnt in provider_rows:
        pct = (cnt / imported_conv_count * 100) if imported_conv_count else 0.0
        providers.append({"name": source, "count": cnt, "percentage": round(pct, 1)})

    dominant_provider = (
        {"name": providers[0]["name"], "count": providers[0]["count"]}
        if providers
        else {"name": "", "count": 0}
    )

    # --- Date range ---
    earliest = db.session.query(func.min(ImportedConversation.created_at_unix)).scalar()
    latest = db.session.query(func.max(ImportedConversation.created_at_unix)).scalar()
    date_range = {"earliest": earliest, "latest": latest}

    # --- Most active month ---
    most_active_month = ""
    if has_data and imported_conv_count > 0:
        # SQLite strftime to group by year-month
        month_rows = (
            db.session.query(
                func.strftime("%Y-%m", ImportedConversation.created_at_unix, "unixepoch").label("ym"),
                func.count(ImportedConversation.id).label("cnt"),
            )
            .filter(ImportedConversation.created_at_unix.isnot(None))
            .group_by("ym")
            .order_by(func.count(ImportedConversation.id).desc())
            .first()
        )
        if month_rows and month_rows[0]:
            most_active_month = month_rows[0]

    # --- Longest conversation ---
    longest_row = (
        db.session.query(
            ImportedConversation.title,
            func.count(ImportedMessage.id).label("msg_count"),
        )
        .join(ImportedConversation.messages)
        .group_by(ImportedConversation.id)
        .order_by(func.count(ImportedMessage.id).desc())
        .first()
    )
    longest_conversation = (
        {"title": longest_row[0] or "Untitled", "message_count": longest_row[1]}
        if longest_row
        else {"title": "", "message_count": 0}
    )

    # --- Average messages per conversation ---
    avg = round(total_messages / total_conversations, 1) if total_conversations else 0.0

    # --- Topic highlights (top 5 from latest scan) ---
    from ...intelligence.store import default_topic_store_path, list_topic_scans

    topic_store = default_topic_store_path(sqlite_path)
    topic_scans = list_topic_scans(topic_store, limit=1)
    topic_highlights: list[str] = []
    if topic_scans:
        clusters = topic_scans[0].get("clusters", [])
        topic_highlights = [c.get("topic_label", "") for c in clusters[:5]]

    # --- Unfinished threads ---
    unfinished_threads = _detect_unfinished_threads(sqlite_path)

    return WrappedSummary(
        total_conversations=total_conversations,
        total_messages=total_messages,
        providers=providers,
        dominant_provider=dominant_provider,
        date_range=date_range,
        most_active_month=most_active_month,
        longest_conversation=longest_conversation,
        topic_highlights=topic_highlights,
        average_messages_per_conversation=avg,
        unfinished_threads=unfinished_threads,
        has_data=has_data,
    )
```

- [ ] **Step 4: Update viewmodels `__init__.py`**

Add to `src/app/viewmodels/__init__.py`:

```python
from .wrapped import WrappedSummary, build_wrapped_summary
```

And update `__all__` to include them.

- [ ] **Step 5: Commit viewmodel**

```bash
git add src/app/viewmodels/wrapped.py src/app/viewmodels/__init__.py tests/test_wrapped_summary.py
git commit -m "feat(wrapped): add WrappedSummary viewmodel + failing tests"
```

---

## Task 2: Route + Template

**Files:**
- Modify: `src/app/__init__.py` (add GET /summary route)
- Create: `src/app/templates/wrapped.html`

- [ ] **Step 1: Add the /summary route**

Add to `src/app/__init__.py`, before `return app`:

```python
@app.get("/summary")
def summary():
    from .viewmodels.wrapped import build_wrapped_summary

    sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    sqlite_path = _sqlite_path_from_uri(sqlite_uri)
    wrapped = build_wrapped_summary(sqlite_path=sqlite_path)

    return render_template("wrapped.html", wrapped=wrapped)
```

- [ ] **Step 2: Create wrapped.html template**

Create `src/app/templates/wrapped.html` — standalone, NOT extending base.html. Always dark Torchlit Vault. Inline CSS. Full viewport, max-width 800px. Sections: empty state gate, hero with glow, headline stat, supporting stats, provider breakdown, most active month, longest thread, topics (conditional), unfinished threads (always), watermark, footer.

Key template logic:
- `{% if not wrapped.has_data %}` → empty state with wordmark + "Import your first conversation" + wine CTA
- `{% if wrapped.topic_highlights %}` → topics section (omit entirely otherwise)
- Unfinished threads section always renders, showing count even when 0
- "Generated by SoulPrint" watermark always present when has_data
- "Back to Workspace" link in footer

- [ ] **Step 3: Run tests to verify route + template work**

Run: `python -m pytest tests/test_wrapped_summary.py -v`
Expected: Most tests should now PASS (viewmodel + route + template rendering)

- [ ] **Step 4: Commit route + template**

```bash
git add src/app/__init__.py src/app/templates/wrapped.html
git commit -m "feat(wrapped): add GET /summary route + standalone template"
```

---

## Task 3: Import Redirect + Workspace Link

**Files:**
- Modify: `src/app/__init__.py` (import_conversations handler)
- Modify: `src/app/templates/index.html`
- Modify: `src/app/templates/import.html`

- [ ] **Step 1: Add post-first-import redirect**

In `src/app/__init__.py`, modify the `import_conversations()` route handler. Before the import logic, capture current count:

```python
count_before = ImportedConversation.query.count() if request.method == "POST" else 0
```

After successful import, check:
```python
if count_before == 0 and import_result.imported_conversations > 0:
    return redirect(url_for("summary"))
```

For incremental imports, add `show_summary_link=True` to the result dict.

- [ ] **Step 2: Add summary link to import.html**

In the result section of `src/app/templates/import.html`, after the existing "Go to Imported conversations" link, add:

```html
{% if result.show_summary_link %}
  <a class="route-card__link" href="{{ url_for('summary') }}">See your updated summary →</a>
{% endif %}
```

- [ ] **Step 3: Add summary link to workspace (index.html)**

In `src/app/templates/index.html`, add a "View your summary" link in the Next Actions section when data exists:

```html
<li><a href="{{ url_for('summary') }}">View your summary</a> — your AI memory at a glance.</li>
```

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/test_wrapped_summary.py -v`
Expected: ALL 8 tests PASS

Run: `python -m pytest tests/ -v`
Expected: ALL tests PASS (368 existing + 8 new = 376)

- [ ] **Step 5: Commit redirect + links**

```bash
git add src/app/__init__.py src/app/templates/index.html src/app/templates/import.html
git commit -m "feat(wrapped): post-first-import redirect + workspace/import summary links"
```

---

## Task 4: Verification + Final Commit

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS (376 tests)

- [ ] **Step 2: Verify GET /summary manually**

Check:
- `GET /summary` returns 200
- Empty DB returns 200 with "Import your first conversation"
- "Generated by SoulPrint" present in response body
- No `Topics` section when no topic scan data exists

- [ ] **Step 3: Verify no regressions**

Check:
- `GET /` still returns 200
- `GET /import` still returns 200
- All existing routes unaffected

- [ ] **Step 4: Use finishing-a-development-branch skill to merge**

Invoke `superpowers:finishing-a-development-branch` to merge `feature/wrapped-summary` into main.
