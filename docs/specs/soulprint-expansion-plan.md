# SoulPrint Expansion Plan — Ecosystem Reach & Hygiene

**Status:** planning draft
**Parent docs:** `ROADMAP.md` (Shape 4 — Ecosystem Reach), `SECURITY.md` (extended per Bucket 3)
**Precondition:** Phase 11 soft launch must ship first. None of this work starts before the Reddit posts land.
**Philosophy:** every item here has either a shipped MCA equivalent or a concrete trust-signal purpose. We adapt shape, not code. Apache-2.0 stays intact. Clean-room implementations against normalized formats, not against MCA's source tree.

---

## Why these, why now

MCA proves the developer-native pattern works. Auto-discovery of Claude Code sessions, drop folders, thread groups, write-capable MCP. These aren't novel ideas. They're established conventions in the local-first AI tools space. SoulPrint shipping without them reads as incomplete to the developer audience even though the web UI is more polished and the provenance story is stronger.

Bucket 3 is smaller in scope but compounds with Bucket 2. An expanded SECURITY.md backs the README's Trust section with concrete architecture details. A CoC signals community readiness. Proper pyproject metadata surfaces SoulPrint in `pip search` and future PyPI. Individually these are cheap; collectively they're the difference between "indie project" and "indie project ready for adoption."

The cost to close both gaps is low because the canonical ledger is already the right shape. Every Bucket 2 item is either a new importer adapter, a new CLI verb, a new MCP tool, or a small join table. No architectural reshape. No frozen decision from `DECISIONS.md` gets touched. Bucket 3 is doc edits and pyproject metadata, hours of work total.

Order below is leverage-first within each bucket.

---

# Bucket 2 — Product capabilities

## P1 — Claude Code session auto-discovery

### Problem

