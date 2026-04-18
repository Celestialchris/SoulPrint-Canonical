# SoulPrint Landscape

> Where SoulPrint sits relative to adjacent tools, patterns, and audiences.
> This file is landscape — how the market reads — not doctrine.
> Doctrine lives in [`positioning.md`](positioning.md) and is deliberately timeless.
> Landscape changes as competitors ship and fail; update this when it does.

---

## Structural cousin: Karpathy's knowledge-base pattern

In April 2026, Andrej Karpathy published a framework for LLM-maintained personal knowledge bases: ingest raw sources into a directory, have an LLM compile them into a wiki of concept articles with summaries and backlinks, query the wiki at scale without a RAG pipeline (up to ~100 articles / 400k words), run health checks for staleness.

**SoulPrint is the domain-specialized version of that pattern, applied to AI conversation exports specifically.** Substitute the nouns: where Karpathy writes "web articles, PDFs, papers in raw/," substitute "ChatGPT exports, Claude archives, Gemini Takeout files." Where he writes "LLM compiles concept articles," substitute "SoulPrint normalizes conversations and extracts themes." Where he writes "query the wiki without RAG at the 100-article scale," substitute "FTS5 search across all imported conversations, with a future ChromaDB upgrade path for heavy users."

This framing matters in three ways. First, it validates the paradigm: a respected senior voice has now written up the general pattern, which means the shape is legible to a wider audience than it was before the write-up. Second, it differentiates SoulPrint from the generic version: a generic wiki compiler treats all sources identically, but AI conversation exports have specific structure — messages, timestamps, provider boundaries, branches, attachments, user vs assistant turns — that a generic pipeline flattens. SoulPrint's specialized treatment of that structure is the moat. Third, it gives SoulPrint a single-sentence pitch for people who have read Karpathy: *"SoulPrint is the Karpathy knowledge base pattern, applied specifically to AI conversation exports."*

The self-referential note: if SoulPrint ever ships a self-hosted MCP server that lets AI coding agents reason over a user's local conversation archive, it will end up looking a lot like Nia (trynia.ai) — an indexer plus a search layer plus an MCP wrapper — but specialized for conversation archives instead of library documentation. That's not a current-you problem; it's a natural extension of the architecture already in place.

---

## Closest direct competitor: MyChatArchive

[MyChatArchive](https://github.com/1ch1n/mychatarchive) is the closest tool to SoulPrint in the local-archive space as of April 2026.

**Overlap.** Both are local-first, both import ChatGPT and Claude exports, both expose an MCP server for AI tools to query the archive, both treat the archive as a file the user owns.

**Non-overlap.** MyChatArchive imports ChatGPT, Claude, Grok, Claude Code terminal sessions, and Cursor IDE sessions. SoulPrint imports ChatGPT, Claude, Gemini, and Grok. Only SoulPrint supports Gemini exports (Takeout `MyActivity.json` and Chrome-extension conversational JSON). Neither currently supports CharacterAI; both see it as a natural next target.

**Engine differences.** MyChatArchive uses local vector embeddings (sentence-transformers). SoulPrint uses SQLite FTS5 with stable IDs and an explicit canonical/derived authority boundary. The FTS5 approach is simpler, more auditable, and matches SoulPrint's "archive is a file you can open in any SQLite viewer" promise. Vector embeddings trade simplicity for semantic-search quality; that trade is the right call for some users and the wrong call for others.

**License boundary.** MyChatArchive is AGPL-3.0. SoulPrint is Apache-2.0. **Format knowledge from MyChatArchive can be used for clean-room implementations of new providers; MyChatArchive code cannot be copied into SoulPrint under any circumstances.** Any importer written against MyChatArchive format knowledge must be clean-room: no copied function signatures, no copied parser structure, fresh implementation against a canonical spec. This was flagged during the Grok importer work and is worth repeating for every future provider.

**Strategic read.** SoulPrint and MyChatArchive are adjacent, not redundant. MyChatArchive serves developers who want semantic-search-over-conversations as part of their coding workflow. SoulPrint serves a broader audience — developers *and* non-developers who emotionally care about their conversation history — with a simpler engine and a different aesthetic. The two tools can coexist. If MyChatArchive adds Gemini or CharacterAI, this file gets updated.

---

## Differentiation from cloud memory silos

In March 2026, both Google and Anthropic launched features to import your AI conversations from other providers — into their own silos. The product truth: your conversation history is being treated as a retention mechanism, not a right.

SoulPrint takes the opposite position. The archive is a file on your machine. The archive is portable. The archive is inspectable in any SQLite viewer. The archive survives SoulPrint itself going away. This is the positional wedge that neither Google's nor Anthropic's offering can match without abandoning their own product incentives: a platform that imports your data into its silo cannot credibly promise to let you take it back out.

Cloud memory tools (Mem0, hosted ChatGPT Memory, Anthropic Memory) occupy a different product slot entirely — they're memory *for* a specific agent to use *during* a specific conversation, not a durable archive of conversations that have already happened. SoulPrint is archival; those tools are working memory. The two can coexist, and SoulPrint's optional mem0 adapter boundary is explicitly designed to let users feed archival records into a working-memory layer without making the working-memory layer canonical.

---

## Two audiences, two paths

SoulPrint has two audiences that arrive through different doors and need different framing.

**Developers and hackers** arrive through GitHub, care about architecture, install from source with `pip install -e .`, use the MCP server to connect SoulPrint to Claude Code or Cursor. For them the value is: local memory layer that any AI tool can query, clean canonical/derived boundaries, provider-agnostic importer contract, Apache-2.0 license, well-tested codebase. The README, `CONTRIBUTING.md`, and `docs/architecture/` are their entry points.

**Emotional-attachment users** arrive through Reddit posts (r/MyBoyfriendIsAI, r/Replika, r/CharacterAI, r/ChatGPT), the landing page, and word of mouth. They care about one thing: *their conversations being safe.* They do not know what GitHub is. They do not know what SQLite is. They have lived through "patch breakups" — the MIT Media Lab's clinical term for the grief users feel when a platform update wipes a bot's memory or changes its personality. The Replika February 2023 "lobotomy." The OpenAI mid-2025 GPT-4o migration. The Character.AI ongoing Moderatedpocalypse. For them the value is: one download, drop in your export, conversations safe on your machine, no cloud, no accounts, nobody can take this from you again. The landing page, packaged installer, and first-run experience are their entry points.

These audiences share the same product but read it in completely different vocabularies. The repository must serve both without letting either audience's framing dominate the other. The README achieves this by leading with the user promise ("Your AI conversations, home"), then offering a Download path for non-developers and a source-install path for developers, then describing the product in import/browse/search/distill/export terms that both audiences can follow.

---

## What's not in this file

- **Frozen product principles** — those live in [`positioning.md`](positioning.md).
- **Frozen architectural decisions** — those live in [`../../DECISIONS.md`](../../DECISIONS.md).
- **Launch plan and distribution** — lives in [`../releases/LAUNCH-PLAYBOOK.md`](../releases/LAUNCH-PLAYBOOK.md) and [`../releases/SOULPRINT-30-DAY-VISION.md`](../releases/SOULPRINT-30-DAY-VISION.md).
- **Feature roadmap** — lives in [`../../ROADMAP.md`](../../ROADMAP.md).

This file is the bridge between doctrine (what SoulPrint is) and distribution (how SoulPrint reaches people). It should be short, current, and updated when the landscape changes.
