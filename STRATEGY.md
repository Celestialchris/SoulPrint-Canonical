---
name: SoulPrint
last_updated: 2026-05-13
---

# SoulPrint Strategy

## Target problem

AI conversations are becoming a second working memory, but that memory is trapped in disposable threads. The hard part is turning those threads into a local, inspectable continuity layer without flattening them into summaries, losing provenance, or renting your mind back from another platform.

## Our approach

Start with custody, not convenience: the raw record stays sacred while every useful layer (search, Ask, Reader, Passport, handoffs) sits above it as a derived, inspectable surface. No single derived layer is mandatory or sacred. The work-of-the-work is part of the product, supported by an extracted private operating layer that runs an idea-to-implementation pipeline (idea generation, scoped prompts, expert routing, safe implementation branches, review support, learned patterns feeding back into the loop) so the system compounds how it gets built. Custody rules are strict: no uncontrolled autonomous commits, no public leakage, no replacing human merge authority.

## Who it's for

**Primary:** A solo builder directing AI agents across multiple assistants (ChatGPT, Claude, Claude Code, Gemini, Grok). The job-to-be-done has two coupled halves:

1. **Hold one canonical, inspectable record of AI conversations** and route clean portable exports to whatever Librarian layer is in use today (Obsidian, an internal Ask, a future tool, or none).
2. **Turn accumulated AI-assisted work into a better development process**: idea generation, implementation planning, expert-routed code execution, review support, and compounding learning, all under strict custody rules.

## Key metrics

- **Continuity coherence (Idea unity)** - whether SoulPrint can produce a usable continuity map across conversations, decisions, prompts, branches, notes, and learned patterns, in any output format (Markdown, Obsidian export, Reader/audio handoff). Measured weekly on 3 active ideas, scored 0-3.
- **Import fidelity** - share of conversations that round-trip Import → Canonical → Export with zero data loss. Measured by fixture-based contract tests under `tests/`.
- **Ask trust** - share of Ask answers whose cited canonical evidence actually supports the answer. Qualitative, weekly sample.
- **Operating-loop compounding** - when doing a similar task again, does the system require less re-explanation, fewer corrections, cleaner routing, safer implementation, and better reuse of prior learned patterns? Weekly review of 1-2 recent loops, scored 0-3. *Aspirational: protocol defined, measurement habit not yet built.*
- **Custody compliance** - incidents per quarter of autonomous commits, public leakage, or merge override from the operating layer. Target: zero, ever.

## Tracks

### Canonical Memory Core

Make the raw conversation ledger trustworthy, durable, and expandable.

_Why it serves the approach:_ protects the sacred record. Imports, stable IDs, provenance, attachments, export integrity, and schema discipline.

### Continuity Surfaces

Make the archive usable when you need to return to an idea.

_Why it serves the approach:_ turns the canonical record into derived but inspectable surfaces. Search, Ask, continuity maps, Markdown/Obsidian exports, Reader/audio handoffs, and bridge packets.

### Real Product Stack

Turn SoulPrint from a working local tool into a real, expandable app you can reason about.

_Why it serves the approach:_ keeps the foundation boring and reliable while gradually evolving the interface (Flask/Jinja now, SvelteKit/Tauri later) without any frontend becoming canonical.

### Operating Layer (private)

Make repeated AI-assisted work easier, safer, and more reusable over time.

_Why it serves the approach:_ a private operating layer for idea generation, scoped prompts, expert routing, quality pressure, reviews, safe branches, and learned patterns feeding back into future work.

## Milestones

One undated milestone, not a launch-pressure roadmap:

- **SoulPrint v1.0.0**: runnable, understood end to end, trusted, tested, exportable, and explained honestly. After that, share it only if there's genuine interest. No forced launch, no fake growth plan.

## Not working on

Commitments expressed in the negative. What gets ruled out when the approach is followed seriously.

*Commercial posture:*
- **Selling SoulPrint right now.** No asking people for money for code I don't understand.
- **Hosted SoulPrint / SaaS.** Local-first remains the default; no shared cloud infrastructure.

*System discipline:*
- **Code I can't reason about.** Nothing becomes part of the system unless I can inspect, approve, and maintain it.
- **Autonomous implementation authority.** No uncontrolled commits, no public leakage, no AI replacing human merge authority.

*Pluggability above canonical:*
- **Single-platform dependency.** SoulPrint must not depend on Obsidian, Web Clipper, Claude, or any one bridge staying available.
- **Frontend canonicalization.** Flask, SvelteKit, Tauri, or any UI layer must remain replaceable; the ledger stays canonical.

*Canonical sanctity:*
- **Replacing the canonical ledger with semantic memory.** RAG, mem0, embeddings, and similar systems can be downstream adapters, never the source of truth.
