● Using ce-ideate to generate improvement ideas grounded in the two spec docs.

  Starting with Phase 0 — checking for prior ideation work and reading the spec files in parallel.

  Searched for 1 pattern, read 2 files (ctrl+o to expand)

● No prior ideation docs found. Both specs read. Now running Phase 1 codebase scan with parallel agents.

● 2 agents finished (ctrl+o to expand)
   ├ Explore (SoulPrint codebase quick context scan) · 9 tool uses · 69.1k tokens
   │ ⎿  Done
   └ compound-engineering:research:learnings-researcher (SoulPrint learnings search for expansion ideas) · 6 tool uses · 52.9k
      tokens
     ⎿  Done

● Phase 1 grounding complete. No prior learnings docs exist. Moving to Phase 2 — launching 5 parallel ideation sub-agents with
   distinct frames.

  ★ Insight ─────────────────────────────────────
  The specs cover ~25 features across two audiences but leave observable gaps: no canonical backup/integrity story, no
  onboarding flow, no device-sync path, and the Persona Extract's cross-provider angle only fires for multi-provider users.
  These are the seams ideation should pressure.
  ─────────────────────────────────────────────────

● 5 agents finished (ctrl+o to expand)
   ├ Ideation: user pain and friction frame · 13 tool uses · 61.6k tokens
   │ ⎿  Done
   ├ Ideation: unmet need / missing capability frame · 5 tool uses · 52.8k tokens
   │ ⎿  Done
   ├ Ideation: inversion / automation / removal frame · 3 tool uses · 46.3k tokens
   │ ⎿  Done
   ├ Ideation: assumption-breaking / reframing frame · 3 tool uses · 46.2k tokens
   │ ⎿  Done
   └ Ideation: leverage and compounding effects frame · 5 tool uses · 52.3k tokens
     ⎿  Done

