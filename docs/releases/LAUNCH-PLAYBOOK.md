# SoulPrint Launch Playbook

*From repo to real users. Every post, every platform, every angle.*

---

## The Core Narrative

Every post, everywhere, tells the same story with angle adjustments per audience:

> Your AI conversations are scattered across ChatGPT, Claude, and Gemini.
> I built a local app that brings them all into one place — searchable,
> browsable, with provenance. No cloud. No accounts. Everything stays
> on your machine.

This is the hook. Everything else is detail.

---

## Pre-Launch Checklist

Complete ALL of these before posting anywhere:

- [ ] **README is tight** — badges, screenshot, 60-second quick start
- [ ] **One real screenshot** — workspace with real imported data (not sample fixtures)
- [ ] **Second screenshot** — transcript explorer showing a real conversation
- [ ] **Third screenshot** — the "Wrapped" summary page (when ready) or federated view
- [ ] **Landing page is live** — deploy `landing/` to GitHub Pages or Netlify
- [ ] **GitHub release tag** — `v0.1.0` with a proper release description
- [ ] **Broken links fixed** — ROADMAP dead refs, double `.md.md` extension in archive
- [ ] **Requirements cleaned** — no phantom `chromadb`/`sentence-transformers`
- [ ] **CI badge is green** on main
- [ ] **Quick start actually works** — fresh clone, install, run, import in < 2 minutes
- [ ] **Landing page matches brand** — USB Drive palette, green accent

---

## Platform Strategy Overview

| Platform | Audience Size | Audience Fit | Timing | Priority |
|----------|--------------|-------------|--------|----------|
| r/ChatGPT | ~5M | ★★★★★ | Day 1 | Primary |
| r/ClaudeAI | ~200K | ★★★★★ | Day 1 | Primary |
| X (Twitter) | Varies | ★★★★ | Day 1 | Primary |
| r/LocalLLaMA | ~400K | ★★★★ | Day 2 | Primary |
| r/selfhosted | ~450K | ★★★★ | Day 2 | Primary |
| Hacker News | ~1M+ | ★★★★★ | Day 3-4 | High |
| r/SideProject | ~200K | ★★★ | Day 2 | Secondary |
| r/Python | ~1.5M | ★★★ | Day 3 | Secondary |
| r/artificial | ~600K | ★★★ | Day 3 | Secondary |
| r/datahoarder | ~500K | ★★★ | Day 4 | Secondary |
| r/productivity | ~2M | ★★ | Day 5 | Tertiary |
| Product Hunt | ~1M | ★★★★ | Week 2+ | Later |
| IndieHackers | ~100K | ★★★★ | Day 5 | Secondary |
| Dev.to | ~1M | ★★★ | Week 2 | Secondary |

**Timing rule:** Post Tuesday–Thursday, 9–11am EST for Reddit. Post Saturday/Sunday morning EST for Hacker News (less competition). Stagger across 3–5 days. Never blast everything at once.

---

## Reddit Posts

### r/ChatGPT — THE PRIMARY LAUNCH POST

**Why first:** Largest AI-specific audience. Every subscriber has ChatGPT exports. This is your most natural user base.

**Title:**
```
I built a local app that makes your ChatGPT export actually useful — browse, search, and discover themes across your full conversation history [open source]
```

**Body:**
```
I've been using ChatGPT daily for over a year. I finally downloaded my data
export and... it's a zip file with JSON. Not exactly browsable.

So I built SoulPrint — a local-first app that imports your ChatGPT conversations
into a real, searchable archive on your machine.

What it does:
• Import your ChatGPT .zip export (auto-detected, takes seconds)
• Browse conversations with full threading and a prompt-level table of contents
• Search across your entire history
• Ask questions that get answered from YOUR conversations, with citations
• Discover topics and themes across hundreds of conversations
• Export a verified "Memory Passport" you can validate and take anywhere

It also imports from Claude and Gemini, so if you use multiple AI tools,
everything ends up in one local archive.

Everything runs locally. No cloud. No accounts. No data leaves your machine.
SQLite database that you own. Apache-2.0 licensed.

Tech: Python/Flask, SQLite. 41 test files. BYOK for intelligence features
(use your own OpenAI or Anthropic API key for summaries and answering).

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

[Screenshot: workspace with imported ChatGPT conversations]
[Screenshot: transcript explorer showing a real conversation]

Would love feedback — especially from people who've been frustrated by
the ChatGPT export format. What would make this more useful for you?
```

