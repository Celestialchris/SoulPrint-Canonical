Here is the compact state map you can paste into your file.

## What we completed

**Phase 5 doctrine hardening reached a clean pause point.**
Rec 1, Rec 2, and Rec 3 shipped: Docs/Canon Steward exists, Routing Justification exists in Template H, and Proof Required blocks landed across the filled Section A experts. PR #201 merged the Proof Required field cleanly, with 8/8/8 symmetry across `Triggers`, `Proof required`, and `Out of scope`, while leaving Importer Engineer untouched. 

**The doctrine queue is parked, not abandoned.**
Remaining Phase 5 items are preserved: Rec 4 Routing Examples, Rec 5 Importer Engineer deferred, Rec 6 Release/Ops Engineer rejected for now, and audit-20 as the first normal routed audit after the Phase 5 self-exemption. 

**The Multi-Agent Forge pattern got named.**
The stable roles are now: Drafter, Higher Reviewer, and Adjudicator. The drafter authors the artifact, the higher reviewer pressure-tests final artifacts without competing rewrites, and the adjudicator owns merge authority. 

**The Librarian role is emerging as a fourth, non-execution role.**
Not another coder. Not another strategist. It compiles raw conversation material into usable vault memory: `raw/` source stays intact, `References/` gets compiled notes, and `_master-index.md` stays updated. 

**The Uncle Bob Quality Engine became the next real campaign.**
Layer 1 already exists: the CRAP scorer combines coverage and cyclomatic complexity, ranks functions, and produces reports. The quality MVP shipped as `feat/quality-toolchain-mvp`; it added `src/quality/`, tests, `coverage`, `radon`, CLI wiring, and the first quality report. 

**Current quality signal exists.**
The report already identifies top offenders, with `src/obsidian/exporter.py::refresh_vault` as the worst offender: complexity 64, coverage 52.2%, CRAP 510.02. 

**The one-branch rule got reframed.**
It remains valid for risky code, security, schema, CI, and migration work. But doctrine work had become too processional. The new rule is: one branch is a safety rule, not a lifestyle. 

## What is queued next

**Active lane: Uncle Bob Quality Engine.**

Next branch:

```text
feat/quality-threshold-ratchet
```

Goal:

```text
Turn the CRAP report from a scoreboard into pressure.
Add thresholds, check mode, and ratchet behavior.
```

Queued layers:

```text
Layer 2: quality-threshold-ratchet
Layer 3: quality-ci-reporting
Layer 4: mutation-testing-mvp
Layer 5: quality-hardening-loop
```

Layer 1 is already done. The rest is not built yet.

**Memory lane: Librarian / vault compilation.**

Queued work:

```text
Compile completed AI threads into References notes.
Preserve raw source material unchanged.
Update _master-index.md.
Create or update Evergreen notes only when a pattern generalizes.
```

The vault convention is clear: all content notes go into `References/`, raw source material stays in `raw/`, and category files are virtual views, not folders. 

**Parked doctrine lane.**

```text
Rec 4: Routing Examples
Route: Docs/Canon Steward + Teaching Engineer
Purpose: illustrative examples, not authoritative rules.

Rec 5: Importer Engineer
Status: deferred
Reason: wait for empirical importer friction.

Rec 6: Release/Ops Engineer
Status: rejected for now
Reason: not enough recurring release/ops evidence.

audit-20:
First normal routed routing-system audit.
Route: Docs/Canon Steward + Senior Engineer.
```

Phase 5 audit already accepted Routing Examples, deferred Importer Engineer, rejected Release/Ops Engineer for now, and set audit-20 as the future normal audit path. 

## Product and feature backlog already documented

**Frontend evolution.**
Current doctrine says: keep Flask/Jinja2 for ledger reliability, add JSON endpoints before richer frontend migration, then use SvelteKit + TypeScript for the cockpit only when specific interactions justify it. SQLite remains canonical. 

**Directive Prompts.**
Spec is authoritative. Route `/prompts`, UI label “Directive prompts,” seven-stage taxonomy, strictly-derived prompt rows plus first-class user annotations keyed on canonical message IDs. Build sequence is already defined as small PRs. 

**Session Attachments.**
Spec says Phases 1 through 4 shipped: asset ledger, conversation-level attachments, message-level attachments, and attachment-aware export bundles. Remaining future concept: project state capsules as a separate spec. 

**Obsidian Bridge.**
Phase 12 shipped a simpler raw-inbox bridge, but the full structured Chats/Themes/Daily vault layout may or may not be live. Needs source verification before treating the full spec as operational truth. 

**Companion Layer.**
Partially shipped: starring, archive/hide, tags MVP, open loops view, and import history/archive health. Remaining queued items include Continue-in-X buttons, archaeology, Wrapped v2, persona extract, weekly digest, shared URL importer, OCR import. 

**Ecosystem Reach.**
Partially shipped: Claude Code session auto-discovery exists in web UI, and CLI dispatch exists with `serve`, `info`, `verify`, and `mcp-config`. Remaining items include drop folder, write-capable MCP capture, groups, fuller CLI search/import/export/scan, and SSE MCP. 

**Tagging MVP.**
Authoritative v2 spec shipped: comma-string `ImportedConversation.tags`, auto-tag on import, inline editable chips on `/imported`, no normalized tag table yet. 

**Search Discovery Enhancements.**
The combined brainstorm was superseded and split into focused docs. It preserves two important future ideas: tag/group prefix composition and provenance narrative/earliest-mention callouts. 

## Agentic harness uncertainty

You have OpenSpec / `.agents` / Codex / Claude Code machinery configured, but the exact implementation is not yet mapped.

Current understanding:

```text
OpenSpec = workflow grammar
Template H = prompt construction law
experts.md = routing law
AGENTS.md = repo-wide model-agnostic behavior
.codex/agents = Codex role presets
.agents/skills = reusable skills/capabilities
.claude/rules = Claude Code hard constraints
CLAUDE.md = SoulPrint-specific Claude behavior
Librarian = vault compiler
```

Queued audit:

```text
agentic-harness-map
```

Purpose:

```text
Inventory .agents, .codex, .claude, AGENTS.md, CLAUDE.md.
Determine what reads what.
Find duplication, stale rules, and authority conflicts.
No edits first. Map before changing machinery.
```

## Current strategic stance

```text
Do not resume doctrine procession immediately.
Do not build more agent machinery blindly.
First: close/confirm PR #201 state if needed.
Then: move into Uncle Bob Quality Engine.
Parallel: let Librarian compile the completed threads.
Later: resume parked Phase 5 doctrine queue.
```

The north star:

```text
The law is now strong enough to guide work.
The next work should make the toolchain bite code.
```
