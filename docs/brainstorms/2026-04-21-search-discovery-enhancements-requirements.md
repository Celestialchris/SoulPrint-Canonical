---
date: 2026-04-21
topic: search-discovery-enhancements
---

> **Superseded.** This combined brainstorm has been split into two focused documents:
> - [`2026-04-21-provenance-narrative-requirements.md`](2026-04-21-provenance-narrative-requirements.md) — shippable now
> - [`2026-04-21-tag-group-composition-requirements.md`](2026-04-21-tag-group-composition-requirements.md) — deferred until CP3 + P5 ship

# Search Discovery Enhancements (combined brainstorm)

Two complementary improvements to how users find and contextualize what is in their archive:
**Tag-Group Composition** makes the archive navigable by structure; **Provenance Narrative** makes
it navigable by time and meaning. Neither requires schema changes. Both ship on top of planned features
(CP3 tags, P5 groups, CP7 Wrapped).

## Problem Frame

**Organization without composition.** Tags (CP3) and Groups (P5) will ship as separate organizational
primitives. A user with conversations tagged "novel" and organized into a "work" group cannot find
conversations that satisfy both in a single search. They must filter in two passes. Power users, CLI
users, and MCP agents are hit hardest because they rely on a single query string across all surfaces.

**Timestamps without meaning.** Every imported conversation has a `created_at_unix` timestamp.
FTS results include message timestamps. This data is rendered technically — as an ISO date — but never
framed emotionally. A user searching "my novel" has no way to see when they first mentioned it without
manually switching to archaeology sort and scrolling.

## Requirements

**Tag-Group Composition in Search**

- R1. The FTS query string accepts `tag:X` and `group:Y` prefix tokens. Recognized prefixes are
  stripped from the query string before FTS5 MATCH processing; remaining terms are passed to
  `sanitize_fts_query` as before.
- R2. Multiple same-type prefixes (e.g., `tag:novel tag:anxiety`) use AND semantics — only
  conversations tagged with both are returned.
- R3. Mixed prefix types (e.g., `tag:novel group:work anxiety`) use AND semantics — the conversation
  must satisfy all prefix filters and contain the content terms.
- R4. Unrecognized prefixes (e.g., `foo:bar`) are passed through as quoted FTS content terms, not
  silently dropped or errored.
- R5. The prefix syntax works identically across the web search form (`/federated`), the
  `soulprint search` CLI subcommand (P7), and the `soulprint_search` MCP tool. No surface-specific
  translation required.
- R6. Tag and group filters apply at the conversation level, not the message level. A message-level
  result is returned only if its parent conversation satisfies all prefix filters.
- R7. If a `tag:X` prefix references a tag that does not exist in the archive, the search returns
  zero results with a specific empty state: "No conversations tagged 'X'." For an unknown group
  name, the equivalent message is "No conversations in group 'X'."
- R8. The feature ships alongside or after CP3 and P5. With only CP3 data available, `tag:` works
  and `group:` returns empty gracefully. With only P5 data, the reverse. Neither feature blocks the
  other.

**Provenance Narrative — Search Results**

- R9. When a search query returns more than one result, the chronologically oldest result is marked
  with a pinned callout block at the top of the results list. The callout appears above the main
  BM25-ranked list, not at the oldest result's natural rank position.
- R10. The callout contains: the label "Earliest mention in these results", a human-relative date
  (e.g., "14 months ago"), the absolute date, the provider badge, the conversation title, the matched
  excerpt, and a "→ Open conversation" link. It uses the same visual row design as standard results
  but with a distinct header band.
- R11. The oldest result is not removed from the BM25-ranked list below — it appears in both places.
  The callout is contextual framing, not a replacement.
- R12. For a single-result search, the callout is suppressed. The single result renders normally with
  its date visible.
- R13. When the user is already in archaeology sort mode (CP5 oldest-first), the callout is
  suppressed — the sort already surfaces the oldest result prominently.

**Provenance Narrative — Wrapped Page**

- R14. The Wrapped / Year in Review page (CP7) gains a new "Where it all started" block showing the
  single earliest conversation in the entire archive by `created_at_unix`. Contents: date, provider
  badge, conversation title, and a link to the explorer. No FTS query needed — this is a
  `MIN(created_at_unix)` query on `imported_conversation`.
- R15. The block is positioned near the end of the Wrapped page as a closing emotional beat — after
  the activity stats and before any share actions. Copy: "Your first conversation — [date]."
- R16. If the archive has fewer than 2 imported conversations, the "Where it all started" block is
  omitted entirely, not shown with placeholder copy.

## User Flow — Search with Prefix Filters

```
User types: tag:novel group:work anxiety
             │           │        │
             ▼           ▼        ▼
         tag filter  group filter  FTS content
         (AND)       (AND)         query

         ┌─────────────────────────────────┐
         │ Parse prefix tokens             │
         │  tag_filters  = ["novel"]       │
         │  group_filters = ["work"]       │
         │  content_query = "anxiety"      │
         └──────────────┬──────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────┐
         │ FTS5 MATCH "anxiety"            │
         │ WHERE conversation IN           │
         │   (tagged "novel")              │
         │   AND conversation IN           │
         │   (group "work")                │
         └──────────────┬──────────────────┘
                        │
                        ▼
              Results ranked by BM25
              (or sorted by date in
               archaeology mode)
```

## Search Results Page Layout