Claude Code writes session transcripts to `~/.claude/projects/*/`*.jsonl` on every machine. Developers using Claude Code accumulate dozens to hundreds of sessions. Today SoulPrint can't see any of it unless the user hand-exports, and Claude Code has no export UI. The entire working memory of SoulPrint's most valuable developer persona is invisible.

### Shape

Add a fifth provider to the importer registry: `claude_code`. Implement the `ConversationImporter` protocol in `src/importers/claude_code.py`. Source format is JSONL, one record per line, with `type: "user" | "assistant"`, `message.content` as either string or list-of-blocks (text, tool_use, tool_result), and ISO-8601 or epoch-ms `timestamp`. Tool uses and tool results preserve as inline text markers in the content field (`[Tool: Bash] ls -la` for tool_use, truncated results for tool_result). This matches how a human reading the transcript would want to see it.

Auto-discovery is a separate mechanism, not part of the importer contract. Lives in `src/importers/claude_code_discovery.py`. Scans `~/.claude/projects/`, reads each project's `sessions-index.json` for metadata (project path, summary, created/modified timestamps), yields file paths. The normal import pipeline takes over from there.

Per-project naming: each session becomes an imported conversation titled from the sessions-index summary if present, else from the project path, else from the session UUID. The project path becomes `source_metadata["project_path"]`. This makes conversation lists readable (you see "refactor auth module" not a UUID) and sets up the groups feature (P5) to filter by project.

### Schema touches

None. `ImportedConversation.source = "claude_code"`, `source_conversation_id = session_uuid`, messages get stable `source_message_id` from the JSONL record's `sessionId` plus sequence index. The existing persistence helpers handle it.

Contract additions in `src/importers/contracts.py`: add `PROVIDER_CLAUDE_CODE = "claude_code"` to the frozen set. Registry registration in `src/importers/registry.py`. Detector `looks_like_claude_code_export` checks for JSONL shape with `type: "user" | "assistant"` records — rejects regular Claude `.json` exports (which are single JSON objects, different shape).

### Phases

1. **Adapter only.** Implement `ClaudeCodeImporter.parse_payload` against a user-supplied JSONL file. Fixture: one real session file, anonymized. Tests in `tests/test_claude_code_importer.py`: empty file, single session, multi-turn with tool uses, malformed lines (gracefully skipped), missing timestamps. Registry integration, contract test. Ships as "point SoulPrint at a `.jsonl` file and it imports." Roughly 300 lines of adapter code plus tests.
2. **Auto-discovery scanner.** Add a `/imported/scan-claude-code` route and CLI verb `soulprint scan claude-code [--path ~/.claude]`. Route shows a pre-import summary (N sessions, M projects, date range) with per-session checkboxes so the user doesn't blind-import 400 sessions. Submit runs the normal import pipeline per-session with the adapter. Tests use a fake `~/.claude/projects/` tree.
3. **Watcher option (deferred).** A background thread or scheduled task that picks up new sessions as Claude Code writes them. Nice-to-have. Not in initial scope. Ships later if demand signals warrant.

### Risks

Claude Code's JSONL format is undocumented. It has changed at least once in the wild (the tool_use block shape is newer). Mitigation: version detection in the parser (look for shape signals like presence of `sessionId` field, block types in content array), graceful skip on unknown record types, warning output instead of hard failure. Test fixtures should capture at least two known format generations once we find them.

Tool_result blocks can be enormous (a `ls -R /` or a test suite output). The 500-char truncation in MCA's parser is reasonable but loses information. SoulPrint's version should truncate to a configurable limit (default 2000 chars) and surface a warning per-conversation like "N tool results truncated" rather than silently dropping.

### Test shape

- Contract: `claude_code` provider round-trips through `persist_normalized_conversations` preserving `source = "claude_code"`.
- Parsing: fixtures for single session, multi-turn, tool use + result, malformed lines, missing timestamps, list-of-blocks content.
- Discovery: fake `~/.claude/projects/` with two projects, three sessions each, `sessions-index.json` present for one project and absent for the other.
- FTS: imported Claude Code messages are searchable immediately after import (no manual rebuild needed).

### Dependencies

None on other Bucket 2 items. Can ship standalone. P5 (groups) composes naturally on top; `project_path` in source_metadata becomes the group key.

---

## P3 — Drop folder pattern

### Problem

Current flow: open app, navigate to /import, click upload button, browse filesystem, select file, submit. Five clicks for something that recurs weekly as users re-export their ChatGPT history. Power users notice.

### Shape

A watched directory. Default `~/SoulPrint/imports/` (configurable via `SOULPRINT_IMPORTS_DIR` env var). Anything dropped in gets auto-detected and imported on startup and on-demand. SHA-256 dedup by file content (not filename — people rename files) so re-dropping the same export is a no-op. Source files stay in place after import; the audit log records the import timestamp and result in a dedicated table.

Not a filesystem watcher. A polled scan. Two triggers:

- **On app startup** — auto-scan once. Results shown on workspace as a banner: "Imported 3 new files from drop folder. 1 already known, skipped." Dismissible.
- **Manual rescan** — `/imported/rescan` route and a "Scan drop folder" button on /import. Same flow.

No live watcher. File watchers are fragile on Windows (SoulPrint's primary platform), polling is good enough for a folder users interact with weekly, and skipping the watcher avoids a whole class of background-thread lifecycle bugs.

Recursive scan by default. Subdirectory conventions emerge naturally (`imports/chatgpt/2026-04/`, `imports/claude/`). The provider detector does the work; directory names are user organization only.

### Schema touches

Tiny. New table `drop_folder_import`:

```python
class DropFolderImport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_sha256 = db.Column(db.String(64), nullable=False, index=True, unique=True)
    filename = db.Column(db.Text, nullable=False)
    imported_at_unix = db.Column(db.Float, nullable=False)
    conversation_ids = db.Column(db.Text, nullable=True)  # JSON array
    status = db.Column(db.String(32), nullable=False)     # imported | skipped_duplicate | failed | needs_provider_hint
    error_message = db.Column(db.Text, nullable=True)