**Post flair:** Use "Other" or "Tools" if available.

---

### r/ClaudeAI — CROSS-PROVIDER ANGLE

**Title:**
```
I built a local memory system that brings your Claude, ChatGPT, and Gemini conversations into one searchable archive [open source]
```

**Body:**
```
If you're like me, you have meaningful conversations scattered across Claude,
ChatGPT, and Gemini. Each platform has its own export format. None of them
talk to each other.

SoulPrint is a local app that imports all three into one canonical archive:

• Auto-detects provider from the export file (drop a .json or .zip)
• Normalizes everything into one local SQLite ledger
• Browse with full transcript explorer — prompt-level TOC, minimap
• Search across ALL providers at once
• Ask grounded questions from your conversation record (with citations)
• Discover themes, topics, and patterns across your full AI history
• Export a verified Memory Passport with provenance

The philosophy: your AI memory should be yours. Locally stored, searchable,
portable, with every answer traceable back to the source conversation.

No cloud. No accounts. No data ever leaves your machine. Apache-2.0.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

[Screenshot: federated view showing Claude + ChatGPT conversations together]

I use Claude as my primary AI tool, so the Claude importer was built with
real exports and has solid test coverage. Happy to answer questions about
how it handles Claude's export format.
```

---

### r/LocalLLaMA — ARCHITECTURE-FORWARD

**Title:**
```
SoulPrint: local-first AI conversation archive — SQLite canonical ledger, multi-provider import, grounded retrieval, no cloud [open source, Python]
```

**Body:**
```
Sharing a project I've been building: a local-first system for importing,
normalizing, and retrieving AI conversation history across providers.

Architecture:
- Layer A (Truth): SQLite canonical ledger with explicit native/imported
  lanes, stable IDs, timestamps, and source provenance
- Layer B (Legibility): Read-only browsing, search, transcript explorer,
  federated cross-lane retrieval
- Layer C (Intelligence): BYOK summaries, topic detection, digests,
  continuity packets — all derived, all traceable back to canonical IDs
- Layer D (Distribution): Web app, CLI tools, Memory Passport export

Current providers: ChatGPT, Claude, Gemini. Adding a provider is bounded
work: implement the ConversationImporter protocol, add a detector, fixture,
and tests. Registry handles auto-detection.

Key engineering choices:
- No vector database. Full-text retrieval over canonical records.
- Grounded answering returns "insufficient_evidence" rather than
  hallucinating when the ledger can't support an answer.
- Every derived artifact (summary, trace, passport entry) stores source
  conversation IDs, generation timestamp, LLM provider, and template version.
- Answer traces are append-only JSONL, always labeled "derived/non-canonical."
- 41 test files, 365 test methods. CI on every push.

Not using: LangChain, LlamaIndex, vector DBs, agent frameworks, or
cloud infrastructure. The entire system is Flask + SQLite + plain Python.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

Next steps: desktop wrapper (PyWebView initially), then a shareable
"AI Memory Wrapped" summary page as a growth hook.

Happy to go deep on any architectural decisions.
```

---

### r/selfhosted — DATA SOVEREIGNTY ANGLE

**Title:**
```
SoulPrint — self-hosted AI conversation archive: import from ChatGPT/Claude/Gemini, search across everything, export verified passports [Apache-2.0]
```

