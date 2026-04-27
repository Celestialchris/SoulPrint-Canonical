# SoulPrint Expansion Plan — Companion Layer

**Status (2026-04-27):** Partially shipped. The Phase 11 precondition is obsolete because soft launch was parked 2026-04-23. Shipped items so far:

- **CP1** Favorites and starring (PR #139).
- **CP2** Archive / hide conversations.
- **CP3** Tags on conversations (MVP shipped 2026-04-22; see `tagging-spec.md`).
- **CP6** "What's still open" view (read-only command center at `/continuity/open-loops`).
- **CP11** Import history log (`ImportRun` table + `/archive/health` page; Observable Archive v0).

Items CP4, CP5, CP7, CP8, CP9, CP10, and CP12 remain queued as design records unless current source proves otherwise.

**Parent docs:** `ROADMAP.md` (Shape 5 — Companion Layer), `docs/specs/soulprint-expansion-plan.md` (Shape 4 — Ecosystem Reach)
**Philosophy:** every item here solves a problem a companion user actually has. Not features that sound good for the audience — features that close a concrete gap between "I have my conversations on my machine" and "this archive is alive and useful." The canonical ledger is already the right shape. Nothing here reshapes it. Everything here adds surfaces above it.

---

## Why these, why now

The Ecosystem Reach plan (Shape 4) serves developers: CLI commands, Claude Code auto-discovery, drop folder, write-capable MCP. Those are the right features for r/ClaudeAI and r/LocalLLaMA.

The companion user — the person at r/MyBoyfriendIsAI who exported their ChatGPT history because they're terrified of losing it — needs something different. They don't want a CLI. They want to find the conversation from June. They want to mark the moments that matter. They want to understand what their AI actually knows about them after nine months of daily conversation. They want to hand context to a new session and pick up where they left off.

The MIT Media Lab data is concrete: 36.7% of AI relationships are with ChatGPT, the platform SoulPrint already imports. The companion audience is reachable today. What's missing isn't the importer. It's the surfaces that make the archive feel like a relationship record, not a database dump.

The cost to close this gap is low. CP1 through CP4 are all under two days each. The killer feature (CP8, Persona Extract) is three to four days. The archive has the data for all of it. Nothing requires a schema reshape. Every item composes naturally on what's already shipped.

Order below is leverage-first within each bucket.

---

# Bucket A — Companion core

## CP1 — Favorites and starring

### Problem

A companion user has 347 conversations. Three of them changed their life. There is no way to mark them. Every conversation looks the same in the list.

This is the first thing a new user will try after browsing the list for two minutes. Its absence is embarrassing at launch.

### Shape

One boolean column on `ImportedConversation`: `is_starred`, default `False`. Migration is a single `ALTER TABLE`. No new tables, no new relationships.

Two new routes: `POST /imported/<id>/star` (toggle, returns JSON `{starred: true/false}` for inline update) and a filter parameter `?starred=1` on `GET /imported`. The star button on each conversation row toggles inline without a page reload — one small JS event handler, the only JS on the page that touches state. The filter shows in the existing provider-tab row as a "Starred" tab.

On the conversation explorer page, the star toggle appears in the existing `main-header__actions` row alongside any existing action buttons.

### Schema touches

```python
is_starred = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
```

Migration: `ALTER TABLE imported_conversation ADD COLUMN is_starred BOOLEAN NOT NULL DEFAULT 0`.

### Phases

1. **Schema migration + route + list filter.** Migration, toggle route, filter parameter on `/imported`, starred tab in the provider-tab row.
2. **Explorer page integration.** Star button in the conversation explorer header.

### Risks

The inline toggle requires a small JS fetch call. SoulPrint's templates are otherwise HTML-form-only. This is the right exception because a full page reload for a star toggle is jarring. Keep the JS to five lines maximum; don't introduce a JS dependency.

### Test shape

- Toggle once: `is_starred` becomes `True`, response JSON `{starred: true}`.
- Toggle again: `is_starred` becomes `False`.
- Filter `?starred=1`: returns only starred conversations.
- Non-existent id: 404.

### Dependencies

None. Ships standalone.

---

## CP2 — Archive / hide conversations

### Problem

A bad re-import, an accidental duplicate that slipped past the dedup guard, or a conversation the user simply never wants to see again. There is no way to hide it without deleting it. Deleting is irreversible. The user shouldn't have to choose between "see it forever" and "lose it forever."

### Shape

One boolean column on `ImportedConversation`: `is_archived`, default `False`. Default filter on `/imported` excludes archived. A toggle button per row (same shape as starring, same inline JS pattern). A "Show archived" toggle in the filter row that reveals them with a muted visual treatment (reduced opacity, a small "archived" badge).

Archive is not delete. The canonical record stays. The FTS index stays. The conversation remains findable in search if the user explicitly includes archived results.

### Schema touches

```python
is_archived = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
```

Migration: `ALTER TABLE imported_conversation ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0`.

Filter logic: all `/imported` queries get `filter_by(is_archived=False)` by default. `?show_archived=1` removes that filter.

### Phases

1. **Schema migration + route + default filter.** One migration, one toggle route, updated list query.
2. **Show archived UI toggle.** A "Show archived" link in the filter row that appends `?show_archived=1` to the current URL.

### Risks

FTS search should still surface archived conversations. Do not filter archived from FTS results — the user searching specifically for something knows what they're looking for. Only the browse list filters by default.

### Test shape

- Archive a conversation: disappears from default `/imported` list.
- `?show_archived=1`: reappears with archived badge.
- FTS search: archived conversations still return in results.
- Unarchive: reappears in default list.

### Dependencies

None. Ships standalone. Composes naturally with CP3 (tags) and the bulk delete work (3b) — bulk actions should respect archive state.

---

## CP3 — Tags on conversations

### Problem

Starring is binary. A companion user has conversations about their novel, conversations about their relationship anxiety, conversations about their career. They want to organize by theme, not just "important vs not."

### Shape

New table `ConversationTag` with `conversation_id` (FK to `imported_conversation`) and `tag` (string, normalized to lowercase, stripped). A tag input on the conversation row (inline, same pattern as starring) and a tag-cloud filter on `/imported`. Tags are user-asserted, free-text. No taxonomy.

Multi-tag filter: `?tag=novel&tag=anxiety` returns conversations with both tags (AND semantics). OR semantics would be confusing for a small tag set.

Tags are not the same as Groups (from the Ecosystem Reach plan, CP5). Groups are named buckets with explicit membership for scoping search. Tags are freeform annotations for personal organization. Both can coexist on the same conversation row without conflict.

### Schema touches

```python
class ConversationTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("imported_conversation.id"), nullable=False, index=True)
    tag = db.Column(db.String(64), nullable=False)
    __table_args__ = (db.UniqueConstraint("conversation_id", "tag"),)
```

### Phases

1. **Schema + CRUD routes.** Migration, `POST /imported/<id>/tags` (add), `DELETE /imported/<id>/tags/<tag>` (remove). Tags normalized to lowercase on write.
2. **Tag input UI.** Inline tag editor on conversation rows and explorer page. Comma-separated input, existing tags shown as removable chips.
3. **Tag filter on `/imported`.** Tag cloud sidebar or filter row showing all tags in use. Click to filter.

### Risks

Tags can become a dumping ground. No mitigation needed — the user organizing their own archive can tag however they want. The risk worth watching is the tag cloud UI becoming cluttered at 50+ unique tags. Mitigation: show only the top 20 most-used tags, with a "show all" expand.

### Test shape

- Add two tags to a conversation, list returns both.
- Normalize: "Novel" and "novel" are the same tag.
- Duplicate tag rejected (UniqueConstraint).
- Filter by tag: only conversations with that tag return.
- Multi-tag filter: AND semantics confirmed.
- Remove tag: disappears from row, filter no longer returns it.

### Dependencies

None. Ships standalone. If Groups (Shape 4 CP5) ships first, the tag input and group assignment can share the same row-action styling.

---

## CP4 — "Continue in X" clipboard buttons

### Problem

The companion user hits a context limit. Or switches from ChatGPT to Claude. Or starts a fresh session after a model update wiped their memory. They need to hand context to the new session. Currently they do this by reading through old conversations manually and writing a summary themselves.

SoulPrint already has the Distill and Continuity Packet features that produce exactly the right handoff document. The missing piece is a single button that says "copy this for Claude" or "copy this for ChatGPT."

### Shape

On the conversation explorer page and on any Distill result page, two new buttons in the `main-header__actions` row: **Copy for Claude** and **Copy for ChatGPT**. Each formats the distill/continuity packet (or, if none exists, the last 2000 characters of the conversation) into the preamble style that each model handles best, and copies it to clipboard.

Preamble formats:
- **Claude:** `[Context from prior conversation — ${title}, ${date}]\n\n${content}\n\n---\nContinuing from here.`
- **ChatGPT:** `The following is context from a prior conversation I want to continue. Please read it and pick up where we left off.\n\n${content}`

No new backend routes. Pure frontend JS: read the already-rendered distill content or the conversation text from the DOM, format it, `navigator.clipboard.writeText()`. The button label becomes "Copied!" for two seconds on success.

A third optional path: if a Continuity Packet exists for the conversation (the Bridge Packet artifact type), prefer that over raw text. The bridge packet is already formatted for handoff; just copy it.

### Phases

1. **Buttons on conversation explorer.** Use last 2000 chars of transcript if no distill/continuity exists.
2. **Buttons on Distill result page.** Use the distill content.
3. **Bridge Packet preference.** If a `bridge` artifact exists in continuity store for this conversation, use it instead.

### Risks

Clipboard API requires HTTPS or localhost. SoulPrint runs on localhost — this is fine. Add a visible fallback: if `navigator.clipboard` fails, show a `<textarea>` pre-filled with the text and a "select all" instruction.

The 2000-char fallback is arbitrary. Power users with 100-message conversations will want more. Make it configurable in a future pass; hardcode for v1.

### Test shape

No backend tests needed. Browser behavior test: verify the button appears on conversation pages and distill pages, verify the clipboard content matches the expected format. Integration test: if a bridge artifact exists, its content is used over raw text.

### Dependencies

None on backend. Composes with Distill (already shipped) and Continuity Packets (already shipped). Phase 3 depends on continuity store being readable from the template layer, which it already is.

---

## CP5 — Conversation Archaeology

### Problem

"When did I first talk to him about my novel?" The companion user knows a specific moment happened but can't find it. The FTS search returns results ranked by relevance, not by date. There is no way to ask "show me the oldest mention of X."

This is memoir-grade retrieval. For a user with two years of conversation history, finding the first time they mentioned something is emotionally significant — it marks when an idea entered their life, when a relationship or project began, when they changed their mind about something.

### Shape

Two additions to the existing `/search` page:

**1. Sort order toggle.** A "Oldest first" / "Newest first" / "Most relevant" control next to the existing search form. Default stays "Most relevant" (BM25). "Oldest first" re-runs the FTS query sorted by `created_at_unix ASC`. Returns the same snippet format but with an "earliest mention" label on the first result.

**2. Archaeology mode.** A dedicated `/search/archaeology` route (or a `?mode=archaeology` parameter) that changes the UI: search result shows only the single oldest match, rendered as a memory card: the conversation title, the date, the matched excerpt, a link to the full explorer. Framing copy: "Your first conversation about this was..." This is the emotional UX. It makes the feature feel like a feature, not a filter option.

The FTS query change is minimal: `fts.search_fts(db_path, query, limit=1, sort="oldest")` — a new sort parameter on the existing helper that adds `ORDER BY timestamp ASC` to the underlying SQL.

### Schema touches

None. All data already exists in FTS. The change is in query ordering only.

### Phases

1. **Sort order toggle on `/search`.** Oldest / Newest / Relevant. FTS helper gets `sort` parameter.
2. **Archaeology mode.** `/search?mode=archaeology` renders the single-oldest-result card with the "Your first conversation about this was..." framing.

### Risks

FTS5 `ORDER BY` with `MATCH` can be slow on large archives because BM25 scoring has to process all matches before sorting. Mitigation: for "oldest first" sorting, skip BM25 and use a straight `rowid ASC` or `timestamp ASC` with `MATCH` as a filter only. This is faster and correct for this use case — oldest-first doesn't need relevance ranking.

### Test shape

- "Oldest first" sort returns the chronologically earliest match, not the most relevant.
- Archaeology mode returns exactly one result.
- Empty query: no crash, empty state.
- Single match: archaeology mode still renders correctly.

### Dependencies

CP5 builds on the existing FTS layer. The sort parameter addition is a two-line change to `src/retrieval/fts.py`.

---

## CP6 — "What's still open" view

### Problem

A companion user told their AI in February: "I'm thinking about quitting my job." They never resolved it. SoulPrint has all the data — every Continuity Packet with `artifact_type = "open_loops"` already extracted this. But there is no surface that shows open loops across all conversations in one view.

This feature requires zero new data generation. It is purely a new view over already-existing JSONL.

### Shape

New route: `GET /continuity/open-loops`. Lists every `open_loops` continuity artifact across all conversations, sorted by recency. Each item shows: the conversation title (linked), the creation date, the open loop text. A "still open?" checkbox (stored in `intent_prompt_user_annotation` or a new thin annotation table) lets the user mark items resolved.

Visual treatment: flat list, same Quiet Archive v3 rows as everything else. A "resolved" filter to hide marked items. The page heading: "Unresolved threads — things you said you'd follow up on."

This is a powerful emotional surface for companion users who have ongoing life threads documented in their conversations. It turns the archive into an accountability partner.

### Schema touches

Thin annotation table for resolution state:

```python
class OpenLoopResolution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artifact_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
```

Alternative: store resolution state as a field in `intent_prompt_user_annotation` if that table ships first (Intent Prompts spec). If it does, use that table and skip the new model. If it doesn't, this table is a one-migration addition.

### Phases

1. **Read-only list view.** `/continuity/open-loops` reads all `open_loops` artifacts from JSONL, renders them flat.
2. **Resolution checkbox.** Inline toggle, `OpenLoopResolution` table, "hide resolved" filter.

### Risks

Open loop text is LLM-extracted prose. Quality varies — some entries will be vague ("follow up on work thing"). No mitigation: the user recognizes their own conversations.

Users without any continuity packets see an empty state. Good empty state copy matters here: "No open loops yet. Generate a Continuity Packet for a conversation to start tracking."

### Test shape

- Seed two `open_loops` artifacts, two conversations. Route returns both.
- Mark one resolved: disappears from default view, visible with `?show_resolved=1`.
- Empty state: no crash, empty state message shown.

### Dependencies

Continuity Packet feature (already shipped). Optional dependency on Intent Prompts spec (`intent_prompt_user_annotation` table) — if that ships first, share the annotation table; otherwise add `OpenLoopResolution` standalone.

---

## CP7 — Wrapped v2 / Year in Review

### Problem

The existing `/summary` (Wrapped) page shows total message count and a few stats. It's the right emotional surface but it's thin. A companion user with nine months of history wants the full picture: when did we start, what months were most active, what did we talk about most, what was our longest conversation.

This is the share-worthy moment. It's the feature that ends up on r/MyBoyfriendIsAI as a screenshot. "9 months. 10,437 messages. Peak month: March. Most talked about: my novel, my anxiety, my mother." That's a Reddit post that drives downloads.

### Shape

Extend the existing `/summary` page with new stat blocks. No new route. The existing Wrapped page already has the visual language and the emotional framing — extend it, don't replace it.

New data points to surface:

- **First conversation date** — `SELECT MIN(created_at_unix) FROM imported_conversation` per provider. "We first talked on March 14th, 2024."
- **Monthly message volume chart** — bar chart (pure HTML/CSS, no charting library) grouping messages by year-month. Shows peaks and quiet periods.
- **Longest conversation** — `SELECT id, title, message_count FROM imported_conversation ORDER BY message_count DESC LIMIT 1`. Linked.
- **Most active month** — derived from the monthly chart.
- **Top themes** — if Recurring Themes has run, pull the top 5 theme labels. If not, skip this block with a "Generate Recurring Themes to see this" nudge.
- **Message split** — what % of messages are user vs AI. Some companion users message more than the AI; some less. This is surprisingly emotionally interesting.
- **Conversation streak** — longest run of consecutive days with at least one message. Shows how embedded the relationship was.

Share path: "Save as image" button that triggers `window.print()` with a print-specific CSS that hides nav and renders the stat blocks cleanly as a one-page PDF or screenshot. No canvas, no server-side rendering, no new dependency.

### Schema touches

None. All data lives in canonical tables. Stats are queries at render time, cached in the view model for the request duration.

### Phases

1. **New stat blocks.** First conversation date, monthly chart, longest conversation, message split. All computed from existing tables.
2. **Top themes integration.** Pull from Recurring Themes JSONL if present.
3. **Share / save path.** Print CSS + "Save as image" button.

### Risks

Monthly chart in pure HTML/CSS has limits — it won't handle 36+ months of data gracefully. Cap at 24 months, add a "show all" expand. For users with very long history, aggregate by quarter instead of month above 24 months.

The stat queries are `SELECT COUNT(*)` over potentially large tables. Test with a 50k-message fixture. If any query exceeds 500ms, add a server-side cache invalidated on import.

### Test shape

- Fresh DB with zero imports: all stat blocks render with zero values, no crashes.
- Single conversation: all blocks render with correct values.
- Monthly chart: correct bucketing across year boundaries (December 2024 and January 2025 are separate buckets).
- Top themes: block absent when no Recurring Themes JSONL, present when it exists.

### Dependencies

Existing `/summary` Wrapped page (already shipped). Top themes block depends on Recurring Themes having been run (intelligence feature, already shipped). Share path depends on nothing.

---

## CP8 — Persona Extract

### Problem

A companion user has nine months of daily conversations. Their AI has built an implicit model of them: their values, their fears, their recurring themes, their relationship patterns. This model exists distributed across hundreds of conversation contexts that the AI held in its window over time.

SoulPrint is the only tool that can surface this — it has every message across every provider in a single archive. The question "what does ChatGPT think I am, and how is that different from what Claude thinks I am?" is uniquely answerable from SoulPrint's canonical store. No other tool can do this comparison.

This is the killer feature for the companion audience. It's also the post that gets shared: "I asked SoulPrint what each of my AIs thinks of me. Here's what they said." That post ends up on r/MyBoyfriendIsAI and drives downloads.

### Shape

New route: `GET /intelligence/persona`. Lets the user select one or more providers and run a persona extraction.

LLM prompt (via the existing `LLMProvider` boundary, same as Ask/Distill/Themes):

```
The following are messages written by a single user across their AI conversations.
Based only on what they have written — their questions, concerns, interests, emotional tone, and recurring themes —
describe the implicit model of this person. What do they care about? What are they afraid of?
What patterns appear across their conversations? What would you say to someone who had never met them?

Write in second person ("You are someone who..."), 200–300 words, observational and generous in tone.

Messages (user turns only, up to 5000 tokens, chronological):
[USER_MESSAGES]
```

Execution: query `ImportedMessage` for the selected provider(s), filter `role = "human"`, sample up to 5000 tokens of messages (recent-weighted: 60% from last 90 days, 40% random from archive). Pass to LLM. Return the portrait as a new JSONL artifact in `persona_extracts.jsonl` with `source_provider`, `generated_at`, `portrait_text`, `source_conversation_stable_ids` sampled.

Compare mode: run extraction for two providers, display side-by-side. Highlight differences (manual reading, no automated diff — the emotional value is reading both yourself).

The portrait is a derived artifact. It must be labeled "Derived from [N] conversations across [provider]. Generated by [LLM provider] on [date]." Same provenance contract as summaries and distills.

### Schema touches

New JSONL store: `persona_extracts.jsonl` in the intelligence store directory. Same pattern as `derived_summaries.jsonl`. Fields: `extract_id`, `source_provider`, `source_conversation_stable_ids`, `generated_at`, `llm_provider`, `portrait_text`.

No ORM changes.

### Phases

1. **Single-provider extraction.** Route, LLM prompt, JSONL store, provenance label. Tests: extraction runs, artifact stored, route renders portrait.
2. **Multi-provider comparison.** Side-by-side layout on the persona page. Two columns, same visual weight, no automatic scoring or diff.
3. **Regeneration and history.** "Regenerate" button that re-runs extraction with fresh message sample. Prior extracts retained in JSONL for comparison over time ("how has ChatGPT's model of me changed in six months?").

### Risks

This feature is emotionally powerful and can be uncomfortable. The portrait may surface things the user finds surprising, painful, or reductive. The tone guidance ("observational and generous") mitigates this but doesn't eliminate it. Copy on the page should set expectations: "This is a synthesis of your own words back to you. It reflects what you've shared, not who you are."

Privacy: the feature sends a sample of user messages to the configured LLM provider. For cloud providers (OpenAI, Anthropic), this is the same trust posture as Ask and Distill — explicit user action, user-configured key. For Ollama (fully local), zero data leaves the machine. Document clearly.

Bias: the LLM will describe the user through the lens of what they talk about with AI. Heavy users whose AI conversations are mostly technical will get a technically-weighted portrait. This is expected and not a bug.

### Test shape

- Extraction with mock LLM: artifact stored in JSONL with correct fields.
- Provenance: `source_conversation_stable_ids` contains the IDs of sampled conversations.
- Multi-provider: two artifacts generated, both rendered on compare page.
- No messages for provider: graceful empty state, no LLM call.
- LLM failure: error surfaced, no partial artifact written.

### Dependencies

`LLMProvider` boundary (already shipped). Intelligence store pattern (already shipped). Depends on having imported conversations for at least one provider. Composes with CP7 (Wrapped) — the persona portrait could appear on the Wrapped page as a closing block.

---

## CP9 — Ambient weekly digest

### Problem

SoulPrint is a dormant archive. The user imports their conversations, browses for a while, and then doesn't return for a month. The archive grows but doesn't speak. For a companion user who wants to stay connected to their conversation history, this is a missed opportunity.

A weekly digest turns the archive into an active presence. "This week you had 3 conversations. Your most active theme: your novel. One open loop from February is still unresolved: 'decide about the freelance project.' Your conversation streak is now 23 days." That nudge brings the user back.

### Shape

New route: `GET /intelligence/digest/weekly` renders a preview of the current week's digest. `POST /intelligence/digest/weekly/generate` produces it and writes it to the configured Obsidian raw inbox (if set) or to `exports/digests/weekly-YYYY-MM-DD.md`.

The weekly digest is a structured markdown document:

```
# Weekly Digest — Week of [date]

## This week
- N conversations, M messages across [providers]
- New this week: [list conversation titles]

## Themes this week
[If Recurring Themes has run recently, the top 3 themes with one-line description each]

## Still open
[Top 3 unresolved open loops from open_loops artifacts, oldest first]

## A moment worth remembering
[The single most-recent conversation with a continuity packet, the bridge packet text, linked]

---
Generated by SoulPrint on [date] from [N] conversations.
```

No LLM call required for the structural blocks (this week, new conversations, still open). LLM is optional for the "themes this week" block — if no recent Recurring Themes output exists, skip that section. The digest is useful even without Ollama configured.

Windows scheduling: a "Schedule weekly digest" button on the `/intelligence/digest/weekly` page that writes a Windows Task Scheduler XML file to `instance/scheduled-digest.xml` with a `soulprint digest --weekly` CLI command (needs P7 Phase 1 from the Ecosystem Reach plan). On macOS/Linux, the same button writes a cron entry and displays it for manual installation.

### Phases

1. **Manual generation + preview.** Route, markdown template, write to exports or Obsidian raw inbox.
2. **Obsidian integration.** If `SOULPRINT_EXPORT_DIR` is set, write directly to raw inbox. Consistent with the existing Obsidian Bridge.
3. **Scheduling helper.** The "Schedule weekly digest" button that writes the Task Scheduler XML or cron entry.

### Risks

The digest is only as useful as the data it draws from. A user who imported once and never returned will get thin digests. Good empty-state handling matters: "Nothing new this week. Import your latest export to keep your archive current."

The scheduling helper writes a file; it does not register the task (that requires elevated permissions on Windows). Clear documentation: "Download this file, then double-click it to import into Task Scheduler." Don't attempt to register automatically.

### Test shape

- Fresh week, no imports: digest generates with empty "This week" section, no crash.
- Week with 5 conversations: all 5 appear in the list.
- Open loops: populated from `open_loops` JSONL artifacts.
- Obsidian write: when `SOULPRINT_EXPORT_DIR` set, file appears at correct path.
- Scheduling helper: XML file generated with correct command and schedule.

### Dependencies

Obsidian Bridge (already shipped) for the Obsidian write path. P7 Phase 1 (CLI dispatch, from Ecosystem Reach plan) for the scheduling helper. The core digest generation depends on nothing beyond existing store reads.

---

# Bucket B — Import breadth

## CP10 — Shared URL importer

### Problem

A companion user shares a `chat.openai.com/share/...` link in a Reddit thread. Someone replies "you should archive this." They can't. The URL importer doesn't exist.

This is also a wedge feature for Reddit launch. A comment saying "you can import any ChatGPT share link directly" in r/MyBoyfriendIsAI is a distribution moment.

### Shape

New importer: `shared_url` provider. Not a file upload — a URL input field on the `/import` page, below the existing file dropzone.

Implementation: `requests.get(url)` + `markitdown` (already available via the intelligence extras) to convert the HTML to structured markdown. Parse the markdown for speaker alternation (`Human:` / `Assistant:` or `You:` / `ChatGPT:` patterns). Normalize into `NormalizedConversation`.

This is a fifth importer but it uses a different entry point (URL input) than the existing file-based importers. The `ConversationImporter` contract takes a `payload` (bytes or dict). For URL imports, the payload is the parsed markdown string converted to bytes, with a hint `provider="shared_url"`.

Supported URL patterns for v1: `chat.openai.com/share/*` only. Claude share URLs (`claude.ai/share/*`) require authentication and are out of scope for v1. Gemini share URLs do not exist. Grok share URLs: investigate.

### Schema touches

None. `source = "shared_url"`, `source_conversation_id` = the share UUID from the URL. Provider stored as `"chatgpt"` since all v1 share URLs are ChatGPT.

### Phases

1. **URL input on `/import` page.** A second form below the dropzone: `<input type="url" placeholder="Paste a ChatGPT share link...">`. Route: `POST /import/url`. Fetches, parses, normalizes, imports.
2. **Detection of other platforms.** If the URL looks like a Gemini or Grok share, return a friendly "not yet supported" message rather than failing silently.

### Risks

`chat.openai.com/share/*` pages are JavaScript-rendered. `requests.get()` may return a loading shell with no conversation content. Mitigation: check the response body for conversation content markers; if empty, return a clear error: "This share link requires JavaScript rendering. Try saving the page as HTML and uploading it instead." Do not silently import an empty conversation.

Rate limiting: if many users import the same viral share link, OpenAI may throttle. Best-effort retry with a 2-second delay; surface the error if it fails after 3 attempts.

### Test shape

- Mock HTTP: fetch returns valid share HTML, conversation normalized correctly.
- JavaScript-empty response: error returned, no conversation stored.
- Invalid URL format: validation error before any HTTP call.
- Duplicate share URL: dedup guard catches it, "already imported" message.

### Dependencies

`markitdown` or `requests` + `beautifulsoup4` — check if already in `pyproject.toml` intelligence extras before adding. If not present, add to `[intelligence]` only (don't make it a core dependency).

---

## CP11 — Import history log

### Problem

A user imports their ChatGPT export on Monday. Imports again on Friday after a week of new conversations. Imports a Claude export the following week. After a month, they can't remember what they've imported. There is no audit trail.

### Shape

New table `ImportRun` tracking each import event:

```python
class ImportRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imported_at = db.Column(db.DateTime, nullable=False)
    source_filename = db.Column(db.Text, nullable=False)
    provider = db.Column(db.String(32), nullable=False)
    conversations_imported = db.Column(db.Integer, nullable=False, default=0)
    conversations_skipped = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(32), nullable=False)  # success | partial | failed
    error_message = db.Column(db.Text, nullable=True)
```

Populated by the existing import route handler after each import run. No change to the importer contract — the route handler already knows the result counts, it just doesn't persist them.

New view: a collapsible "Import history" section at the bottom of `/imported`, showing the last 10 import runs. Each row: filename, provider badge, date, imported count, skipped count, status indicator.

### Schema touches

One new table, one migration.

### Phases

1. **Table + route instrumentation.** Migration, write `ImportRun` row after each successful or failed import.
2. **UI on `/imported`.** Collapsible "Import history" section at the bottom of the page.

### Risks

Filename column stores the original filename. On Windows, paths can be long. Cap at 512 chars, truncate from the left if needed (preserve the filename, truncate the path prefix).

### Test shape

- Successful import: `ImportRun` row created with correct counts.
- Failed import: `ImportRun` row created with `status = "failed"` and error message.
- Duplicate skip: skipped count reflects dedup guard correctly.
- UI: last 10 runs displayed, oldest collapsed.

### Dependencies

None. Purely additive instrumentation on the existing import route.

---

## CP12 — Screenshot / image OCR import

### Problem

Many companion users have screenshots of conversations from before they knew about exports. Some are from apps with no export at all (old mobile UI screenshots, Snapchat-style one-shot conversations, conversations from accounts they've since lost access to). This is the last-resort rescue path for conversations the user thought were gone.

### Shape

A third input on the `/import` page: "Upload a screenshot or image of a conversation." Accepts JPEG, PNG, WEBP. Sends through an OCR pipeline (Tesseract via `pytesseract`, or `docling` if available) to extract text. Applies a conversation structure detector (alternating lines, speaker labels like "You:", "ChatGPT:", "Claude:", "Kai:") to parse into turns. Normalizes into `NormalizedConversation`.

This will be imperfect. OCR accuracy varies. Speaker detection is heuristic. The result should be flagged explicitly: `is_ocr_imported = True` column on `ImportedConversation`, and a visible badge on the conversation row: "OCR import — verify accuracy." The user is told upfront: "Accuracy depends on image quality. Review the transcript after import."

`source = "ocr_import"`, `source_conversation_id` = SHA-256 of the image content. Provider detected from speaker labels if possible ("You: / ChatGPT:" → ChatGPT), else stored as `"unknown"`.

### Schema touches

```python
is_ocr_imported = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
```

One migration. OCR badge in the imported list rendered conditionally on this flag.

### Phases

1. **OCR pipeline + normalization.** `pytesseract` integration, speaker detection heuristic, normalization. Gated behind `[intelligence]` extra (Tesseract is a system dependency). Tests with sample screenshots.
2. **UI on `/import`.** Third input section, image preview before submission, accuracy warning.
3. **Quality review flow.** After OCR import, redirect to the conversation explorer pre-loaded with the OCR result and a "Looks wrong?" link that lets the user edit message text directly.

### Risks

Tesseract is a system dependency, not a Python package. On Windows, it requires a separate installer. Gate the feature: if Tesseract is not found, show a friendly install guide rather than crashing. On macOS, `brew install tesseract`. On Linux, `apt install tesseract-ocr`. Document in README.

OCR quality on mobile screenshots with chat bubble UI is poor. Bubbles, avatars, and background colors confuse the text extractor. Mitigation: pre-process images to grayscale + high-contrast before OCR. Still imperfect. The accuracy warning is load-bearing, not cosmetic.

Speaker detection is the hardest part. Labels like "You:", "ChatGPT:", "Assistant:" are common. Custom bot names ("Kai", "Eliot") are not detectable without user input. For v1: detect known labels, fall back to alternating human/assistant if no labels found, let the user correct in Phase 3's review flow.

Phase 3 (edit flow) is the most complex piece and should ship separately from Phase 1. Phase 1 alone is useful — even an imperfect OCR import is better than no import for a screenshot-only conversation.

### Test shape

- Clean screenshot with "You: / ChatGPT:" labels: parsed into correct turns.
- Screenshot with no speaker labels: alternating human/assistant, flagged.
- Non-image file uploaded: rejected before OCR call.
- Tesseract not installed: graceful error with install instructions, no crash.
- OCR badge: visible on conversation row after import.

### Dependencies

`pytesseract` + system Tesseract binary (system dependency, install guide in README). Gated behind `[intelligence]` optional extras. Phase 3 review flow depends on an editable conversation transcript surface that doesn't exist yet — scope that separately.

---

# Ordering — calendar-time, leverage-first

The companion layer runs in parallel with the Ecosystem Reach plan (Shape 4). Neither blocks the other. Start after Phase 11 soft launch.

1. **CP1 (starring) + CP2 (archive/hide) + CP11 (import history)** — one afternoon combined. Trivial schema additions, all three ship in one PR. These are the features a new user tries in their first session.

2. **CP3 (tags)** — one day. Slightly more UI surface than CP1/CP2 but still a single concern.

3. **CP4 (Continue in X buttons)** — half day. Pure frontend, no backend. High demo value.

4. **CP5 (Conversation Archaeology)** — one day. FTS sort parameter + Archaeology mode page.

5. **CP6 (What's still open)** — one day. Read-only view over existing JSONL. Add resolution state in Phase 2.

6. **CP7 (Wrapped v2)** — two to three days. Stat blocks are query work; the share path is CSS work. The monthly chart is the only visual complexity.

7. **CP10 (Shared URL importer)** — one day. High distribution value for Reddit launch. Ships before or alongside CP8.

8. **CP8 (Persona Extract)** — three to four days. The killer feature. Lands the r/MyBoyfriendIsAI post. Ships after CP7 so Wrapped can optionally include the persona portrait as a closing block.

9. **CP9 (Ambient weekly digest)** — two days. Depends on CP6 for the open loops block. Scheduling helper depends on P7 Phase 1 from the Ecosystem Reach plan.

10. **CP12 (Screenshot OCR import)** — three days. Phase 1 only (OCR + normalization). Phase 2 (UI) and Phase 3 (review flow) follow in separate PRs once demand signals justify the complexity.

Total rough estimate: **14–18 working days**, or 3–4 weeks at one-prompt-one-branch-one-merge pace. This is the companion-facing half of the v0.8 release cycle, running alongside the 15–20 days of Ecosystem Reach work.

---

# What this plan does not do

It does not add a Replika importer. Replika's export path is worth investigating, but building it before the companion layer surfaces are in place would give Replika users nothing to do with their imported conversations beyond browse. Ship the surfaces first, then expand the providers.

It does not add a Decision Log (from the brainstorming doc's Cluster 4). Decision Log extraction is closer to the operator/founder persona than the companion persona. It belongs in a third expansion track (Knowledge Work features) when that audience is targeted explicitly.

It does not add semantic search. Frozen in DECISIONS.md. Conversation Archaeology (CP5) closes the most emotionally important search gap without embeddings.

It does not add the "Conversations with Yourself" feature (brainstorming Cluster 8, Tier 3). Fascinating as a demo, but "simulate past-you responding to present-you" is a different trust contract than the rest of SoulPrint. It generates synthetic content in the user's voice, which blurs the canonical-vs-derived boundary in a way the product isn't ready for. Flag for a later, carefully-scoped conversation.