```

This is a derived-layer audit log, not canonical. A user wiping and re-scanning rebuilds it transparently.

Alternative considered: `.soulprint-imported.json` sidecar files next to each source file. Dismissed. Users back up their imports folder, copy it across machines, and the sidecar files would go stale relative to the SoulPrint database they're pretending to mirror. Database-owned audit log is cleaner.

### Phases

1. **On-startup scan.** Auto-run at app factory time, behind `SOULPRINT_AUTO_SCAN=true` env flag (default on). Produces the workspace banner. Route behind it: `/imported/drop-folder` shows the audit log.
2. **Manual rescan button.** Adds a single UI surface to trigger the same scan logic. Same result flow.
3. **CLI verb.** `soulprint scan --drop-folder` for headless use. Trivial wrapper around the scan function.

### Risks

False positives on provider detection for files that match multiple detectors. Today the registry raises `ImportProviderDetectionError` on multi-match, which is correct for single-file uploads. For drop folder, surface the ambiguity in the audit log with status `needs_provider_hint` and a UI action "Reimport as ChatGPT / Claude / …". Don't crash the whole scan over one ambiguous file.

Very large drop folders (user dumps 200 exports) can stall the workspace load. Cap on-startup scan to last-modified-within-7-days or similar. The manual rescan has no cap. Document clearly.

### Test shape

- Fake drop folder with known ChatGPT + Claude + Grok + Gemini exports plus one unknown format. Four imported, one in audit log with `failed` status.
- Re-scan after first scan: all four marked `skipped_duplicate`, zero new canonical rows.
- File with same SHA as a prior-imported file at a different path: marked `skipped_duplicate`, no canonical changes.
- Empty drop folder: clean no-op, no banner.
- Missing drop folder: created silently, no error.

### Dependencies

None. Composes with P1 — Claude Code JSONL files dropped in the folder get auto-imported by the same pipeline.

---

## P4 — Write-capable MCP (`soulprint_capture_note`)

### Problem

Today SoulPrint's MCP surface is read-only. Claude Code can search past conversations, but when a useful insight surfaces mid-coding ("oh, this connects to the payment-retry thing from last month"), there's no way to capture it back into SoulPrint without tab-switching to the web UI. The archive grows only through uploads. Not through use.

MCA's `capture_thought` closes this loop. It's the single most underappreciated feature in their toolkit.

### Shape

Add `soulprint_capture_note` to `src/mcp_server.py`. Takes `content` (required, the note body), `tags` (optional list of strings), and `source_context` (optional dict with `conversation_id`, `message_id`, `reasoning` to record what the note connects to). Writes a row to the existing `MemoryEntry` table with `role = "user"` (it's user-authored via the agent), `timestamp = now`, tags stored in the existing `tags` Text column.

Provenance is the whole game here. Every captured note needs to know:

- Was it written by a human typing in the UI, or by an agent via MCP? → new column `source_kind` on `MemoryEntry`.
- Which agent, which session? → MCP doesn't give session identity directly. Best we can do: record the MCP tool name and timestamp. Good enough for v1.
- What did the agent say it was capturing? → `source_context.reasoning` field. Stored as structured JSON in a new `capture_context` Text column on MemoryEntry.

Annotate the tool with `readOnlyHint: False, destructiveHint: False, idempotentHint: False, openWorldHint: False`. This tells MCP clients the tool writes but doesn't destroy — important for agent frameworks that gate on these hints.

### Rate limiting

Agents can loop. An LLM with tool access could capture thousands of notes in a runaway. Two defenses:

- **Per-call:** reject empty or duplicate-of-recent (content match within last 5 minutes) captures with a structured error.
- **Per-session:** max 100 captures in a 10-minute window, return a rate-limit error with `retry_after` hint.

Both defenses live in the MCP tool handler, not in `MemoryEntry` validation — agent-shape concern, not data concern.

### Schema touches

Add two columns to `MemoryEntry`:

```python
source_kind = db.Column(db.String(32), nullable=True)     # "ui" | "mcp_capture" | "clip"
capture_context = db.Column(db.Text, nullable=True)        # JSON blob, agent-provided context
```

Backfill existing rows to `source_kind = "ui"` on migration (or leave NULL and treat NULL as "ui"). Clip-to-notes feature already writes MemoryEntry rows; those get `source_kind = "clip"` via migration.

### Phases

1. **Schema migration + MCP tool.** Write the tool, thin shell over `db.session.add(MemoryEntry(…))`. Tests: capture with required content, capture with tags and context, capture with empty content (rejected), duplicate capture within 5 minutes (rejected).
2. **UI surface for captured notes.** `/memory` page already shows MemoryEntry rows. Add a filter/badge for `source_kind = "mcp_capture"` so users can see what the agent wrote. Hovering shows `capture_context`. This is a trust surface — users need to see what the agent is doing on their behalf.
3. **Write-back into conversation explorer.** When the agent captures with `source_context.conversation_id`, surface the note on the conversation explorer page as a linked annotation: "Claude Code captured a note on this conversation 3 hours ago." Closes the loop visually.

### Risks

Agent loops (defenses above).

User trust. Write-capable MCP is a different trust posture than read-only. Document prominently in README and MCP connection docs. The first thing a user sees when they enable the capture tool should be "This lets connected AI agents add notes to your archive. Notes are always tagged with their source. You can filter or delete them at any time."

Privacy. Agents capturing notes is a new way for conversation content to flow back into SoulPrint. If the agent is Claude Code against a Claude API key the user controls, fine. If it's some third-party agent in a Cursor config the user forgot about, it's a surprise. Mitigation: per-session rate limit and the prominent UI surface in phase 2.

### Test shape

- MCP tool contract: capture with valid content creates one MemoryEntry row with correct source_kind, tags, capture_context.
- Duplicate capture within 5-minute window rejected with structured error, no new row.
- Rate limit: 100 captures in under 10 minutes, 101st rejected.
- MemoryEntry query with `source_kind = "mcp_capture"` filter returns only agent-captured rows.
- Round-trip: capture via MCP → appears in `/memory` UI → deletable → next capture with same content succeeds (not treated as duplicate because the prior row is gone).

### Dependencies

None on other Bucket 2 items. Schema migration (two new columns) is the only infrastructure bit. Can ship before or after P3.

---

## P5 — Thread groups

### Problem

SoulPrint's archive mixes everything. Personal ChatGPT chats, work Claude sessions, random Grok experiments, Claude Code project work. Users want to scope search to "just my coding archive" or "just the work around SoulPrint itself." Today's only scoping is per-provider, which is the wrong axis: work and personal chats both happen in ChatGPT.

### Shape

A `thread_group` table, a `conversation_group` join table, and a `group` filter parameter on `soulprint_search`, `soulprint_list_conversations`, the `/imported` page, the `/federated` search page, and the CLI search (P7). That's the whole feature.

MCA names them "groups" because their unit is a "thread." SoulPrint's unit is a conversation — same thing, different word. We call them "groups" too; UX label is "Groups," surface vocabulary matches MCA. No need to invent a new term.

### Schema

```python
class ThreadGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)

