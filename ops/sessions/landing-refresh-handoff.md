# Landing Page Refresh — Handoff

**Status:** Deferred until a real launch window is on the calendar. Not stalled; parked.
**Written:** 2026-04-23
**Reason for deferral:** The Phase 11 "soft launch" milestone in ROADMAP predates the MCA/Expansion/Companion plans and no longer reflects current priorities. Landing refresh was urgent only because launch was imminent. Launch isn't imminent. So the work waits.
**When to unpark:** When a launch date becomes real — Reddit drop, Hacker News Show HN, YouTube demo, paid product cut.

---

## What prompted this work

The current `landing/index.html` violates its own `CLAUDE.md` prohibitions (USB language appears in nine separate locations), the install command in the terminal demo is dead (`pip install -r requirements.txt` — that file was deleted), and provider coverage is three out of five (ChatGPT/Claude/Gemini only, missing Claude Code and Grok). Before launch, all three need fixing.

---

## Current state audit (from a full read of `landing/index.html` on 2026-04-23)

### Identity problems

The landing's visual identity is built on USB as a load-bearing metaphor, not just a tagline:

- `<title>` literally reads "SoulPrint — A virtual USB stick for your AI life."
- Hero visual is a 14-column CSS pixel-grid USB drive (HTML lines 159-174, CSS lines 44-49)
- Favicon and nav-brand SVG is a green USB stick (inlined line 146, file at `landing/assets/logo.svg`)
- Meta description: "A local-first desktop app that imports ChatGPT, Claude, and Gemini..."
- Bottom CTA heading: "Plug in and own it."
- Step 04 of "How it works" is titled "Take it with you."

CLAUDE.md line 66 explicitly prohibits this language. A retokening pass can't fix it. The hero needs a new visual concept.

### Token drift from Quiet Archive v3

All tokens on the landing belong to either Magenta Sanctum v2 or USB Drive era:

| Property | Current | Should be |
|---|---|---|
| Accent | `#4ade80` (green) | `#A25B47` (clay) |
| Surface | `#0e0f11` (cold near-black) | `#0F0D0B` (warm-black) |
| Typography | Outfit via Google Fonts CDN | Playfair Display + DM Sans, bundled local |
| Wordmark gold | absent | `#E7C98A` with Torchlight ember shadow |

Provider colors on the landing are also stale. PR #145 shifted Claude `#C69224` → `#D97757`, split Claude Code to `#F5C518`, and shifted Grok purple → `#8B3A3A`. Landing still uses the old palette.

### Copy corrections needed

- Every "ChatGPT, Claude, and Gemini" or "ChatGPT .zip, Claude .json, or Gemini Takeout" mention needs all five providers: ChatGPT, Claude, Claude Code, Gemini, Grok.
- Terminal demo (line 245): `pip install -r requirements.txt` → `pip install -e .` (or `pip install -e ".[intelligence]"` for full stack).
- Nav Download link: deployed `/releases` vs repo direct `.exe`. Different audience implications; pick one consciously.

### Em dashes

Every em dash in public copy needs to become a period, comma, or separate sentence. Em dashes read as AI-generated on public surfaces.

### What works and can stay

Section rhythm is sound: hero, providers, features, terminal demo, how-it-works (4 steps), Without/With comparison, bottom CTA, footer. Single static HTML file. Netlify serves directly, no build step. IntersectionObserver reveal animations are appropriate. Feature grid maps to real features (Import, Search, Browse, Ask, Discover themes, Export passport).

The Without/With difference table is the sharpest conceptual thing on the page. Structure survives any retokening.

---

## Framer template research (completed 2026-04-23)

The research phase closed before Phase 2 was deferred. Full contact sheet and deep-read exist for 25 templates across Template and Inspiration collections. Summary:

### Verdict on templates

No single Framer template imports cleanly. The AI-SaaS genre on Framer has converged on a narrow visual vocabulary (gradient mesh, purple-teal accent, glow effects, "AI-powered" badges) that is exactly what Quiet Archive v3 is reacting against. Retokening any of them to clay + warm-black strips the gradient, kills the glow, desaturates the accent, and leaves a skeleton you'd have to rebuild anyway.