**Body:**
```
I built this because I wanted actual ownership over my AI conversation history.

SoulPrint runs entirely on your machine. Flask + SQLite. No phone-home,
no analytics, no cloud dependency.

What it does:
- Import your ChatGPT, Claude, and Gemini exports (auto-detected)
- Canonical SQLite ledger — one file, fully portable
- 10 web surfaces: workspace, import, browse, search, ask, discover, export
- Memory Passport: export your archive with manifest, provenance, and checksums
- Validate any exported passport against the canonical record
- Grounded answering with citation trails

What it doesn't do:
- No hosted anything. No accounts. No login.
- No phoning home. No telemetry.
- No cloud sync (by design — this is local-first)

Intelligence features (summaries, topics, digests, answering) are BYOK —
bring your own OpenAI or Anthropic API key. Without a key, import/browse/
search/export all work fully. The intelligence layer is an optional upgrade.

Tech: Python 3.12, Flask, SQLAlchemy, SQLite. Apache-2.0.
Test suite: 41 files, 365 methods. CI with GitHub Actions.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

Setup is: clone, pip install, run. Database lives in instance/soulprint.db.
No Docker yet but the dependency footprint is tiny (Flask + SQLAlchemy for
minimal mode).

Interested in feedback from the selfhosted community — especially on what
you'd want from the export/validation system.
```

---

### r/SideProject — BUILDER'S JOURNEY

**Title:**
```
I built SoulPrint — a local-first app that imports your AI conversations from ChatGPT, Claude, and Gemini into one searchable archive
```

**Body:**
```
Been building this for a few months. Sharing because it's finally at the
point where I think other people would find it useful.

The problem: I use ChatGPT, Claude, and Gemini regularly. My conversation
history — research, decisions, creative work — is scattered across three
platforms that don't talk to each other. Their exports are barely usable.

The solution: SoulPrint imports from all three, normalizes everything into
a local SQLite archive, and gives you real tools to browse, search, ask
questions from, and export your full AI history.

What makes it different:
- Local-first: everything stays on your machine, always
- Multi-provider: one unified view, but provenance is always explicit
- Intelligence: topic detection, summaries, grounded answering (BYOK)
- Memory Passport: verifiable export with provenance and checksums
- Answer audit: every generated answer has a trace back to source records

Current state:
- 3 provider importers (auto-detected)
- 10 web surfaces
- 41 test files, 365 test methods
- Full CLI toolkit for import, query, search, answer, export, validate
- Landing page: [link]
- Apache-2.0 licensed

Tech: Python, Flask, SQLite. No frameworks beyond Flask. No vector DBs.
No cloud infrastructure. Intentionally simple stack.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

[Screenshot: workspace]
[Screenshot: transcript explorer]

Next steps: desktop wrapper, freemium gate, and a "Wrapped" summary
page (think Spotify Wrapped for your AI history — the growth hook).

Feedback welcome — especially on what features would make you want to
actually use this daily.
```

---

### r/Python — TECHNICAL CRAFT

**Title:**
```
SoulPrint: a Flask+SQLite app for importing and searching AI conversations across providers — 41 test files, clean architecture, open source
```

**Body:**
```
Sharing a Python project I've been building: a local-first AI conversation
archive with multi-provider import, federated retrieval, and a clean
four-layer architecture.

Technical highlights:

**Importer contract pattern:**
Each provider (ChatGPT, Claude, Gemini) implements a `ConversationImporter`
protocol. Auto-detection happens through `looks_like_*` detector functions
registered in a central registry. Adding a new provider is: adapter +
detector + fixture + tests. The registry handles everything else.

**Lane-aware retrieval:**
Native and imported records stay in explicit lanes. Federated search
composes them read-only without merging. Every result carries its lane,
source, and stable ID.

**Grounded answering:**
Questions are reduced to compact lexical terms, searched across federated
lanes, and answered with explicit citations. The system returns
`insufficient_evidence` rather than guessing.

**Answer traces:**
Every generated answer writes an append-only JSONL trace with question,
retrieval terms, status, citations, and fallback notes. Auditable.

**Testing:**
41 test files, 365 test methods. Covers parsing, persistence, CLI,
browser integration, citation handoff, continuity, and passport validation.
CI runs on every push.

Stack: Python 3.12, Flask, SQLAlchemy, SQLite. Minimal dependencies
(flask + flask-sqlalchemy for core). Optional: openai/anthropic for
intelligence features.

Architecture:
```
Truth (SQLite) → Legibility (browse/search) → Intelligence (derived) → Distribution
```

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

Happy to discuss the architecture or any specific implementation decisions.
```

