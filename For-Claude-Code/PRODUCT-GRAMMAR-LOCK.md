# SoulPrint 0.1 — Product Grammar Lock

*Locked language system for the app, landing page, and launch materials.*
*Implementation-ready. No strategy essays.*

---

## The Two-Layer Promise

SoulPrint v0.1 has two user hooks, and the product grammar must carry both.

**Layer 1 — The archive hook (gets people in the door):**
> Your AI conversations are scattered everywhere. SoulPrint brings them home.

This is the launch message. It describes a pain that every ChatGPT/Claude/Gemini user has felt. It matches the v0.1 free tier: import, browse, search, export. No configuration needed. Immediate payoff.

**Layer 2 — The continuation hook (keeps them, differentiates):**
> Never start from scratch with AI again.

This is the power message. It describes what SoulPrint does that nobody else does: generate continuity packets from old conversations and hand them off into new ones. It matches the BYOK intelligence tier. It's the upgrade path and the long-term identity.

**Rule:** Layer 1 leads in launch posts, the README tagline, the landing page hero, and any context where someone hasn't heard of SoulPrint before. Layer 2 leads inside the app (workspace CTA after import, continuity surfaces, upgrade prompt) and in contexts where the user already has data imported.

You don't have to choose. You need both. The archive hook is the top of the funnel. The continuation hook is the retention engine.

---

## Locked One-Line Promise

**Public-facing (README, landing hero, launch posts):**
> Your AI conversations are scattered everywhere. SoulPrint brings them home.

**In-app (workspace, continuity, upgrade prompt):**
> Never start from scratch with AI again.

**When both are needed (landing page below the fold, Product Hunt, longer posts):**
> Your AI conversations are scattered across ChatGPT, Claude, and Gemini.
> SoulPrint brings them into one local archive — searchable, browsable, and ready to continue.

---

## Locked Nav Labels

These are the user-facing labels. Routes are unchanged.

| Route | Nav Label | Page Heading | Notes |
|-------|-----------|--------------|-------|
| `/` | Workspace | Workspace | Unchanged |
| `/import` | Import | Bring conversations home | Warmer page heading |
| `/imported` | What you've discussed | What you've discussed | Unchanged from brand.md |
| `/imported/<id>/explorer` | — | *(conversation title)* | No nav entry; page heading is the conversation title |
| `/chats` | Your own notes | Your own notes | Unchanged from brand.md |
| `/federated` | Everything, together | Everything, together | Unchanged from brand.md |
| `/ask` | Ask your memory | Ask your memory | Slightly warmer than bare "Ask" |
| `/intelligence` | Themes & patterns | Themes & patterns | Unchanged from brand.md |
| `/answer-traces` | How answers were found | How answers were found | Unchanged from brand.md |
| `/passport` | Take it with you | Take it with you | Unchanged from brand.md |
| `/summary` | Your summary | *(standalone page, no nav)* | Always dark. The wow moment. |

**Nav grouping** (frozen in DECISIONS.md, reproduced here for reference):
- **Sanctum:** Workspace, Ask your memory
- **Memory:** What you've discussed, Your own notes, Everything together
- **Interpretation:** Themes & patterns, How answers were found
- **Continuity:** Import, Take it with you

**Change from brand.md:** "Ask" → "Ask your memory" and "Import" page heading → "Bring conversations home." Everything else is unchanged. The group labels (Sanctum, Memory, Interpretation, Continuity) are internal nav section headers, not clickable items.

---

## Locked CTA Labels

CTAs appear in specific contexts. Each one has exactly one job.

| Context | CTA Text | Action | Tier |
|---------|----------|--------|------|
| Workspace, no data | Import your first conversation | → `/import` | Free |
| Workspace, has data | Continue a conversation | → most recent conversation's continuity view | Pro (graceful gate) |
| Workspace, has data (secondary) | Browse your history | → `/imported` | Free |
| Import page, success (first import) | See your summary | → `/summary` | Free |
| Import page, success (incremental) | See your updated summary → | → `/summary` | Free |
| Transcript explorer | Continue this thread | → continuity packet generation | Pro (graceful gate) |
| Continuity packet view | Copy handoff to clipboard | → clipboard | Pro |
| Upgrade prompt | Go deeper | → `upgrade.html` | Gate |
| Landing page hero | Download | → GitHub release | Free |
| Landing page hero (secondary) | View on GitHub | → repo | Free |