● All 5 agents returned. Now merging 40 raw candidates, deduplicating (9 cluster groups), synthesizing 3 cross-cutting
  combinations, and running adversarial filtering.

  ★ Insight ─────────────────────────────────────
  The strongest ideas cluster around two systemic gaps the specs don't address: (1) the archive has no observable health story
   — users can't see when it's stale, corrupted, or growing; (2) derived intelligence features require manual triggering and
  have no management surface, which will become painful as Ask, Distill, Themes, Persona, and Digest all ship.
  ─────────────────────────────────────────────────

  ---
  Surviving Ideas — Phase 4 Review

  7 survivors from ~25 unique candidates. Full rejection summary below.

  ---
  1. Canonical Ledger Integrity Guard

  Description: On every canonical write (import, note capture), generate or update a sidecar manifest recording row counts per
   table, schema version, and a file-level checksum. On app startup, verify the manifest. If mismatch is detected, surface a
  clear warning with a recovery path pointing to the last passport export. CLI: soulprint verify.

  Rationale: The product's core promise is "local-first, verifiable." But there is no verification mechanism. SQLite
  corruption is silent — a failed write, a disk issue, or a partial migration can corrupt the ledger with zero user
  visibility. This feature puts substance behind the promise. It's also low code cost: a manifest file and a startup check.

  Downsides: The sidecar can go stale if the user copies the DB without it. False positives are possible around migrations.
  The "recovery path" to the passport is only useful if passports are current — pairs well with auto-export.

  Confidence: 90% | Complexity: Low

  ---
  2. First-Run Guided Import Wizard

  Description: On first launch with zero imported conversations, show a step-by-step modal: pick your provider from a grid of
  icons, see export instructions tailored to that provider (with a direct link to their export page), drag-and-drop your file
  with live provider detection feedback, and get an immediate import summary with counts and date range. Dismissible
  permanently. Banner fallback if the user skips it.

  Rationale: New users — especially the companion audience — land on an empty app with no signal about what to do. Import is
  behind a nav link. They don't know what file format ChatGPT uses, whether to unzip it, or what "provider" means. This is the
   product's emotional entry point, and currently it has no guidance. The first 5 minutes set the retention arc.

  Downsides: Provider export instructions need maintenance when providers change their UI (ChatGPT's export path has changed
  at least once). Modal requires a small JS component for drag-and-drop. Instructions will need separate copy for each of the
  4–5 providers.

  Confidence: 95% | Complexity: Medium

  ---
  3. MCP Agent Approval Gate

  Description: Change P4's soulprint_capture_note to write to a mcp_pending_write queue table instead of directly to
  MemoryEntry. The app shows an unread badge on the workspace nav. Clicking it opens a review list: captured content, agent
  identity, timestamp, reasoning. Per-item actions: [Accept], [Edit], [Reject]. Accepted writes become canonical MemoryEntry
  rows. Bypassable with SOULPRINT_MCP_AUTO_APPROVE=true for users who trust their agents.

  Rationale: P4's current design says "write silently, show a label afterward." That's a weaker trust contract than
  SoulPrint's posture warrants. An approval gate makes write-capable MCP consent-first, not post-hoc. The queue is also
  inherently auditable — the user can see everything an agent attempted, not just what got accepted. This distinction matters
  when agents loop or behave unexpectedly.

  Downsides: Adds friction. Power users automating with Claude Code will find the queue annoying and will need the
  auto-approve bypass. The queue must not grow unboundedly if the user ignores it for weeks — needs a configurable retention
  limit.

  Confidence: 75% | Complexity: Medium

  ---
  4. Tag-Group Composition in Search

  Description: Extend the FTS query sanitizer to recognize tag:X and group:Y prefix tokens. A query like tag:novel group:work
  anxiety becomes an FTS search for "anxiety" filtered to conversations tagged "novel" AND in group "work." Works identically
  in CLI (soulprint search), the web search form, and the MCP soulprint_search tool. No new UI for Phase 1 — the parser
  extension is the entire deliverable. Phase 2 adds filter chips that generate these queries visually.

  Rationale: Tags (CP3) and Groups (P5) are planned as independent features. Without composition in search, a user with 50
  tagged conversations across 5 groups must filter in two separate passes. Tag-group composition makes both features
  exponentially more useful the moment they both ship — the same query syntax works in CLI, web, and MCP, so power users and
  agents get equal access.

  Downsides: Adds parsing logic to the FTS sanitizer, which already handles edge cases carefully (NEAR, AND/OR, unbalanced
  quotes). Must document the query semantics clearly — prefix filters are AND-combined, not OR. The implementation needs tests
   across all three surfaces.

  Confidence: 88% | Complexity: Low

  ---
  5. Provenance as Emotional Feature

  Description: Surface the existing created_at_unix and source_conversation_id data as a user-facing narrative layer, not just
   a trust guarantee. On the conversation explorer, a quiet label: "Your first conversation on this topic was March 14th,
  2024." In search results, the oldest match is annotated: "First mentioned 14 months ago." In Wrapped v2 (CP7), the "You
  first talked to us about X on..." block becomes a closing emotional beat. The data already exists. This is a display pattern
   applied consistently.

  Rationale: Provenance is currently a technical feature — stable IDs, source identity, export integrity. The same data,
  framed emotionally, turns the archive from a database into a memoir. "You've been thinking about this for 14 months" is
  meaningfully different from "search result from 2024-03-14." No new schema, no LLM call, no new infrastructure — only a
  display decision that reframes what's already there.

  Downsides: "First mention of this topic" requires a query to find the earliest FTS match for a term across the archive,
  which can be slow for large archives. Needs caching or a derived index. Consistent UI treatment requires touching multiple
  templates.

  Confidence: 82% | Complexity: Low-Medium

  ---
  6. Living Archive Dashboard

  Description: A new /archive/health route (and soulprint info --health flag) that shows: last import date per provider with a
   staleness badge if >14 days, FTS index freshness (last rebuilt vs. last import timestamp), duplicate conversation count,
  archive growth diff since last import (N conversations added, M messages), and a per-provider message-count sparkline for
  the last 30 days. All data is queries over existing tables. The action link "ChatGPT last imported 23 days ago → [Export
  guide]" drives re-import behavior.

  Rationale: Users import, use the archive, and have no signal when it's stale or internally inconsistent. The FTS index can
  silently fall behind imports. Duplicates can accumulate without visibility. This dashboard makes the archive observable — it
   turns a passive collection into a monitored system. It also creates actionable nudges at exactly the moment the user is
  looking at their archive.

  Downsides: Some queries (COUNT on large imported_message) can be slow. A stats cache invalidated on import is needed for
  large archives. The sparkline is CSS-only (limited to ~30 bars), which breaks for users with very long history — cap at 90
  days.

  Confidence: 85% | Complexity: Low-Medium

  ---
  7. Auto-Intelligence Trigger on Import

  Description: After bulk import completes, show a post-import action panel: "Extract open loops and summaries from N new
  conversations? [Run now] [Skip]." If SOULPRINT_AUTO_DISTILL=true, run automatically in the background. The job calls Distill
   on each new conversation, writes artifacts to JSONL. Opt-in, gated on LLM configured. When done: "Intelligence refreshed —
  N summaries, M open loops extracted." Progress is visible in a task status area, with a cancel button.

  Rationale: Open loops, bridge packets, summaries, and themes are the intelligence promise. All require manual
  per-conversation triggering. For a user who imports 40 new conversations weekly, manual triggering is a workflow blocker
  that kills intelligence feature engagement. Auto-trigger on import makes the entire intelligence layer ambient. CP9 (weekly
  digest) and CP6 (open loops view) both become more useful when extraction runs automatically.

  Downsides: Requires LLM configured — no-op for users without Ollama or an API key. On large imports (200 conversations), the
   job runs for minutes. Needs a progress indicator and a cancellation path. Must not block the app on job execution.

  Confidence: 78% | Complexity: Medium

  ---
  Rejection Summary

  ┌─────┬──────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────┐
  │  #  │               Idea               │                               Reason Rejected                                │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 1   │ Provider Link Buttons in App     │ Too small — belongs in a QoL fix, not an ideation item                       │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 2   │ Auto-Rebuild FTS on Bulk Import  │ Bug fix / correctness issue, not a product idea                              │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 3   │ Proactive Continuity Injection   │ Browser-extension territory; outside Flask/local architecture                │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 4   │ Multi-User Co-Archives           │ Fundamentally different trust model; scope-expanding beyond v0.8             │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 5   │ Lateral/Structural Search        │ Undefined without semantic similarity, which is frozen in DECISIONS.md       │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 6   │ Implicit Thread Detection        │ Heuristic reliability too low without semantic matching; creates false       │
  │     │                                  │ associations                                                                 │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 7   │ Per-Provider Persona Fallback    │ Aspirational comparisons to other providers' "style" would mislead users     │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 8   │ Temporal Slice View              │ Weaker version of CP5 archaeology; best as an extension of it, not           │
  │     │                                  │ standalone                                                                   │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 9   │ Emotional Arc Timeline           │ Better as a CP7 Wrapped v2 extension than a separate feature                 │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 10  │ Visible Dedup & Merge Dialog     │ Partially addressed by P3's conflict handling; not novel enough              │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 11  │ Intelligence Layer Control       │ Important but premature — the problem isn't real until more intelligence     │
  │     │ Surface                          │ features ship                                                                │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 12  │ Passport-as-Sync-Transport       │ Clever but fragile — conflict semantics when two machines diverge are        │
  │     │                                  │ unresolved                                                                   │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 13  │ Per-Conversation Passport Export │ Good QoL but low leverage on other features                                  │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 14  │ Canonical Annotation Layer       │ Significant UI/data contract work; better after CP1-CP4 land first           │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 15  │ FTS-Powered Tag Suggestions      │ Tactical — belongs in a CP3 implementation PR, not ideation                  │
  ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 16  │ MCP Bulk-Action Tools            │ P4's trust model must prove itself before bulk operations expand it          │
  └─────┴──────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────┘

  ---
  What should happen next? Four options:

  1. Brainstorm a selected idea — pick one of the 7 and I'll run ce:brainstorm to define it precisely enough for planning
  2. Refine the ideation — add more ideas, raise the bar, or re-evaluate a rejected idea
  3. Save and end — write the ideation doc and close the session
  4. Save and hand off — write the doc, then move directly to brainstorming a specific idea