```
┌─────────────────────────────────────────────────────┐
│  EARLIEST MENTION IN THESE RESULTS                  │
│  March 14, 2024 · 14 months ago                     │
│  [chatgpt] Rainy day conversation                   │
│  "…been thinking about ⟨my novel⟩ for weeks now…"  │
│  → Open conversation                                │
└─────────────────────────────────────────────────────┘

  [claude] Story structure help — Apr 3, 2025
  "The arc of ⟨my novel⟩ keeps shifting…"
  → Open at this message

  [chatgpt] Character arcs — Feb 12, 2025
  "For ⟨my novel⟩ I want to avoid…"
  → Open at this message

  [chatgpt] Rainy day conversation — Mar 14, 2024  ← also in ranked list
  "…been thinking about ⟨my novel⟩ for weeks…"
  → Open at this message
```

*The callout is pinned at the top regardless of BM25 rank. The oldest result also appears in its
natural position in the ranked list.*

## Success Criteria

- A user typing `tag:novel group:work anxiety` in the web search form, CLI, and MCP tool receives
  the same filtered result set from all three surfaces.
- A user searching "my novel" in an archive with 2 years of history immediately sees "Earliest
  mention in these results — March 2024" at the top of results, without switching to archaeology mode.
- The Wrapped page's "Where it all started" block appears for any user with at least 2 imported
  conversations, linking to the explorer.
- An unknown tag or group prefix returns a clear empty state with a specific message, not a generic
  "no results" fallback.

## Scope Boundaries

- `provider:X` prefix syntax is out of scope. Provider filtering is an existing separate parameter;
  consider for a later extension once prefix parsing is proven.
- OR semantics for multiple same-type prefixes are out of scope. `tag:novel tag:anxiety` always means
  AND. OR support is a future extension.
- UI filter controls that generate prefix syntax are out of scope for Phase 1 — syntax only. Dropdown
  filter chips that produce `tag:X group:Y` tokens are a natural Phase 2.
- "First ever in entire archive" secondary query is out of scope. The callout uses the oldest result
  in the current result set. Archaeology mode (CP5) covers the absolute-first use case.
- Provenance narrative does not apply to native notes — only to imported conversations, which have
  reliable `created_at_unix` timestamps.
- No schema changes for either feature.

## Key Decisions

- **Prefix operators over UI panel**: uniform syntax across web, CLI, and MCP. All three surfaces get
  composition immediately with no API divergence. UI controls can be added later as a generator.
- **AND semantics for multiple prefixes**: conservative and predictable. OR would require a different
  syntax (commas, brackets?) and adds ambiguity for little gain in the common case.
- **Oldest result in current search (not archive-wide scan)**: avoids a secondary FTS query. Keeps
  the feature simple. Archaeology mode (CP5) already handles the "find the absolute first" use case.
- **Callout pinned at top**: provenance should be immediately visible, not buried at BM25 rank 12.
  The emotional value is lost if it requires scrolling to find.
- **Wrapped page closing block**: "where it all started" completes the Wrapped narrative — from
  activity stats to the archive's origin. A `MIN(created_at_unix)` query, no LLM required.

## Dependencies / Assumptions

- Tag-Group Composition depends on CP3 (tags on `ImportedConversation`) and P5 (group membership)
  having data in the database. The parser can be built before either ships, but returns no filtered
  results until at least one dimension has rows.
- `search_fts()` in `src/retrieval/fts.py` already returns `timestamp` (message-level) in each
  result dict — the provenance callout (R9-R12) uses this to identify the oldest result in the
  current set. The Wrapped page block (R14) uses `MIN(created_at_unix)` directly on
  `ImportedConversation` — a conversation-level field, not a message field. These two timestamp
  sources are distinct.
- The search results page (`federated.html`) is the primary search surface for provenance display.
- CP7 (Wrapped page, `wrapped.html`) must be in scope or already shipped before R14-R16 can land.
- The `sanitize_fts_query` function in `fts.py` will need a new pre-processing step that extracts
  prefix tokens before sanitization runs on remaining terms.

## Outstanding Questions

### Resolve Before Planning
None.

### Deferred to Planning

- [Affects R1, R5][Technical] The `sanitize_fts_query` function wraps all terms in quotes. The
  prefix parser must run before sanitization and extract recognized prefix tokens. Plan should define
  whether this is a new function (`parse_search_query`) or an extension of the existing sanitizer.
- [Affects R1, R6][Technical] Tag and group filters require SQL JOINs against `conversation_tag` and
  `conversation_group` tables (from CP3 and P5). `search_fts()` currently returns only FTS results;
  the route layer applies the conversation-level filter. Confirm whether filtering happens in the FTS
  query or as a post-filter step.
- [Affects R5][Technical] The MCP `soulprint_search` tool currently passes the query string directly
  to `search_fts()`. The prefix parser needs to be invoked at the same entry point. Confirm the MCP
  tool's call path.
- [Affects R13][Needs research] The callout is suppressed in archaeology mode. Confirm how CP5's
  archaeology sort mode is signaled to the template — is it a query parameter, a route variant, or a
  sort flag on the result set?
- [Affects R14][Technical] The Wrapped page's data is assembled at render time. Confirm the view
  model pattern used in `wrapped.html` and where the `MIN(created_at_unix)` query should be added
  (view helper, route, or template query).

## Next Steps
→ `/ce:plan` for structured implementation planning