class ConversationGroup(db.Model):
    """Join: which imported conversations belong to which group."""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("thread_group.id"), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("imported_conversation.id"), nullable=False, index=True)
    __table_args__ = (db.UniqueConstraint("group_id", "conversation_id"),)
```

Group memberships are user-asserted, not derived. No automatic grouping. An optional future feature could suggest groups based on title clustering or time ranges; v1 is strictly manual.

Groups do not interact with Projects (Shape 1 capture pipeline). Projects become first-class IDs later; groups become first-class names now. When Projects ships, we'll likely add `project_id` as a column on `ImportedConversation` (not a group membership), and Groups stays orthogonal. A Project is a structural fact from the provider; a Group is a user organization tag. Different axes.

### Phases

1. **Schema + CRUD.** Migration, `ThreadGroup`, `ConversationGroup`. Routes: `GET /groups`, `POST /groups`, `DELETE /groups/<id>`, `POST /groups/<id>/members`, `DELETE /groups/<id>/members/<conv_id>`. Minimal UI on `/groups` page listing groups with conversation counts. Tests round-trip.
2. **Group assignment UI.** On `/imported`, add a "Group" column with an inline dropdown per-row ("Add to coding… / Add to personal… / Create new group…"). On conversation explorer, breadcrumb chip showing current groups with remove action. Multi-select on `/imported` plus bulk-assign-to-group button (composes with Phase 11 multi-select export — same checkbox surface).
3. **Group-scoped search.** Add `group` parameter to `soulprint_search`, `soulprint_list_conversations`, FTS query helpers, `/federated` search form, `/imported` filter dropdown. Filter semantics: if group specified, return only conversations with a row in `conversation_group` with matching `group_id`. CLI `soulprint search "query" --group coding` (needs P7).
4. **MCP tool: group management.** Add `soulprint_list_groups` (read-only) and optionally `soulprint_create_group` / `soulprint_add_to_group` (write-capable, same trust posture as P4). Agents can organize the archive as they search. Deferred — gated on P4 shipping first so the write-MCP trust story is already established.

### Risks

Groups could balloon into a tagging system. Resist. Groups are named buckets with membership, not a taxonomy. If users want multi-dimensional tagging, that's a different feature (and probably not worth building — the `MemoryEntry.tags` field already handles freeform tagging at the note level).

A conversation in zero groups and a conversation in three groups need to render consistently in the imported list. Test the edge cases.

### Test shape

- Create group, add three conversations, list shows all three with group chip.
- Delete group: conversations unaffected, join rows removed.
- Filter search by group: only conversations in that group return.
- Bulk add: 50 conversations assigned to a group in one action, no duplicate memberships.
- Group name uniqueness constraint.
- Remove conversation from group, add back, count stays accurate.

### Dependencies

Shipped order: P5 Phase 1 (schema) → P1 Phase 2 (Claude Code auto-discovery with project_path in source_metadata) → P5 Phase 2 (bulk assign — Claude Code conversations naturally group by project). P7 (CLI) unblocks P5 Phase 3's CLI verb. P4 enables P5 Phase 4.

---

## P7 — CLI search, export, import

### Problem

SoulPrint ships as `soulprint` — one command, starts the web server. Power users and scripters want `soulprint search "something"` to print results to a terminal without opening a browser. MCA's `mychatarchive search --platform claude --since 2026-01-01` is the shape.

### Shape

Extend the existing `soulprint` entry point with subcommands. Today it's a single server-start command; after this it's `soulprint [serve|search|import|export|info|scan]`. Server-start stays the default when no subcommand is given (backwards compatible).

Candidate subcommands:

- `soulprint serve` — explicit version of the default. `--port 5678`, `--host 127.0.0.1`, `--no-browser`.
- `soulprint search <query>` — FTS over the archive. `--provider chatgpt`, `--group coding` (needs P5), `--limit 20`, `--json`, `--since 2026-01-01`.
- `soulprint import <file>` — import a single file. `--provider claude` hint, `--dry-run` shows what would be imported.
- `soulprint scan [drop-folder|claude-code]` — explicit scan of a drop folder or ~/.claude. Needs P1 and P3.
- `soulprint export <path>` — simple "dump all conversations as markdown." `--provider`, `--group`, `--format markdown|json|csv`. Not the passport export.
- `soulprint info` — stats (P8, below).
- `soulprint mcp-config` — prints the `.mcp.json` block for Claude Code / Cursor with correct paths.

Implementation: argparse (stdlib, no new dependency, matches codebase style). Subcommand dispatch in `src/cli.py`, each subcommand is a thin wrapper around existing retrieval/importer/FTS functions plus a `rich` terminal printer.

### Phases

1. **Restructure entry point.** `soulprint serve` becomes canonical, `soulprint` with no args dispatches to `serve` for backwards compat. Add `soulprint info` (P8) and `soulprint mcp-config` as the first two subcommands — both read-only, both fast, both demonstrate the pattern. Two evenings of work.
2. **`soulprint search`.** Reuses `src/retrieval/fts.py` with a terminal-output renderer. `--json` for scripting. Tests: basic query, provider filter, empty result, malformed FTS query (sanitized gracefully).
3. **`soulprint import` and `soulprint scan`.** Wires up P1 and P3 as CLI verbs. Tests: import a sample file, import with `--dry-run`, scan a fake drop folder.
4. **`soulprint export`.** The simple markdown dump. Passport export stays as its own thing (`soulprint passport export`) to keep the mental model clean — passport is a sealed, validated artifact; this export is a utility dump.

### Risks

CLI argument schemas grow organically and become incoherent. Mitigation: every subcommand takes the same common flags (`--db`, `--verbose`, `--json`) and feature-specific flags. Documented in a CLI reference section in CONTRIBUTING.md (not README — keep README product-focused).

Backwards compat. Today `soulprint` starts the server. Changing that would break shortcuts and desktop launchers. The phase-1 pattern (bare `soulprint` still starts the server) is a hard requirement.

### Test shape

- Subcommand dispatch: `soulprint info`, `soulprint search "query"`, `soulprint --help` all exit 0.
- JSON output parseable with `json.loads`.
- `soulprint serve` starts the server on the correct port and returns cleanly on SIGINT.
- Bare `soulprint` with no args matches `soulprint serve` behavior.

### Dependencies

Must land before P5 Phase 3's CLI group filter. No other upstream dependencies. Independent of P1, P3, P4 (though those become more usable once CLI exists).

---

## P8 — `soulprint info`

### Problem

No paste-worthy proof of archive size. MCA's README has `mychatarchive info` showing 47,832 messages and 1,204 threads — that single block is the most persuasive thing on their page. SoulPrint's workspace has the same stats in the UI but there's no terminal command to capture them into a screenshot, a blog post, or a Reddit thread.

### Shape

`soulprint info` prints (in `rich`-formatted text, with a `--json` flag for scripts):

```
SoulPrint — ~/.soulprint/soulprint.db
─────────────────────────────────────
  Conversations:    1,204
  Messages:         47,832
  Notes:                37
  Continuity packets:    9
  Passports exported:    3
  Providers:
    chatgpt:    912
    claude:     248
    gemini:      31
    grok:        13
  Date range: 2024-03-14 → 2026-04-18
  Database size: 128.4 MB
  Intelligence: Ollama + gemma4 configured (last ran 2 hours ago)
