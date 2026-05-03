# Tagging — SoulPrint Spec v2

**Status:** Authoritative for Tags MVP (A1 scope). Committed 2026-04-22.
**Supersedes:** v1 (2026-04-22 earlier same day, now archived). v1 over-specified — it locked a modal curation flow, a triage queue, and cross-surface filter UI based on design decisions that hadn't been pressure-tested. This v2 collapses to the minimum that ships the core vision.
**Scope:** Comma-string schema on `ImportedConversation.tags` + auto-tag on import + visible, inline-editable chips on `/imported` list rows.
**Explicitly out of scope:** star-refinement modal (belongs to a separate future spec for Phase B, star-as-triage), cross-surface chip rendering on `/federated` or `/chats`, URL tag filter UI, bulk edit, triage queue, normalized tag table.

---

## 1. What tagging is

Every imported conversation gets a tag derived from its title at import time. That tag sits on the row as a chip. The user can add, remove, or rename tags per-row with the same kind of lightweight form POST that CP1 starring uses.

This is one primitive. One column, one auto-tag step, one row surface, inline edit via plain form submits.

The broader two-tier vision (raw tags plus a curation layer via starring) isn't abandoned. It's sequenced: this spec ships the raw tier. The curation tier is Phase B of the plan and will have its own spec if and when it becomes active work.

---

## 2. Current state audit (against main at PR #144)

> **Note (2026-04-27):** This audit and the "Gap this spec fills" section
> describe the pre-implementation state. The MVP shipped 2026-04-22 per
> the file header. The section is preserved as design context.

Existing tagging code, unchanged by this spec:

- `MemoryEntry.tags` is a comma-string column. Used by `/chats?tag=X` substring filter.
- `/api/clip` at `src/app/__init__.py:526` auto-tags clipped notes with `clipped`.
- `/save` creates plain notes with whatever the user types in the tag field.

Gap this spec fills:

- `ImportedConversation` has no `tags` column.
- `/imported` rows surface no organizational primitive beyond starring (CP1) and archive/delete actions.

What this spec does NOT change:

- `MemoryEntry.tags` schema, auto-tag behavior, or filter semantics.
- `/api/clip` or `/save` auto-tag behavior.
- Any surface other than `/imported` list rows.

---

## 3. Locked decisions

| ID | Decision | Section |
|----|----------|---------|
| A  | Schema: comma-string on `ImportedConversation.tags`, matching `MemoryEntry.tags` pattern. | 4 |
| B  | Auto-tag on import only. First meaningful word from title with stopword list. | 5 |
| C  | Inline edit on `/imported` rows via plain form POSTs. No JS required. | 6 |
| D  | Normalization: lowercase, strip, collapse internal whitespace, 64-char max, reject empty, dedupe. | 7 |

---

## 4. Schema — Decision A

### Chosen shape

```python
class ImportedConversation(db.Model):
    # ... existing columns ...
    tags = db.Column(db.String, nullable=False, server_default="", default="")
```

Comma-separated string. Normalized on every write path via the helper in Section 7. Matches the existing `MemoryEntry.tags` convention so the codebase has one tagging pattern, not two.

### Migration

Idempotent ALTER guard at startup, same pattern as the `is_starred` column from CP1:

```python
cols = _pragma_columns(conn, "imported_conversation")
if "tags" not in cols:
    conn.execute(text("ALTER TABLE imported_conversation ADD COLUMN tags VARCHAR NOT NULL DEFAULT ''"))
```

No Alembic. No backfill of existing rows. Existing conversations get empty tag strings; auto-tagging applies only to future imports. A user who wants tags on already-imported conversations edits them inline. No re-import pass required.

### Rejected alternative

**Normalized `ConversationTag` table** (FK + unique constraint) from CP3 in `soulprint-companion-layer-plan.md`. Rejected because the rename-across-N-rows benefit is negligible at personal-archive scale and the migration cost on existing `MemoryEntry.tags` would double implementation work. Decision is re-examinable in a future v3 if tag cardinality or rename needs justify the cost.

---

## 5. Auto-tag on import — Decision B

### When