**"Continue" appears as an action, not a nav item.** It shows up at the moments where it's the natural next step — after browsing a conversation, after importing data, on the workspace when you have history. It doesn't replace "Import" or "Browse" as the primary first-time action.

---

## Allowed / Disallowed User-Facing Terms

### Use these:
| Term | When |
|------|------|
| conversations | Always. This is what users imported. |
| your memory | When referring to the full archive. "Ask your memory." |
| continue | As an action. "Continue this thread." "Continue a conversation." |
| bring home / brought home | The import action. "Bring conversations home." |
| themes, patterns | For intelligence layer. Not "topics" in the UI (too generic). |
| handoff | For continuity packets. "Copy handoff to clipboard." |
| provenance | In architecture contexts (README, docs). Not in the app UI. |
| local | When distinguishing from cloud. "Everything stays local." |
| your machine | More concrete than "local." "Nothing leaves your machine." |
| traces | For answer audit. Keep it. Users who find this surface want precision. |

### Do not use in user-facing text:
| Term | Why | Replace with |
|------|-----|--------------|
| canonical | Architecture jargon | "your record" or "your archive" |
| ledger | Architecture jargon | "your archive" or "your conversations" |
| lanes | Architecture jargon | "providers" or just omit |
| federated | Architecture jargon | "everything, together" (the nav label handles it) |
| derived | Architecture jargon | "generated" or "discovered" |
| normalization | Architecture jargon | just omit — users don't care how import works |
| grounded | Architecture jargon | "from your conversations" or "with citations" |
| BYOK | Architecture jargon | "your own API key" |
| stable IDs | Architecture jargon | just omit |
| artifacts | Internal term | "packets" or "summaries" depending on context |
| intelligence layer | Internal term | "Themes & patterns" |
| provenance | In the app UI | "source" — "From your ChatGPT conversation on March 3" |

**Exception:** README, CLAUDE.md, CONTRIBUTING.md, architecture docs, and the Hacker News / r/LocalLLaMA posts can and should use the precise terms. The disallowed list applies only to the app UI and user-facing landing page.

---

## Summary/Wrapped Page Language

The `/summary` page is always dark, standalone, no nav. Its language is cinematic, not warm.

- Hero: "SoulPrint" wordmark with glow → "Your AI Memory" → date range
- Headline stat: the total message count, massive. Label: "messages with AI"
- Sections use uppercase JetBrains Mono labels: PROVIDERS, THEMES DISCOVERED, LEFT OPEN
- Watermark: "Generated by SoulPrint" + "soulprint.dev"
- Footer: "Screenshot this page to share your AI memory summary"

No warm nav labels here. No "What you've discussed." This page speaks in its own register — quiet, premium, cinematic. It earns the glow.

---

## What This Language Lock Changes From Current State

1. **Import page heading:** "Import" → "Bring conversations home"
2. **Ask nav label:** "Ask" → "Ask your memory"
3. **Workspace primary CTA (when data exists):** Add "Continue a conversation" as the main action
4. **Transcript explorer:** Add "Continue this thread" CTA pointing to continuity
5. **Landing page hero subtext:** Consider adding "Never start from scratch with AI again" below the fold
6. **Upgrade prompt CTA:** "Go deeper" (already frozen in DECISIONS.md)

Everything else in brand.md and the current nav labels stays as-is.

---

## Recommended Next Frontend Phase

With language locked, the frontend work is:

1. **CSS Alignment (Task 1 from execution plan)** — app matches Torchlit Vault. Highest impact. Do this first.
2. **Apply language changes** — update the 5 specific text changes listed above in templates. Small PR.
3. **Wrapped summary page (Task 3)** — the growth hook and screenshot moment.
4. **Freemium gate (Task 4)** — "Go deeper" upgrade prompt, license key.

Do not redesign the nav structure, the information architecture, or the route layout. The current 14 surfaces are correct. The work is making them speak in one voice and look like one product.

---

*The archive hook gets them in. The continuation hook keeps them.*
*Both are true. Both are the product. Lead with what the audience already feels.*