```

The last line is the differentiation hook. MCA doesn't surface LLM config status; SoulPrint's intelligence-is-local story benefits from making it visible.

### Schema touches

None. All stats are queries over existing tables. The "intelligence configured" line reads from the provider config (`SOULPRINT_LLM_PROVIDER` env plus `src/intelligence/provider.py::is_llm_configured()`). Last-ran timestamp requires either a new column on the existing summary store to record generation time (probably already there — check `src/intelligence/store.py`), or filesystem mtime on the summary store file.

### Phases

One phase. Ship as part of P7 Phase 1.

### Risks

Stats slow on very large archives. Test with a 50k-message fixture. If `SELECT COUNT(*)` on `imported_message` is >2s, denormalize into a stats cache updated on insert. Unlikely at current scales; document the threshold.

### Test shape

- Fresh DB: all zeros, no errors.
- Populated DB: counts match expectations.
- `--json` output parseable.
- Missing intelligence config: "Not configured" on that line, not a crash.

### Dependencies

Needs P7 Phase 1 (CLI dispatch). Trivial after that.

---

## P9 — SSE/HTTP MCP transport

### Problem

SoulPrint MCP today runs on stdio. Stdio MCP is local-only by design — connected tool spawns the server as a subprocess, reads/writes via pipes. Works perfectly for Claude Code / Cursor on the same machine. Fails entirely for "access my archive from my phone" or "have my NAS run the server and every machine in the house connects to it."

### Shape

MCP's SSE (Server-Sent Events) transport is the standard answer. FastMCP (the library SoulPrint already uses) supports it natively:

```python
mcp.run(transport="sse", host="127.0.0.1", port=8420)
```

CLI flag: `soulprint serve --mcp-transport sse --mcp-port 8420` (default stays stdio). Binds to 127.0.0.1 by default so SSE on localhost works immediately and remote access is opt-in. Opt-in remote requires `--mcp-host 0.0.0.0` and a warning printed at startup.

Remote access requires either a VPN (Tailscale, WireGuard) or an auth layer. SSE MCP without auth on 0.0.0.0 is an open archive. Very bad. Shipping order:

1. **SSE on 127.0.0.1 only.** Unblocks "multiple local processes talking to one archive" use case. No auth needed because nobody off-machine can reach it.
2. **Auth layer.** Bearer token via `SOULPRINT_MCP_TOKEN` env var. Server generates a token on first run if not set, prints it. Clients pass it in the `Authorization: Bearer` header. MCP spec supports this.
3. **Remote-friendly binding.** `--mcp-host 0.0.0.0` allowed only after auth layer ships, always with the auth token required.

The Phase 11 deferred-P1 item (loopback restriction on `SOULPRINT_LLM_BASE_URL`) is the same shape of concern and the same fix pattern. Share the helper.

### Schema touches

None. Auth token stored in `instance/mcp-token` file, permissions 0600.

### Phases

1. **SSE on 127.0.0.1.** One CLI flag, one FastMCP config change, docs update. Tests: server starts, `curl http://localhost:8420/mcp/sse` returns the handshake.
2. **Auth layer.** Tests: request without token rejected 401, request with wrong token rejected 401, request with correct token proceeds.
3. **Remote binding plus docs.** Runbook for Tailscale setup, NAS deployment sketch (docker-compose file), explicit security notes in SECURITY.md.

