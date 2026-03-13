# SoulPrint — Product Vision: Next 30 Days

*From working prototype to shippable product.*

---

## Where We Are (March 13, 2026)

SoulPrint is a functional local-first memory continuity system with:

- 216 passing tests
- 3 provider importers (ChatGPT, Claude, Gemini) with auto-detection
- 9 web surfaces (Workspace, Import, Ask, Notes, Passport, Imported, Federated, Native Memory, Answer Traces)
- Intelligence layer: per-conversation summaries, cross-conversation topic detection, digest synthesis
- Memory Passport export + validation
- Grounded answering with citation handoff and trace audit
- CSS restyle with warm parchment palette, frosted nav, card system
- Two-layer doctrine: product/architecture (Layer 1) + visual direction (Layer 2)
- Clean repo: LICENSE, CI, CONTRIBUTING, ROADMAP, CHANGELOG, stratified docs

**What's missing is not capability. It's packaging, identity, and a path to users.**

---

## The 30-Day Goal

By mid-April 2026, SoulPrint should be:

1. **Downloadable** — a desktop app someone installs in 60 seconds
2. **Beautiful** — every surface polished to the point of being screenshot-worthy
3. **Discoverable** — a landing page that communicates the product in 10 seconds
4. **Monetizable** — a freemium gate that feels fair and natural
5. **Shareable** — at least one "wow" moment that generates organic screenshots

---

## Product Identity

### Mission
Every person should own their AI memory.

### One-liner
Your AI conversations are scattered everywhere. SoulPrint brings them home.

### What SoulPrint Is
A local-first memory continuity system. Import your AI conversation history from ChatGPT, Claude, and Gemini. Browse it, search it, ask questions from it, discover themes across it, and export it as a verifiable Memory Passport. Everything stays on your machine. Nothing is hosted. The canonical local ledger is yours.

### What SoulPrint Is Not
- Not a hosted SaaS (your data never leaves your machine)
- Not a mem0 clone (SoulPrint is user-facing, not developer infrastructure)
- Not an AI dashboard (no metrics theater, no admin-panel energy)
- Not a generic wrapper (SoulPrint has its own canonical ledger and trust chain)

### Differentiator
Nobody else is building cross-provider AI conversation memory with provenance, intelligence, and exportability as a local-first product. Mem0 serves developers. Rewind captures everything. Obsidian is general knowledge management. SoulPrint is specifically: **your AI memory, locally owned, intelligently organized, and provably yours.**

---

## Architecture (unchanged — this is the spine)

```
Layer A — Truth        → Canonical SQLite ledger. Explicit lanes. Stable provenance.
Layer B — Legibility   → Browse, search, inspect, trace, export. Read-only over truth.
Layer C — Intelligence → Summaries, topics, digests. All derived. All provenance-bound.
Layer D — Distribution → Desktop app, landing page, installer, freemium gate.
```

Build sequence: truth → legibility → intelligence → distribution.
We are now entering Layer D.

---

## Week 1: Brand & Landing Page (March 14-20)

