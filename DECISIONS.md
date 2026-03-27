# SoulPrint — Frozen Decisions

*Decisions recorded here are settled. Do not revisit unless the fundamental product thesis changes.*

---

## Architecture

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03 | SQLite is the canonical ledger. No vector databases, no Postgres, no hosted storage. | Local-first. Single-file truth. Portable. |
| 2026-03 | Four-layer architecture: Truth → Legibility → Intelligence → Distribution. Build in that order. | Prevents speculative infrastructure. Each layer depends only on the one below it. |
| 2026-03 | Every derived artifact (summary, topic, digest, continuity packet) must store: source conversation stable IDs, generation timestamp, LLM provider used, prompt template version. | Provenance is the product's moral backbone. Derived must never impersonate canonical. |
| 2026-03 | mem0 is optional, downstream, non-authoritative, and fully reconstructible from canonical data. It is not the engine for intelligence features. | SoulPrint owns its own truth chain. mem0 is a potential working-memory adapter, not a replacement for canonical storage. |
| 2026-03 | Retrieval is lane-aware (imported/native/federated) and read-only over truth. | Answering never mutates the ledger. |
| 2026-03 | Provider importers follow a fixed contract: adapter implementing `ConversationImporter`, `looks_like_*` detector, registry with auto-detection, fixture + tests. | Adding a provider is bounded, testable work — not a redesign. |

## Engineering

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03 | Continuity Packet (Lane 1) ships before Lineage Suggestions (Lane 2). | Lane 1 gives immediate value even with no linkage logic. Lane 2 only becomes valuable once the packet format exists. |
| 2026-03 | Continuity packet engine lives in the existing intelligence boundary (`src/intelligence/`), using the same `LLMProvider` interface as summaries and digests. | One intelligence boundary. No second brain. No hidden authority branch. |
| 2026-03 | Engine choice: BYOK over existing provider boundary. `SOULPRINT_LLM_PROVIDER` + `SOULPRINT_LLM_API_KEY`. OpenAI for speed/cost, Anthropic for quality. | Same pattern already working for summaries, topics, digests. |
| 2026-03 | Continuity artifacts are typed: summary, decisions, open loops, entity map, bridge packet. Not one generic blob. | Different memory shapes for different jobs. Generic summaries become graveyards. |
| 2026-03 | Lineage links (continuation/fork/revisit/supersede) are derived, not canonical. The canonical ledger is never mutated by lineage inference. | Silent continuity is dangerous. Inspectable continuity is SoulPrint. |
| 2026-03 | Topic scan has a keyword fallback when no LLM is configured. Continuity Packet MVP itself is LLM-backed structured synthesis; continuity-adjacent heuristics may add fallbacks in later phases. | Product stays useful before the user configures an API key. |

## Design

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03 | Design direction: "USB Drive." Near-black background (#0e0f11), green (#4ade80) trust accent, system sans-serif body, Forum wordmark, JetBrains Mono for labels. | Green communicates safety and trust for users handing over conversation history. Clean, minimal, not dashboard. |
| 2026-03 | Green (#4ade80) is the primary accent. Purple (#a78bfa) marks derived/generated surfaces. | Two-accent system. Green = action/trust. Purple = "this was generated." |
| 2026-03 | No box-shadows, no icons in nav, no font-weight above 500. Flat rows with border-bottom dividers. | Content sits on the dark background with typography and spacing creating structure. |
| 2026-03 | Provider lane colors: ChatGPT green (#4ade80), Claude purple (#a78bfa), Gemini blue (#60a5fa). | Lane identity through color, consistent with accent palette. |
| 2026-03 | The live `app.css` is always authoritative over doc files. | Prevents coherence drift between docs and implementation. |

## Product

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03 | Freemium split: import/browse/passport/traces = free. Ask/intelligence/distill = paid. Summary/Wrapped = free (growth hook). | Free tier must feel complete, not crippled. Intelligence is the natural upgrade. |
| 2026-03 | License validation is local-only. Key file at `instance/license.key`, prefix `SP-`. No server auth. No accounts. No login flow. | Local-first means local-first. |
| 2026-03 | Brand has two faces: public (lucid, premium, immediate) and inner (cinematic glow on Summary/Wrapped page). | Market viability without killing the soul. |
| 2026-03 | Nav grouping: Sanctum (Workspace, Ask) · Memory (Imported, Native, Federated) · Interpretation (Intelligence, Distill, Traces) · Continuity (Import, Passport). | Reduces taxonomy parsing. Makes the product feel authored, not listed. |
| 2026-03 | The "wow" moment is the Summary/Wrapped page. Dark, premium, cinematic, share-ready. This carries the strongest glow in the system. | The regular app stays calm and trustworthy. The summary page earns distribution. |