---

### r/datahoarder — PRESERVATION ANGLE

**Title:**
```
Archive your AI conversations locally with full provenance — imports from ChatGPT, Claude, and Gemini into a verified, exportable SQLite ledger
```

**Body:**
```
I've been archiving my AI conversations and wanted something better than
raw JSON exports sitting on disk.

SoulPrint imports conversations from ChatGPT (.zip), Claude (.json), and
Gemini (Takeout) into a canonical SQLite ledger with:

- Stable IDs and timestamps for every record
- Explicit source provenance (which provider, which conversation)
- Duplicate guards (same conversation won't import twice)
- Full-text search across all providers
- Memory Passport export: manifest + JSONL lanes + provenance index
- Passport validation: verify exports against the canonical contract

The archive is one SQLite file (instance/soulprint.db). Fully portable.
The Memory Passport export adds a structured layer with checksums and
provenance that you can validate independently.

Local-only. No cloud. No accounts. Apache-2.0.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical
```

---

### r/artificial — PRODUCT POSITIONING

**Title:**
```
SoulPrint: cross-provider AI conversation memory, locally owned — why nobody else is building this and why they should be
```

**Body:**
```
There's a gap in the AI tooling ecosystem that nobody is filling:

Mem0 is for developers. Rewind captures everything on your screen.
Obsidian is general knowledge management. Various "ChatGPT viewers" handle
one provider and stop there.

Nobody is building: multi-provider AI conversation memory, with intelligence,
provenance, and exportability, as a local-first product for end users.

That's SoulPrint. It imports from ChatGPT, Claude, and Gemini. It normalizes
everything into a canonical local ledger. It lets you browse, search, discover
themes, ask grounded questions, and export a verified Memory Passport.

The thesis: as people build meaningful context across multiple AI assistants,
the fragmentation problem gets worse. Every provider wants to keep your
history locked in. SoulPrint is the tool that says "this is YOUR memory."

Current state: 3 providers, 10 surfaces, 41 test files, full CLI, canonical
ledger with provenance. Open source, Apache-2.0.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

Interested in discussion about:
- Is AI conversation memory a real product category?
- What other providers would be most valuable to support?
- Does anyone else feel the fragmentation problem?
```

---

## X (Twitter) Thread

Post as a thread. Include screenshots. Pin to profile.

### Tweet 1 — Hook
```
Your AI conversations are scattered across ChatGPT, Claude, and Gemini.

None of them talk to each other. The exports are barely usable.

I built SoulPrint — a local app that brings your full AI history into
one searchable, browsable archive.

No cloud. No accounts. Your data stays on your machine.

🧵👇

[Screenshot: workspace with real data]
```

### Tweet 2 — What it does
```
What SoulPrint does:

→ Import from ChatGPT, Claude, Gemini (auto-detected)
→ Browse conversations with full threading + TOC
→ Search across all providers at once
→ Ask questions grounded in YOUR conversations
→ Discover themes and patterns across your history
→ Export a verified Memory Passport

Python + SQLite. Apache-2.0.
```

### Tweet 3 — Differentiator
```
What SoulPrint is NOT:

— Not a hosted SaaS (nothing leaves your machine)
— Not a mem0 clone (built for users, not developers)
— Not an AI dashboard (no metrics theater)
— Not a single-provider viewer (3 providers and growing)

It's specifically: your AI memory, locally owned, intelligently
organized, and provably yours.
```

### Tweet 4 — Architecture (for the devs)
```
Architecture for the curious:

Layer A: Canonical SQLite ledger — explicit lanes, stable IDs
Layer B: Read-only browsing, search, inspection
Layer C: Derived intelligence — summaries, topics, grounded answering
Layer D: Distribution — web app, CLI, passport export

Every derived artifact traces back to canonical records.
41 test files. CI on every push.
```

### Tweet 5 — CTA
```
SoulPrint is open source and free to use.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical

If you've ever wished you could search across all your AI
conversations in one place — this is it.

Star it. Clone it. Break it. Tell me what's missing.
```