At the moment an `ImportedConversation` row is created during any provider's import flow. Runs once per conversation. Does not apply retroactively to already-imported rows.

### Extraction rule

Given the conversation title:

1. Split on whitespace.
2. Drop leading tokens matching the stopword list (Section 5.1).
3. Take the first remaining token.
4. Normalize per Section 7.
5. If the result is empty (empty title, all-stopword title, or normalizes to empty), leave `tags` as `""`.

### Examples

| Title | Auto-tag |
|-------|----------|
| `"How do I bake carbonara?"` | `bake` |
| `"My novel draft revisions"` | `novel` |
| `"Soulprint issue"` | `soulprint` |
| `"The complete guide to X"` | `complete` |
| `""` | (empty) |
| `"Why"` | (empty, single stopword) |

### 5.1 Stopword list

```
the, a, an, my, your, how, do, can, what, why, when, where, is, are, i, you, we, us, to, for, of, and, or, but, in, on, at, with, this, that, these, those, it
```

English only for v1. Stored as a frozenset in the tags utility module. Non-English extension is a v3 concern, re-examinable if usage signals surface it.

### Not changed

`/api/clip` continues to auto-tag clipped notes as `clipped`. `/save` continues to produce whatever the user types. Symmetric auto-tagging of `/save` notes was considered and rejected because plain notes have no source from which to derive a meaningful tag, and a uniform auto-tag ("authored" or similar) would add noise without signal.

---

## 6. Inline edit on `/imported` rows — Decision C

Every row on `/imported` renders its tags as chips. Each chip displays the tag text and a remove affordance. A compact add-tag input sits at the end of the chip row.

### Add and remove routes

Two new POST routes, mirroring CP1 starring's plain-form pattern:

```
POST /imported/<conv_id>/tags/add
POST /imported/<conv_id>/tags/remove/<tag>
```

Both accept a `next` form field for post-redirect destination (same pattern used by star/unstar). Both redirect to the sanitized `next` or fall back to `/imported`.

**`/tags/add`** reads a single `tag` field from the form body. Normalizes per Section 7. If already present in the row's tags, it's a no-op (not an error). If empty after normalization, it's a no-op.

**`/tags/remove/<tag>`** removes the named tag from the row's comma-string. Normalizes the incoming URL-path tag before matching so encoded variations collide. If not present, no-op.

### Template shape

The chip row in `imported_list.html`:

```jinja
<span class="tag-chip-row">
  {% for tag in (conv.tags or '').split(',') if tag.strip() %}
    <form method="post" action="/imported/{{ conv.id }}/tags/remove/{{ tag.strip() | urlencode }}" class="tag-chip">
      <input type="hidden" name="next" value="{{ current_path_with_params }}">
      <span class="tag-chip__label">{{ tag.strip() }}</span>
      <button type="submit" class="tag-chip__remove" aria-label="Remove tag {{ tag.strip() }}">×</button>
    </form>
  {% endfor %}
  <form method="post" action="/imported/{{ conv.id }}/tags/add" class="tag-chip-add">
    <input type="hidden" name="next" value="{{ current_path_with_params }}">
    <input type="text" name="tag" class="tag-chip-add__input" placeholder="+ tag" maxlength="64">
  </form>
</span>
```

No JavaScript. The add-input submits on Enter (browser default for a single input in a form). The visual polish of this chip row is Phase C territory (the `.row-action-btn` promotion) — inline styles are acceptable for the tags MVP, class promotion lands when Phase C runs.

### Redirect-after-action safety

Both routes use the same inlined CodeQL-recognized sanitizer pattern that CP1 starring closed. Not a helper; the sanitizer shape is visible at each redirect sink.

```python
nxt = request.form.get("next", "")
nxt = nxt.replace("\\", "")
if nxt and not urlparse(nxt).netloc and not urlparse(nxt).scheme:
    return redirect(nxt)
return redirect(url_for("imported_conversations"))
```

---

## 7. Normalization — Decision D

A single helper handles every write path: import auto-tag, add route, remove route (for URL-path tag matching).

