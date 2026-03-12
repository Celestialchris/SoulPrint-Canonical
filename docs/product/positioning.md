# SoulPrint Positioning

## One-sentence definition
SoulPrint is a local-first memory passport for AI users: it helps you bring, unify, search, inspect, and carry your conversation history across tools with clear provenance and exportable continuity.

## Why SoulPrint exists
People now create valuable context across multiple AI products, but that memory is fragmented by platform silos. SoulPrint exists so users can keep durable, user-owned continuity instead of starting over whenever they switch tools.

## What SoulPrint does today
- Imports user-authorized AI conversation exports (currently ChatGPT export lane).
- Normalizes conversations/messages into stable, queryable records.
- Persists canonical records in local SQLite as the source of truth.
- Provides federated retrieval across native and imported lanes.
- Provides minimal local answering that is read-only and grounded in retrieved records.
- Supports markdown export for portable continuity.
- Keeps an optional mem0 adapter boundary available but disabled by default.

## What SoulPrint may become later
- Broader import lanes for additional platforms.
- Better local retrieval and inspection tools.
- Optional downstream working-memory integrations (for example mem0) that accelerate recall without replacing canonical storage.
- Optional document-QA style workflows over user-controlled exports.

## What SoulPrint is not
- Not a hosted memory SaaS platform.
- Not a replacement for user-owned canonical storage.
- Not an attempt to outbuild mem0 as infrastructure.
- Not an agent orchestration product at its core.
- Not a mythology-heavy "archive of humanity" pitch in active product docs.

## Who SoulPrint is for
- AI power users who work across multiple assistants and want continuity.
- Builders and researchers who need traceable memory with stable IDs/timestamps.
- Privacy-conscious users who prefer local-first control and exportability.

## Core product loop (user-facing)
1. **Import** your conversation exports.
2. **Normalize** into consistent records.
3. **Store** in a local canonical ledger (SQLite).
4. **Retrieve/inspect/export** with provenance so memory is reusable anywhere.

## Product principles
1. **Canonical ledger is authoritative.** SQLite records are the baseline truth layer.
2. **Derived layers are downstream.** Any adapter or summary layer must point back to canonical IDs/timestamps.
3. **Answering is read-only and grounded.** Retrieval and responses should never silently rewrite source records.
4. **Local-first by default.** Users can run and inspect the system without hosted dependencies.
5. **Portable continuity matters.** Markdown and stable records reduce lock-in and preserve user agency.

## Relationship to optional systems
- **mem0:** Optional downstream adapter for working-memory acceleration. It is not authoritative storage and is disabled by default.
- **Local RAG / document QA:** Optional subsystem for question answering over exported/user-owned material; separate from canonical ingestion and storage.
- **Obsidian/vault workflows:** Useful export and reflection destinations, not canonical runtime infrastructure.