### Brand Identity
- Logo: fingerprint-inspired mark (the "soul" in SoulPrint)
- Primary palette: warm parchment (#f2f0e9), accent blue-grey (#3f5f73), surface white (rgba(255,253,248,0.94))
- Typography: system stack (-apple-system, SF Pro) for the app; one distinctive display font for the landing page
- Visual DNA: calm, warm, trustworthy, local-first, not-corporate

### Landing Page
- Static site (GitHub Pages or Netlify — zero server costs)
- Hero: tagline + one hero screenshot of workspace with real data
- Product loop visual: Import → Browse → Search → Ask → Discover → Export
- "What it's not" section (own the positioning)
- Social proof placeholder (GitHub stars, test count, provider count)
- Email signup for launch (Buttondown free tier)
- Download CTA (initially links to GitHub release)
- Footer: Apache-2.0, GitHub link, "Built with local-first principles"

### Deliverables
- `landing/` folder in repo with static HTML/CSS
- Logo as SVG in `landing/assets/`
- `BRAND.md` in docs/product/ formalizing palette, typography, voice

---

## Week 2: Desktop App & Real Data (March 21-27)

### Desktop Packaging
- PyWebView wrapper first (fastest path to "double-click to open")
- Window title: "SoulPrint — Your AI Memory"
- First-run onboarding: "Welcome to SoulPrint. Drop your first export here."
- Clean shutdown on window close
- Tauri exploration begins in parallel (for eventual proper installer)

### Real Data Testing
- Import your actual ChatGPT export (the real zip from OpenAI)
- Import your actual Claude export
- Import your actual Gemini Takeout
- See every surface with real data — fix anything that breaks or looks wrong
- Take screenshots of every surface with real data for the landing page

### Deliverables
- `desktop/launcher.py` working on Windows
- `requirements-desktop.txt`
- Screenshots folder for landing page
- Bug fixes from real-data testing

---

## Week 3: Freemium Gate & Polish (March 28 - April 3)

### Monetization Model

**Free tier (the hook — no friction):**
- All imports: ChatGPT, Claude, Gemini (and future providers)
- Full browsing: workspace, imported list, transcript explorer, federated search
- Full export: Memory Passport export + validation
- Native memory
- Answer traces

**Paid tier ($9/month or $49/lifetime — test both):**
- Intelligence layer: summaries, topic threads, digests
- In-app Ask (grounded answering)
- Priority support
- Future providers as they're added

**Implementation:**
- License key validation (simple local check, no server auth)
- Sell through LemonSqueezy or Gumroad
- "Upgrade" prompt when free user tries Ask or Notes
- 7-day free trial of paid features on first install

### UI Polish Pass
- Every surface reviewed with real data at 1200px, 768px, 480px
- Empty states refined (especially Notes when LLM not configured)
- Loading states for import and ask operations
- Error messages humanized (no stack traces)
- Nav consolidation: consider grouping (Import + Imported = one surface)

### Deliverables
- License gate implementation
- LemonSqueezy/Gumroad product page
- Polished screenshots for landing page update

---

## Week 4: Growth Hook & Soft Launch (April 4-10)

### The "Wrapped" Moment
- `/summary` route: beautiful one-page visual summary of your AI memory
- Total conversations, provider breakdown, timeline, most-discussed topics
- "Generated by SoulPrint" watermark
- Share button (download as image or copy link)
- This is the screenshot moment. This is what goes on Twitter/Reddit.

### Soft Launch
- GitHub release with version tag (v0.1.0)
- Landing page live with download link
- Post on: r/ChatGPT, r/ClaudeAI, r/LocalLLaMA, r/selfhosted, Hacker News
- Simple message: "I built a local app that imports your ChatGPT/Claude/Gemini history and lets you browse, search, and discover themes across all of them. No cloud. No accounts. Your data stays on your machine."
- Email signup list notified

### Deliverables
- v0.1.0 release on GitHub
- Landing page updated with real screenshots
- Social posts drafted
- Email announcement sent

---

## Future Provider Roadmap (post-launch)

### Near-term additions (April-May 2026)
- **Grok (xAI)** — Twitter/X users are a natural audience. Export format TBD (likely JSON via data export request).
- **Copilot (Microsoft)** — Takeout exports as JSON with conversationId/timestamp/userInput/botResponse structure. Large Windows user base.
- **Perplexity** — growing AI search tool. Export support unclear but worth tracking.

### Medium-term additions (Summer 2026)
- **Ollama / local model conversation logs** — for the self-hosted crowd. This audience overlaps heavily with SoulPrint's local-first values.
- **DeepSeek** — growing in popularity, especially in developer circles.
- **Mistral Le Chat** — European AI provider, aligns with data sovereignty narrative.

### Provider addition pattern (already established)
Every new provider follows the same contract:
1. Research actual export format (get a real fixture)
2. Write adapter implementing `ConversationImporter` protocol
3. Add `looks_like_*` detector function
4. Register in `registry.py` with auto-detection
5. Add fixture to `sample_data/`
6. Write tests (parser, persistence, CLI, browser integration)
7. Update README provider list

The architecture already supports unlimited providers. Adding one is a bounded, testable task — not a redesign.

---

## Revenue Projections (honest, conservative)

### Scenario: 1,000 downloads in first month
- 10% convert to paid = 100 paying users
- At $9/month = $900/month recurring
- At $49/lifetime = $4,900 one-time

### Scenario: 5,000 downloads in first 3 months
- 8% convert = 400 paying users
- At $9/month = $3,600/month recurring
- At $49/lifetime = $19,600 one-time

### Scenario: Hacker News front page
- 10,000-50,000 visits in 48 hours
- 5-10% download = 500-5,000 installs
- Conversion depends entirely on first-run experience quality

**The honest read:** revenue follows from product quality and distribution reach. The first $1,000/month is the hardest. After that, word of mouth and the "Wrapped" sharing mechanic can compound. The local-first angle is a genuine differentiator in a market full of SaaS products that want to hold your data hostage.

---

## Competitive Positioning Map

```
                    Developer-facing ←————————→ User-facing
                         |                          |
    Infrastructure       |   Mem0                   |
                         |   Zep                    |
                         |                          |
    Product              |                          |   SoulPrint ← YOU ARE HERE
                         |                          |   Rewind/Limitless
                         |                          |
    Toy/Demo             |   Various GitHub         |   ChatGPT export viewers
                         |   memory repos           |   (basic, single-provider)
                         |                          |
              Hosted ←———————————————————————→ Local-first
```

SoulPrint's unique position: **user-facing, local-first, multi-provider, with intelligence.** Nobody else occupies this square.

---

## The One Rule (still applies)

Every decision in the next 30 days must pass this test:

**Does this make someone want to download SoulPrint, try it once, and tell someone else about it?**

If not, it's not ready for this month.

---

## What Success Looks Like on April 13, 2026

- A person can go to soulprint.dev (or similar)
- Read one sentence and understand what it does
- Download a desktop app
- Drag in their ChatGPT export
- See their conversations beautifully organized in 30 seconds
- Discover themes they didn't know existed
- Screenshot their "AI Memory Wrapped" summary
- Post it on Twitter
- Their friend asks "what is this?"
- The cycle repeats.

That's the product. That's the month.