```python
def normalize_tag_string(raw: str) -> str:
    """Normalize one tag or a comma-separated list. Returns the canonical string."""
    parts = [p.strip().lower() for p in raw.split(",")]
    parts = [" ".join(p.split()) for p in parts]  # collapse internal whitespace
    parts = [p[:64] for p in parts]
    parts = [p for p in parts if p]
    seen = set()
    deduped = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return ", ".join(deduped)
```

Lives at `src/app/tags.py` (new module). Also houses the `STOPWORDS` frozenset from Section 5.1 and the `auto_tag_from_title` helper referenced in Section 8.

### Examples

| Input | Output |
|-------|--------|
| `"Novel, NOVEL, novel"` | `"novel"` |
| `"  My  Draft , notes"` | `"my draft, notes"` |
| `""` | `""` |
| `"a, , , b"` | `"a, b"` |
| (65-char tag) | (truncated to 64) |

---

## 8. Build sequence — single PR

Target branch: `feat/tags-mvp`. One commit, or two on the same branch if schema + migration is cleaner separated from routes + template.

1. Add `ImportedConversation.tags` column with idempotent ALTER guard (same shape as `is_starred`).
2. Create `src/app/tags.py` with `normalize_tag_string`, `STOPWORDS` frozenset, and `auto_tag_from_title(title: str) -> str`.
3. Wire `auto_tag_from_title` into each provider's importer at the point of conversation creation.
4. Register two new POST routes: `/imported/<conv_id>/tags/add` and `/imported/<conv_id>/tags/remove/<tag>`. Inline the canonical sanitizer pattern at each redirect sink.
5. Update `src/app/templates/imported_list.html` row template to render the chip row (chips + add input).
6. Tests:
   - Column exists after migration.
   - Auto-tag extracts first meaningful word per Section 5 examples.
   - Normalization behaves per Section 7 examples.
   - Add route: adds a new tag, dedupes if present, no-ops on empty.
   - Remove route: removes a present tag, no-ops on missing.
   - Redirect sanitizer: rejects protocol-absolute and backslash-prefixed `next` values.
   - Rendering: chip row appears on `/imported` with correct tags per row.

Target: +12 to +15 tests. Baseline 930 → ~942-945 passing post-PR.

---

## 9. Out of scope

Each item below was considered during v1 design and dropped for v2. Some are deferred with re-examination paths; some are frozen.

- **Star refinement modal.** Deferred. Folded into Phase B (star-as-triage) when B becomes active.
- **Cross-surface chips on `/federated`.** Deferred. Adding when federated-search + tag-filter composition becomes a real need (likely alongside ce-ideate #4).
- **URL filter `/imported?tag=X`.** Deferred. Small follow-up when user behavior surfaces the need.
- **Tag cloud sidebar.** Deferred. Phase 4 visual-language territory at earliest.
- **Bulk edit via checkbox + toolbar.** Frozen per Chris's explicit decision. Re-examinable only if a concrete user need surfaces.
- **Triage queue.** Frozen. Starring (via Phase B) is the triage moment, per-conversation, not batched.
- **Linked notes via modal.** Deferred. Folded into Phase B.
- **LLM-assisted tag suggestions.** Deferred to v3. On-demand via the Gemma4 boundary when prioritized.
- **Multi-word auto-tags from titles.** Rejected. Refinement is the user's job.
- **FTS integration for tags.** Rejected. Explicit `tag:X` prefix tokens (ce-ideate #4) are the composition path.
- **Normalized tag table migration.** Deferred to v3.

---

## 10. Non-goals (frozen)

- Semantic tag clustering. Frozen in `DECISIONS.md`.
- Shared tag taxonomy across users. SoulPrint is single-user.
- Auto-tag as the primary organizational mechanism. Auto-tag is a starting line. Starring (Phase B) is where curation happens.

---

## 11. Spec change log

**2026-04-22 (v2)** — Collapsed scope to A1 MVP. Modal curation flow, triage queue, cross-surface chips, URL filter UI, bulk edit, linked notes all moved out of scope.

**2026-04-22 (v1, earlier same day)** — Initial spec. Over-specified. Archived.
