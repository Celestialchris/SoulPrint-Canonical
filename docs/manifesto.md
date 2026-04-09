# Why SoulPrint Exists

Every day, millions of people pour their thinking into AI conversations: strategy, code, research, legal reasoning, medical questions, creative work. This is not casual chat. It is extended cognition: the overflow of human thought into a new medium.

None of it belongs to you.

Your conversation history sits on servers you don't control, in formats designed for lock-in, behind export flows that produce dead archives nobody can use. When you switch providers, or when they change terms, deprecate features, or shut down, that thinking disappears. A year of context, gone.

In March 2026, both Google and Anthropic launched features to import your AI conversations. Not into your hands, but into their competing silos. The message is clear: your memory is a retention mechanism, not a right.

SoulPrint takes the opposite position.

## The security problem nobody talks about

Your AI conversations are one of the highest-value datasets you produce. They contain how you think, what you're building, what you're worried about, who you're working with, and what you don't yet understand. For individuals, that's intimate. For organizations, it's a liability: proprietary logic, client details, internal strategy, all sitting in a third-party system with no audit trail and no access controls you define.

This is not a hypothetical risk. It is the default condition for every person using a hosted AI tool today.

## What SoulPrint does about it

SoulPrint is a local-first tool that imports your AI conversations from ChatGPT, Claude, and Gemini, normalizes them into a single SQLite archive on your machine, and gives you full-text search, cross-provider browsing, and intelligence features, all without making a single network call.

No telemetry. No analytics. No cloud. The archive is a file you own and can verify yourself.

When you use intelligence features like Distill or Ask, conversation data is sent to an LLM provider of your choice, using your own API key, only when you explicitly trigger it. Everything else runs offline.

## Principles

**Custody, not access.** You don't "access" your data through our interface. You hold a file. Open it in any SQLite viewer. It's yours whether SoulPrint exists tomorrow or not.

**Provenance over convenience.** Every conversation carries its source provider, original timestamps, and a checksum chain. Memory Passport exports include a manifest you can validate independently. If you can't verify it, you can't trust it.

**Local by architecture, not by promise.** SoulPrint doesn't avoid the cloud as a policy decision. The architecture has no networking layer. There is nothing to disable, no toggle to misconfigure, no server to breach. The absence of connectivity is structural.

**Intelligence without surveillance.** Distillation, theme extraction, and grounded Q&A work across your full conversation history. The computation happens through your own API key, under your own rate limits, with no intermediary.

## Who builds this

SoulPrint is built and maintained by a solo developer who needed it first and decided to ship it. The project is open-source under Apache-2.0. The code is public. The security policy is published. Contributions are welcome.

This is not a startup pitch. It's an infrastructure opinion: your AI conversation history is yours, it should be portable, verifiable, and secure by default, and no platform should be the sole custodian of how you think.

---

*Your memory. Your machine. Your custody.*