### The four templates worth pattern-borrowing

- **Codexia** (Svaco) — editorial-illustration hero posture. The specific Japanese-garden illustration doesn't transfer, but the *approach* of using an editorial illustration instead of a product screenshot or gradient mesh is the single most distinctive pattern in the Framer set. Maps well to "lived-in personal archive" as a visual concept if a custom illustration gets commissioned.

- **Maximux** (Salim/Webestica) — bento feature grid. Three smaller tiles on top, two wider tiles on bottom. Creates visual hierarchy where uniform 3×2 grids create uniform weight. One of the bottom tiles in the source JPEG is a code snippet card, matching SoulPrint's existing terminal-demo section. The reference JPEG sits at `docs/screenshots/` under whatever filename it got saved as from the `Template-html.zip` upload.

- **Exact** (Arthur Duchesne) — section rhythm and dev-audience IA. Hero → logo/trust strip → core features → use cases → testimonials → pricing → FAQ. Explicit anchor IDs (`#core-features`, `#use-cases`, `#pricing`). The hero itself (full IDE mockup) doesn't transfer because SoulPrint is a web app, not an IDE, but the information architecture does.

- **Cadence** (Arthur Duchesne) — problem-framing section placement. "What's slowing you down?" block sits between hero and features. This is copywriting structure, not visual. SoulPrint's adaptation: "Your AI history is locked in five platforms. One update, your context is gone." The preservation narrative from the emotional-attachment audience frame.

### Synthesis: pattern-first, hand-coded

The recommended Phase 2 approach if it becomes active:

1. Hero in Codexia posture (editorial illustration, not product screenshot or gradient mesh). Commission a custom illustration in Quiet Archive palette — warm-black, clay, gold ember glow. Possible motifs: abstract archive/ledger visual, stylized candle or torchlight, SoulPrint-specific archive iconography. Rejects: AI-SaaS gradient meshes, glassmorphism panels, particle systems.
2. Feature section in Maximux bento layout. Three small tiles top (Import, Search, Ask), two wider tiles bottom (Browse transcripts, Export Passport). Demotes "Discover themes" — it's conceptually subordinate to Ask. One of the wider tiles is a code-snippet card, matching the existing terminal demo.
3. Page rhythm from Exact's section sequence: hero → "Works with" provider strip → core features bento → use cases → FAQ → final CTA. Drop testimonials (solo project, no testimonials), drop pricing (single-tier freemium, no table to show).
4. Problem-framing copy block from Cadence's placement: between hero and features. Copy adapted to preservation narrative.

### Visual identity options for the hero

If custom illustration isn't feasible, three fallback hero approaches ranked:

- **Wordmark-led.** Playfair Display "SoulPrint" with Torchlight gold glow as the whole hero. Typography carries it. Most aligned with Quiet Archive restraint. Most template-durable.
- **No metaphor.** Warm-black gradient, clay accent lines, gold wordmark, typography does the work. Closest to Cursor/Raycast restraint.
- **Archive/ledger visual.** Warm-black pane with sample conversation rows, clay accent on timestamps. Reads like looking at the app itself. Risk: screenshots age.

Wordmark-led and no-metaphor survive pattern-borrowing best. Archive-pane is the conventional "show the product" move but depends on a screenshot that needs maintenance.

---

## Open questions the Phase 2 prompt needs to answer

These weren't decided before deferral. When Phase 2 unparks, decide each:

1. **Hero metaphor.** Codexia-posture custom illustration, wordmark-led, no-metaphor, or archive-pane.
2. **Hero CTA target.** Direct `.exe` (Windows emotional-attachment user), `/releases` (cross-OS developer), or both as side-by-side buttons. Each encodes an audience assumption.
3. **Providers strip visual.** Text-with-dots (current), or provider logos. Licensing varies (OpenAI and Google have strict marks; Anthropic has guidelines; xAI has no public guidance). Safest: keep text-with-dots, update colors to PR #145 palette.
4. **Open-source prominence.** Currently understated in bottom CTA. For developer audience should be louder and nearer hero. For emotional-attachment audience matters less. Two-audience trade that shows up everywhere on the landing.
5. **Screenshot or no screenshot.** `docs/screenshots/` has Quiet Archive v3 images ready. A half-opacity product screenshot under or beside the hero answers "what does it look like" without being a carousel. Risk: screenshots age.
6. **Favicon.** Current is green USB stick. Replacements: the SoulPrint wordmark rendered at small sizes, a standalone Playfair "S" with gold glow, or a dedicated icon. A proper mark is worth committing.

---

## Phase 2 Template H prompt hooks

When the prompt gets written, the mandatory-reads block (after the standing CLAUDE.md and context/soul.md) should include:

- `landing/index.html`
- `src/app/static/app.css` lines 1-120 or wherever CSS custom properties are defined (authoritative token source)
- `docs/product/design-doctrine-quiet-archive.md`
- `docs/product/positioning.md` (for tagline pressure-testing)
- `docs/product/brand.md`
- This handoff
- `docs/product/phase-2-landing-notes.md` (the earlier notes file, if it got committed to the repo)

Scope lock defaults:
- Nothing under `src/app/` (landing is fully decoupled from app)
- Nothing under `docs/` except possibly `docs/product/positioning.md` if tagline revision happens during the work
- `CHANGELOG.md` goes *in* the edit list (retire USB-era language under `[Unreleased] / Changed`)

Stop conditions:
- Page renders with zero requests to `fonts.googleapis.com` or `fonts.gstatic.com`
- `grep -i 'usb\|capsule\|plug in\|carry it' landing/` returns zero hits
- All five providers appear everywhere providers are mentioned
- Terminal demo install command executes successfully against a fresh clone
- Accent color in CSS is `#A25B47`, surface is `#0F0D0B`
- Favicon no longer renders a USB shape
- Zero em dashes in the rendered page copy

---

## Research artifacts produced during this session

Stored in `/mnt/user-data/uploads/` during the 2026-04-23 session; may or may not have been moved into the repo:

- `Template-html.zip` — 13 Framer templates saved as HTML + images
- `Inspiration-html.zip` — 12 Inspiration-collection Framer templates
- `Pictures.zip` — 99 images scraped via Obsidian Web Clipper
- `template_triage_bundle.zip` — ChatGPT + Playwright contact sheet, CSV, and deep-read on Exact/Cadence/Codexia
- `framer-gallery.html` — self-contained HTML gallery pulling 100 preview images from Framer's Vercel CDN (works in-browser only; my sandbox can't fetch the CDN)

If any of these got committed to the repo under `docs/product/research/` or similar, future Claude should read them before drafting the prompt. If they didn't, the synthesis in this handoff is enough to proceed without the raw files.

---

## What not to do when Phase 2 unparks

- Do not re-open the "which Framer template" question. Research is closed. Pattern-first hand-coded is the answer.
- Do not re-derive the USB problem. It's identified, catalogued, and ready to fix.
- Do not assume the current landing's section rhythm is wrong. It's sound. Retokening and recomposition is the work, not redesign.
- Do not add a testimonials section (solo project, no testimonials).
- Do not add a pricing table (single-tier freemium; adding pricing signals a paid product that doesn't exist).
- Do not move to a build-step stack (Tailwind, Next.js, Astro) without deliberate trade evaluation. Current landing is single static HTML file Netlify serves directly. That simplicity is a feature.

---

## Trigger conditions for unparking

Unpark Phase 2 when one of these becomes true:

- A Reddit launch post is being drafted (r/ClaudeAI, r/LocalLLaMA, r/MyBoyfriendIsAI, r/ChatGPT).
- A Hacker News Show HN is being prepared.
- The paid packaged product (`.exe` installer) reaches feature-complete state.
- A YouTube demo recording is being planned that links to soulprint.dev.
- You notice the landing coming up in your own conversation with someone technical and feeling embarrassed about it.

Until then, the landing sits as-is. It's not great, but it's not blocking anything right now.