### Risks

Auth bugs are the entire game here. A misconfigured MCP server exposing the archive on the public internet would be a trust incident. Reduce scope ruthlessly: Phase 3 (remote binding) does not ship until Phase 2 (auth) has been security-reviewed by at least one outside contributor and has shipped tests covering every bypass attempt we can imagine. If no reviewer is available, Phase 3 waits.

SSE specifically (versus WebSocket or HTTP long-poll) is the MCP standard right now. The standard may evolve. Pin the MCP library version in pyproject.toml and re-evaluate on upgrade.

### Test shape

- SSE server starts on configured port, responds to handshake.
- Auth required: 401 without token, 200 with correct token.
- Tool calls over SSE return same results as over stdio (regression test using existing MCP tool contract).
- Default bind is 127.0.0.1: connection from another machine fails with connection refused.

### Dependencies

Ships independent of other P-items. Lowest priority because the user base that needs remote MCP is small. Don't prioritize over P1/P3/P4/P5.

---

# Bucket 3 — Doc and repo hygiene

These items are small individually. Their value is compound: an expanded SECURITY.md makes the README's Trust section land with specifics; a Code of Conduct signals community readiness; proper pyproject metadata surfaces SoulPrint in package search; a LICENSING.md disambiguates Apache-2.0 plus bundled assets. None takes more than a couple hours. All land before v0.8 ships.

## D1 — SECURITY.md extension

### Problem

Current SECURITY.md is 16 lines. It covers the big points (local-first, BYOK, vulnerability reporting) but doesn't enumerate attack surface, doesn't document the security posture of specific subsystems, doesn't tell a developer auditing SoulPrint what they're looking at.