### Standalone tweet for later (quote-tweet bait):
```
Hot take: your AI conversation history is more valuable than your
search history ever was, and right now it's locked inside 3+ platforms
that don't talk to each other.

I'm building SoulPrint to fix that. Local-first. Open source.

https://github.com/Celestialchris/SoulPrint-Canonical
```

---

## Hacker News

### Show HN Post

**Title:**
```
Show HN: SoulPrint – Local-first archive for ChatGPT/Claude/Gemini conversations
```

**Body:**
```
SoulPrint imports your AI conversation exports from ChatGPT, Claude, and
Gemini into a canonical local SQLite ledger. Browse, search, discover themes,
ask grounded questions with citation trails, and export a verified Memory
Passport. Everything runs on your machine. No cloud. No accounts.

Architecture: four layers — canonical truth (SQLite), read-only legibility
(browse/search), derived intelligence (BYOK summaries/topics/answering),
and distribution. Every derived output traces back to stable IDs.

Python 3.12, Flask, SQLAlchemy, SQLite. 41 test files. Apache-2.0.
Intelligence features use your own OpenAI or Anthropic key.

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical
```

**HN rules:**
- Post Saturday or Sunday morning EST (less competition in Show HN)
- Be in the comments answering every question, especially architectural ones
- If someone compares to mem0: "mem0 is developer infrastructure; SoulPrint is an end-user product. Different audience, different trust model."
- If someone asks about vector DBs: "Intentionally not using them. Full-text retrieval over canonical records is simpler, faster, and doesn't require a separate index. The architecture supports adding vector search as an optional layer later without replacing the canonical ledger."
- Never ask for upvotes. Ever.
- If it doesn't land, wait 2-3 weeks and try again with a different angle

---

## Product Hunt (Week 2+, after desktop wrapper)

**Tagline:**
```
SoulPrint — Your AI conversations, brought home
```

**Description:**
```
Your AI history is scattered across ChatGPT, Claude, and Gemini.
SoulPrint brings it all into one local archive.

Import → Browse → Search → Ask → Discover → Export

Local-first. No cloud. No accounts. Yours.
```

**Maker comment:**
```
I built SoulPrint because my AI conversation history — research,
decisions, creative work — was scattered across three platforms that
don't talk to each other.

SoulPrint imports from ChatGPT, Claude, and Gemini, normalizes
everything into a local SQLite ledger, and gives you real tools:
browsing, search, grounded answering, topic discovery, and a verified
Memory Passport you can export and validate.

Everything runs on your machine. The canonical ledger is yours.

I'd love feedback, especially on:
- What other AI providers should I support next?
- Would you actually use the Memory Passport export?
- What would make you use this daily?
```

**PH timing:** Tuesday morning is traditionally best. Hunter welcome but not required.

---

## IndieHackers Post

**Title:**
```
Building SoulPrint — a local-first app for AI conversation memory
```

**Body:**
```
I've been building SoulPrint for the past few months. It's a local-first
app that imports your AI conversation history from ChatGPT, Claude, and
Gemini into one searchable, browsable archive.

The thesis: as AI becomes part of daily work, conversation history becomes
valuable. But it's fragmented across providers. Nobody is building a tool
to bring it together locally, with provenance and real intelligence.

Current state:
- 3 provider importers
- 10 web surfaces (browse, search, ask, discover, export)
- 41 test files
- Full CLI toolkit
- Memory Passport export with validation

Monetization plan:
- Free: import, browse, search, export, passport, traces
- Paid ($9/mo or $49 lifetime): Ask, Intelligence layer
- Local license key validation (no accounts, no server auth)
- Growth hook: "AI Memory Wrapped" — shareable summary page

Tech: Python, Flask, SQLite. Intentionally simple. No cloud infrastructure.

What I'd love feedback on:
1. Is "AI conversation memory" a real product category?
2. Does $9/mo or $49 lifetime feel right for the paid tier?
3. What features would make you switch from raw exports?

GitHub: https://github.com/Celestialchris/SoulPrint-Canonical
```

---

## Dev.to / Hashnode Blog Post (Week 2)

**Title:**
```
How I Built a Cross-Provider AI Conversation Archive with Python and SQLite
```

**Outline:**
1. The problem: fragmented AI history across 3+ providers
2. Architecture: four-layer model (truth → legibility → intelligence → distribution)
3. The importer contract pattern (how to make providers pluggable)
4. Lane-aware retrieval (why you don't want to merge imported + native)
5. Grounded answering (why `insufficient_evidence` is better than hallucinating)
6. Memory Passport (what a portable, verifiable AI conversation export looks like)
7. What's next: desktop wrapper, freemium, the "Wrapped" growth hook
8. Lessons learned: keep the stack simple, test everything, ship the spine first

This post is for technical credibility and SEO. Link back to GitHub. Include code snippets from the importer contract and retrieval layer.

---

## Engagement Playbook (Post-Launch)

### Day 1-3: Active response
- Answer EVERY comment on every platform. Be generous with technical detail.
- Thank people who star the repo. Follow back people who engage substantively.
- If someone finds a bug, fix it fast and reply with the commit.

### Day 4-7: Follow-up content
- Post a "thank you + what I learned" follow-up on r/SideProject
- Tweet individual feature highlights (one per day) with screenshots
- If any post got significant traction, write a short retrospective

### Week 2: Sustained presence
- Dev.to/Hashnode technical deep-dive article
- Product Hunt launch (if desktop wrapper is ready)
- Continue engaging in AI subreddits when "conversation history" or "AI memory" comes up

### Ongoing: Organic engagement
- Quote-tweet anyone complaining about ChatGPT/Claude exports
- Reply in threads about "AI memory" with a genuine one-liner
- Share feature updates as they ship (new providers, Wrapped page, etc.)
- Build a changelog thread on X that you update with each release

---

## Key Messaging Do's and Don'ts

### DO:
- Lead with the human problem ("scattered across three platforms")
- Include screenshots — they're worth more than any text
- Be specific about what it does (not vague "AI memory management")
- Mention the test count (signals engineering quality)
- Say "local-first" and "no cloud" — these are genuine differentiators
- End with a question that invites engagement
- Be honest about what's planned vs. what's shipped

### DON'T:
- Use the word "revolutionary" or "game-changing"
- Mention mem0 unprompted (let others make the comparison)
- Oversell intelligence features before someone has configured an API key
- Post the same text across multiple subreddits (each gets a tailored angle)
- Edit in product links after a post gets traction (Reddit hates this)
- Mention pricing in launch posts (this is about the product, not the business)
- Use "AI" as an adjective more than twice per post
- Mention the Archetype/SoulPrint mythology (that's inner product, not public face)

---

## Screenshot Shot List

Capture these with real imported data before posting anywhere:

1. **Workspace** — dashboard with provider coverage, recent conversations, counts
2. **Transcript explorer** — a real ChatGPT conversation with TOC and minimap
3. **Federated view** — mixed results from ChatGPT + Claude showing provenance
4. **Import page** — showing the drag-and-drop or file selection interface
5. **Answer trace** — a grounded answer with citations linked to source conversations
6. **Memory Passport** — the export/validate surface
7. **Wrapped summary** (when ready) — the dark premium shareable page

Use real conversations. Redact anything sensitive. Screenshots with real data are 10x more compelling than empty-state screenshots.

---

## Timeline

```
Day -3 to -1:  Repo cleanup, screenshots, landing page live, v0.1.0 tagged
Day 0:         r/ChatGPT + r/ClaudeAI + X thread (morning EST)
Day 1:         r/LocalLLaMA + r/selfhosted + r/SideProject
Day 2:         r/Python + r/artificial
Day 3-4:       Hacker News (weekend morning)
Day 4-5:       r/datahoarder + r/productivity + IndieHackers
Week 2:        Dev.to article + Product Hunt (if desktop ready)
```

---

*The product is real. The architecture is clean. The story is clear.*
*Now ship the face and tell the world.*