The README's Trust section makes concrete promises: no telemetry, no phone-home, explicit outbound on intelligence features only. SECURITY.md is where those promises become technical claims with file paths and function names behind them.

### Shape

Extend SECURITY.md to enumerate:

1. **Data locations.** `instance/soulprint.db` (canonical), `exports/` (passports, markdown), `instance/license.key` (license), `instance/mcp-token` (future P9). Filesystem permissions guidance (0600 for token, 0644 for db is fine because it's read by the user).
2. **Attack surface enumeration.**
   - Import parsers (malformed export files — gracefully-handled parse errors, no eval/exec in any parser).
   - Flask web UI on 127.0.0.1:5678 (loopback only — don't bind 0.0.0.0 without auth).
   - MCP server on stdio (subprocess-spawned, no network surface).
   - Intelligence features (the sole outbound network call; explicit per-feature consent).
   - Future SSE MCP (P9) documented as opt-in remote, auth-required.
   - Obsidian bridge (file writes to a user-configured vault directory; no filesystem escape).
3. **What SoulPrint does not do.** No analytics, no telemetry, no phone-home, no auto-update, no crash reporting, no third-party SDK, no tracking pixel. Named, not implied.
4. **What a supply-chain attack against SoulPrint looks like.** pip install compromise is the primary risk. Users should verify the release signature (when we ship one) and pin versions in production use. We don't sign releases today; this is a known gap and listed as such.
5. **Best-practices runbook.** Don't open ports to the internet. Use local-only Ollama for intelligence features. Back up your SQLite file. Rotate your `SOULPRINT_LICENSE_OVERRIDE` if you leaked it. Lock down your `instance/` directory on shared machines.

### Phases

One phase, ~80-100 lines of markdown. Done in an afternoon. See the draft at the end of this document.

### Dependencies

None. Write this first because the README's Trust section references it.

---

## D2 — CODE_OF_CONDUCT.md

### Problem

SoulPrint is approaching a public Reddit launch. Contributor communities form at launch, not before. Having a CoC present at launch signals "this is a project that takes community seriously" to potential contributors and filters out bad-faith actors.

### Shape

Drop-in Contributor Covenant 2.1. MCA uses it. Most mature OSS projects use it. The text is standard; the only SoulPrint-specific edit is the contact email. Use whatever reporting channel exists (GitHub Security Advisories for security issues, an email for CoC reports).

### Phases

One phase. Copy-paste, one substitution, commit. 15 minutes.

### Dependencies

None.

---

## D3 — pyproject.toml metadata

### Problem

Thin `pyproject.toml` hurts pip discoverability and future PyPI publish readiness. MCA has keywords and classifiers populated; SoulPrint likely doesn't (audit first).

### Shape

Add or extend:

- `keywords` — `["ai", "chat", "archive", "mcp", "local-first", "llm", "memory", "conversation-history", "chatgpt", "claude", "gemini"]`
- `classifiers` — Development Status, Intended Audience, License, Python versions, Topic, OS (Windows/macOS/Linux).
- `[project.urls]` — Homepage (soulprint.dev), Repository (github), Issues, Documentation, Releases.
- `[project.optional-dependencies]` — Confirm `[intelligence]` extras are listed. Consider `[dev]` extras for test dependencies (pytest, ruff) so `pip install -e ".[dev]"` works as expected for contributors.

### Phases

One phase. 30 minutes to audit and update.

### Dependencies

None. Lands anytime.

---

## D4 — CONTRIBUTING.md clarity pass

### Problem

CONTRIBUTING.md exists. Haven't fully audited it. Likely covers setup and style but probably not enough: test patterns, importer contract, how to add a provider, how MCP tools are registered, how the trust chain is preserved across changes.

### Shape

Audit current CONTRIBUTING.md against these checkpoints:

1. **Quick-start for contributors.** `git clone`, `pip install -e ".[dev]"`, `pytest`, `soulprint`. Should work in 60 seconds on a clean machine.
2. **Architecture pointer.** Four-layer architecture summary (canonical → legibility → intelligence → distribution) with pointers to `docs/architecture.md` for depth.
3. **Adding a provider.** Pointer to `docs/specs/` or a dedicated `docs/adding-a-provider.md` that walks through the importer contract, detector, fixture, registry entry, tests. Use the existing four providers as templates.
4. **Adding an MCP tool.** Pattern from `src/mcp_server.py` — FastMCP decorator, annotations, docstring conventions.
5. **Test patterns.** Pointer to `.claude/rules/soulprint-testing.md` if committed, or inline the key points (make_test_temp_dir, release_app_db_handles, no mocking SQLAlchemy).
6. **What not to do.** Frozen decisions from DECISIONS.md — no vector DB, no semantic search replacement, no agent frameworks, no async routes. Link to DECISIONS.md for the full list.

### Phases

One phase. A couple hours if the current file is thin; longer if gaps emerge.

### Dependencies

None.

---

## D5 — LICENSING.md clarification

### Problem

Apache-2.0 on the code is clear. Bundled assets are less clear — bundled fonts (Playfair, DM Sans, JetBrains Mono), bundled logo, bundled sample data. Each has its own license. A LICENSING.md (or an expanded section in README) disambiguates what's Apache-2.0 code, what's OFL fonts, what's other.

### Shape

A short LICENSING.md that enumerates:

- **Code.** Apache-2.0. See LICENSE.
- **Bundled fonts.** Playfair Display (OFL), DM Sans (OFL), JetBrains Mono (OFL). All redistributable under the SIL Open Font License.
- **Bundled logo / brand assets.** If any — clarify user rights.
- **Sample data.** Sample imports in `sample_data/` — synthetic, CC0 / public domain dedicated so users can round-trip tests without license worry.

### Phases

One phase. 30 minutes.

### Dependencies

None.

---

## D6 — Release signing preparation (tracked, not scheduled)

### Problem

Today SoulPrint releases are unsigned. An attacker who compromises the GitHub Releases CDN could substitute a malicious installer and users would have no way to detect it. For a product that promises "local-first, no cloud, verifiable," unsigned binaries are a gap worth naming.

### Shape

Sign future releases with a PGP key. Document the key fingerprint and verification instructions in SECURITY.md. Alternative (simpler) path: publish SHA-256 sums in release notes, signed by a PGP key or committed under a Git tag that GitHub signs. Either way, the user can verify.

### Phases

Not scheduled. Listed in SECURITY.md as "future work" so users know we're aware of the gap. Schedule when the user base gets large enough to be a target.

### Dependencies

None on Bucket 2. Relies on having a stable signing key which is an operational decision, not a code change.

---

# Ordering — calendar-time, leverage-first

1. **D1 (SECURITY.md extension)** — afternoon. Unblocks README Trust section having something to point at. Ships in the same PR as the README rewrite.
2. **D3 (pyproject.toml) + D5 (LICENSING.md) + D2 (CoC)** — one afternoon combined. Hygiene sweep.
3. **D4 (CONTRIBUTING.md audit)** — a couple hours. Lands before soft launch.
4. **P1 Phase 1 (Claude Code adapter)** — 1-2 days. Highest-leverage single win. Lands a Reddit post in r/ClaudeAI on landing.
5. **P8 + P7 Phase 1 (soulprint info + CLI dispatch)** — 1 day. Unblocks everything else and lets us screenshot a real stats block for the README.
6. **P3 Phase 1 (drop folder on-startup scan)** — 2 days. Dramatic friction reduction, one Reddit post worth alone.
7. **P1 Phase 2 (Claude Code auto-discovery UI)** — 1-2 days. Upgrades P1 Phase 1's wow factor.
8. **P5 Phases 1 + 2 (groups schema + UI)** — 2-3 days. Unlocks the "scope my coding archive" query pattern.
9. **P4 Phases 1 + 2 (capture MCP + UI surface)** — 2 days. Closes the read-write MCP loop.
10. **P7 Phases 2 + 3 (search, import, scan CLI)** — 1-2 days once P7 Phase 1 is in.
11. **P5 Phase 3 (group-scoped search)** — 1 day. Finishes groups.
12. **P9 (SSE MCP)** — 2-3 days if scoped to localhost-only. Optional.

Total rough estimate: Bucket 3 is ~1 day end-to-end. Bucket 2 is 15–20 working days, or 4–5 weeks at one-prompt-one-branch-one-merge pace. This is the v0.8 release cycle.

Everything after Phase 11 soft launch. Nothing before.

---

# What this plan does not do

It does not add semantic search via embeddings. DECISIONS.md has that frozen, and nothing here changes the thesis that FTS5 + Ollama is the right local-first retrieval stack. If semantic search ever ships, it goes in as a derived layer above canonical, clearly labeled derived, opt-in.

It does not add a Cursor importer. Explicit cut. Cursor's conversation store is a local SQLite with undocumented schema that changes. Audience is small, maintenance cost is high. Not worth it.

It does not change the importer contract, the canonical ledger shape, the provenance rules, the design system, or the two-audience distribution strategy. Everything here is additive to surfaces (new CLI verbs, new MCP tools, new importer adapters, new join tables) rather than reshaping core.
