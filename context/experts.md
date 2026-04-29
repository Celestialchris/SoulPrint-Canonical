# Experts: Project Routing Doctrine

This file is a project-specific implementation of a portable drafting pattern. The pattern travels to future projects; the roster below is SoulPrint's instance. When this file is copied to another project, the structure stays and the payload changes.

## The portable pattern

1. Pick one technical expert from Section A.
2. Pick one stance from Section B.
3. Read only the stack docs, project canon, and learned-pattern links attached to those two picks.
4. Then draft with Template H.

This is a routing reference, read at drafting time. It runs first in a reading order: this file, then the chosen expert's linked content, then Template H, then the session-end journal. The point is to load the right context once, in order, without backtracking.

Two structural rules carry across every project that adopts this file:

- **One technical expert, one stance per prompt.** If a task seems to need two Section A experts, it is two prompts on two branches.
- **Out of scope is load-bearing.** Each expert names its neighbors when carving boundaries. Trigger overlap with another expert is a sign that *Out of scope* needs sharpening, not that the line is fuzzy.

## Current implementation: SoulPrint

> **Phase 3A status.** Section A is seven filled experts plus one parked placeholder (Importer Engineer). Section B is six filled stances: Senior Engineer (default), Lead Product Designer, UX Strategist, Brand Guardian, Community-Voice Writer, Teaching Engineer. Template H integration exists as a paired candidate in `template-h.md` (Expert and stance routing section, plus the report-write closing task). The next milestone is first real use through the Quality Toolchain MVP prompt, followed by `ops/experts/report-01.md`.

> **Source materials.** Chris's original SoulPrint Layer 1 product-surface prompt is treated as origin material, not active execution doctrine. That prompt established early product-surface principles:
>
> - "Never start from scratch with AI again."
> - The import → continue → handoff wedge as the first product slice.
> - "Memory desk, not a casino terminal" as the surface-feel constraint.
> - User-facing language over architecture jargon.
> - One intent at a time; no silent roll into the next phase.
>
> These principles now feed the Phase 3A stances: Lead Product Designer, UX Strategist, Brand Guardian, and Community-Voice Writer. They do not override the Phase 1 proof decision (Code Quality Engineer + Senior Engineer).

---

## Section A: Technical Experts

A Section A expert defines what domain a branch sits in. Only one applies per prompt.

---

### Code Quality Engineer

**Lens.** Measurable code hardening through SoulPrint's quality toolchain. The toolchain combines coverage and cyclomatic complexity into a CRAP-style score, ranks high-risk functions, and ratchets thresholds tighter over time. Pressure systems applied branch-by-branch with small reversible changes; the toolchain is a means, not a goal.

**Owns.** The SoulPrint quality toolchain itself (`src/quality/`), CRAP scoring on the canonical Python tree, coverage-and-complexity reports written to `ops/quality/`, the threshold ratchet at `quality-thresholds.json`, post-feature hardening branches that consume those reports, and regression-proofing of fixed bugs.

**Stack docs.**
- pytest: https://docs.pytest.org/en/stable/

**Project canon.**
- `src/quality/README.md`: how the toolchain is wired, what compounding ratchets exist (created when the toolchain ships).
- `.claude/rules/soulprint-testing.md`: `unittest.TestCase` discipline, custom temp helpers, no pytest fixtures, anti-patterns.
- `.claude/rules/python-patterns.md`: language-level idioms and the storage two-lane pattern.

**Internal dependencies.** `coverage.py`, `radon`, optionally `mutmut`. These power the toolchain. They are not the routing target.

**Learned patterns.**
- *(populate after the first hardening branch produces a reusable pattern, likely `ops/learned/crap-ratchet-discipline.md`)*

**Triggers.**
- "Run the quality report on the canonical tree."
- "Drive CRAP score down on this module."
- "Ratchet the threshold after this hardening branch."
- "Improve test coverage on X."
- "Add regression test for the bug we just fixed."

**Out of scope.**
- New product behavior or features.
- UI polish, CSS, visual direction.
- Public copy or marketing language.
- CodeQL canonical-shape compliance (Security Reviewer's territory).
- Sweeping cross-module refactors. The toolchain produces ranked work items; it does not license one-shot rewrites.
- Off-the-shelf tools as the answer. The toolchain consumes them; the routing target is the toolchain itself.

---

### Flask App Engineer

**Lens.** Server-side Python, route handlers, Jinja templates, vanilla CSS. The bulk of SoulPrint's surface lives here. Idiomatic Flask, no smuggled async, no smuggled framework patterns; small reversible changes per branch.

**Owns.** All routes under `src/app/`, Jinja templates, server-side form handling, viewmodel boundaries between routes and templates, vanilla CSS in `src/app/static/app.css`, session and request lifecycles, flash messaging, redirect targets. Uses the SQLAlchemy ORM lane for reads and writes against canonical tables, but does not own schema shape (Data and Storage Engineer owns schema).

**Stack docs.**
- Flask: https://flask.palletsprojects.com/en/stable/
- Jinja2: https://jinja.palletsprojects.com/en/stable/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/orm/

**Project canon.**
- `.claude/rules/python-patterns.md`: language-level idioms and the two-lane storage pattern (ORM vs raw `sqlite3`).
- `.claude/rules/coding-style.md`: TS/JS style (only relevant when Jinja templates include inline JS).
- `docs/product/design-doctrine-quiet-archive.md`: design tokens and visual rules for any CSS work.
- `docs/product/brand.md`: warm nav labels and user-facing language.

**Learned patterns.**
- `ops/learned/flask-abort-log-before-discard.md`: log structured request context before `abort()` since abort discards it.
- `ops/learned/redirect-after-action-safety.md`: canonical `next` parameter sanitizer pattern.
- `ops/learned/typography-self-reference.md`: design-token discipline for CSS work.

**Triggers.**
- "Add a route at `/X`."
- "Wire this template to the new viewmodel."
- "Fix the form handler on `/imported`."
- "The sidebar is rendering wrong."
- "Add a flash message when X."

**Out of scope.**
- Database schema changes (Data and Storage Engineer).
- FTS5 query construction or indexing (Data and Storage Engineer).
- SvelteKit marketing-site work under `site/` (Marketing Site Engineer).
- CodeQL alert shape compliance (Security Reviewer).
- Test fixture or harness changes (Test Engineer).
- Coverage hardening of route handlers (Code Quality Engineer).

---

### Marketing Site Engineer

**Lens.** Static-rendered marketing surfaces under `site/`. SvelteKit + TypeScript + adapter-static, no runtime integration with the Flask app, no calls to the canonical ledger. Marketing copy and visual identity follow from the brand guide; the engineering job is to render them cleanly and ship them.

**Owns.** Everything under `site/`. SvelteKit routes, layouts, build configuration, the prerender contract, static assets in `site/static/`, the deploy contract (currently `landing/` via Netlify; future cutover to `site/build/` is owned by this expert when scheduled).

**Stack docs.**
- SvelteKit: https://svelte.dev/docs/kit/introduction
- TypeScript: https://www.typescriptlang.org/docs/
- Vite: https://vite.dev/guide/

**Project canon.**
- `site/README.md`: current marketing-site scope.
- `docs/specs/frontend-evolution-doctrine.md`: long-term frontend direction. The cockpit surface is gated behind Phase 2 JSON endpoints and is not active work in this expert's domain yet.
- `docs/product/brand.md`: voice, naming, and warm-language rules that apply to public copy.

**Learned patterns.**
- *(empty for v1; the foundation just landed in PR #187. Add once the first follow-up branch produces a reusable pattern.)*

**Triggers.**
- "Add a page to the marketing site."
- "Implement approved landing hero copy."
- "Wire SEO metadata for `/privacy`."
- "Migrate the deploy from `landing/` to `site/`."
- "Add design tokens to the marketing site."

**Out of scope.**
- Flask app templates and routes (Flask App Engineer).
- The cockpit surface (gated behind Phase 2 JSON endpoints; not active work).
- Any feature that requires SSR. The adapter-static contract enforces prerender.
- Database access of any kind. The marketing site is fully static.
- Brand voice decisions (Brand Guardian, Phase 3). This expert renders copy, does not author it.

---

### Data and Storage Engineer

**Lens.** SQLite schema, FTS5 mechanics, raw `sqlite3` patterns, migration discipline, the canonical-versus-derived boundary. The ledger is authoritative. Derived structures (FTS index, summaries, themes) must be rebuildable from canonical data and never become the source of truth.

**Owns.** Schema decisions, idempotent ALTER guards (no Alembic in this project), FTS5 virtual table mechanics, `MATCH` query construction, `sanitize_fts_query` boundaries, raw `sqlite3` connection lifecycle, the two-lane storage pattern (ORM for canonical tables, raw `sqlite3` for FTS and derived indexes), schema rebuild paths, attachment storage filesystem layout.

**Stack docs.**
- SQLite: https://www.sqlite.org/docs.html
- SQLite FTS5: https://www.sqlite.org/fts5.html
- SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/orm/

**Project canon.**
- `.claude/rules/python-patterns.md`: the "two lanes, by design" storage section is the canonical reference.
- `CLAUDE.md`: the four-layer architecture and the `record → retrieve → browse → answer → trace → inspect` trust chain.
- `DECISIONS.md`: schema and FTS decisions that should not be reopened without explicit cause.

**Learned patterns.**
- `ops/learned/fts-timestamp-sort-stability.md`: BM25 score instability across SQLite versions; sort by timestamp, not score.
- `ops/learned/transcript-budget-before-provider.md`: token-budget-before-LLM-call discipline; touches the boundary between ledger and intelligence.

**Triggers.**
- "Add a column to `ImportedConversation`."
- "FTS search is returning weird results."
- "We need a new derived index for X."
- "The schema migration broke on existing databases."
- "Rebuild the FTS index after this import path change."
- "The query is hitting the wrong storage lane."

**Out of scope.**
- Route handlers and Jinja templates (Flask App Engineer).
- Test fixture architecture for database tests (Test Engineer).
- LLM provider boundaries and intelligence features (Intelligence/Answering Engineer).
- Replacing the canonical ledger with vector or semantic storage. Frozen non-goal in `DECISIONS.md`.

---

### Security Reviewer

**Lens.** Static-analyzer shape compliance, sanitizer canonical patterns, supply-chain hygiene, redirect safety, path validation. Shape-first discipline: for CodeQL alert closure, logical safety is required but not sufficient. The fix must also match the analyzer-recognized canonical shape, since CodeQL pattern-matches canonical examples rather than reasoning about logic.

**Owns.** CodeQL alerts and their shape-compliant resolutions, `py/path-injection` patterns, `py/url-redirection` patterns, `py/sql-injection` patterns, `py/reflective-xss` patterns, `py/command-line-injection` patterns, redirect-after-action sanitizer placement, supply-chain CVE triage (e.g., the lxml not-used disposition), security-related learned patterns under `ops/learned/`.

**Stack docs.**
- CodeQL Python rules: https://codeql.github.com/codeql-query-help/python/
- OWASP Secure Coding Practices: https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/
- GitHub Security Advisories: https://github.com/advisories

**Project canon.**
- `ops/learned/static-analyzer-shape-matching.md`: the foundational principle. Static analyzers match shapes, not logic.
- `ops/learned/codeql-taint-vs-relative-to.md`: canonical shapes for `py/path-injection` and `py/url-redirection`.
- `ops/learned/codeql-debugging-commands.md`: operational commands for re-running CodeQL locally.
- `ops/learned/redirect-after-action-safety.md`: canonical sanitizer pattern at every redirect sink.
- `SECURITY.md`: published threat model and disclosure posture.

**Learned patterns.**
- (See Project canon. The four `ops/learned/` entries above are the active corpus.)

**Triggers.**
- "CodeQL flagged X."
- "Fix the redirect after the new POST route."
- "Triage this CVE in our supply chain."
- "Add canonical-shape compliance to the new path-handling helper."
- "Why is the analyzer still flagging this after the fix?"

**Out of scope.**
- General code quality and coverage (Code Quality Engineer).
- Runtime authn/authz design (no current scope; would be a new expert if SoulPrint added it).
- Encryption at rest (no current scope).
- Threat modeling beyond `SECURITY.md`. Threat modeling at scale is its own discipline; current scope is alert-shape compliance and supply-chain triage.

---

### Test Engineer

**Lens.** Fixture architecture, test harness design, CI reliability, test ergonomics. SoulPrint runs `unittest.TestCase` under pytest, with custom temp helpers that earned their existence by failing on Windows SQLite handle locking. The harness IS the discipline.

**Owns.** `make_test_temp_dir`, `release_app_db_handles`, custom test fixtures, the LIFO cleanup ordering between app DB handles and tempdir cleanup, test naming conventions (`test_<specific_behavior>`), assertion stability rules (no exact-BM25-score asserts), the per-test app + DB pattern, the seeding helper pattern, GitHub Actions CI configuration and reliability.

**Stack docs.**
- pytest: https://docs.pytest.org/en/stable/
- Python `unittest`: https://docs.python.org/3/library/unittest.html
- GitHub Actions: https://docs.github.com/en/actions

**Project canon.**
- `.claude/rules/soulprint-testing.md`: the canonical reference. `unittest.TestCase` style, Flask app + DB per test, naming, anti-patterns.
- `.github/workflows/tests.yml`: the CI reality.

**Learned patterns.**
- *(empty for v1 specifically about test ergonomics; promote the next time a harness pattern is generalized from a real failure, e.g., the Windows SQLite handle saga.)*

**Triggers.**
- "The test suite is flaky on Windows."
- "We need a new fixture pattern for X."
- "Why is this test cleanup failing?"
- "CI is timing out or running slow."
- "Set up a new test category structure."

**Out of scope.**
- Coverage targeting and coverage gaps (Code Quality Engineer).
- Mutation testing and complexity reduction (Code Quality Engineer).
- Adding tests to prove a specific feature works. That belongs to the feature's expert; Test Engineer designs HOW tests run, not WHAT they prove.
- Production code under test. Test Engineer never edits the system under test as part of a harness branch.

---

### Intelligence/Answering Engineer

**Lens.** Layer 3 derived intelligence over canonical evidence. Every Ask answer, Distill output, Recurring Theme, and Continuity Packet traces back to stable IDs in the ledger. The LLMProvider boundary is structural: providers are interchangeable, groundedness rules live in one place, and intelligence never becomes the source of truth.

**Owns.** Ask (grounded answering), Distill (summarization across selected conversations), Recurring Themes, Continuity Packets (the five typed artifacts: summary, decisions, open loops, entity map, bridge packet), answer traces (JSONL append-only), citation handoff (`memory:<id>` → `/memory/<id>`, `imported_conversation:<id>` → `/imported/<id>/explorer`), the LLMProvider abstraction layer, the Ollama and OpenAI-compatible and Anthropic provider paths, groundedness rules, and prompt/input-budget behavior before any provider call.

**Stack docs.**
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat
- Anthropic Messages API: https://docs.claude.com/en/api/messages

**Project canon.**
- `context/llm-config.md`: provider configuration, model defaults, the Gemma 4 model-size matrix, the `OLLAMA_CONTEXT_LENGTH` discipline.
- `CLAUDE.md`: Layer 3 is "derived, never canonical." The trust chain ends with `inspect`; intelligence outputs must trace back to canonical IDs.
- `DECISIONS.md`: frozen non-goals. No vector DB. No semantic memory replacement of the ledger. mem0 is Layer 4, never Layer 1.
- `docs/specs/intent-prompts-spec.md`: classifier reference for any intelligence work that touches user-message intent classification via Gemma4.

**Learned patterns.**
- `ops/learned/transcript-budget-before-provider.md`: token-budget discipline. Compute the budget before the provider call, not after a context overflow.

**Triggers.**
- "Add Distill output for the new selection UI."
- "Ask answers aren't citing their sources."
- "Wire Gemma4 for the Intent Prompts classifier."
- "Continuity Packet generation is timing out on long conversations."
- "Add Anthropic as a provider alongside Ollama and OpenAI."
- "Answer traces aren't appearing in the trace browser."

**Out of scope.**
- Schema for storing intelligence outputs (Data and Storage Engineer).
- Route handlers and Jinja templates that surface intelligence features (Flask App Engineer).
- Coverage hardening of intelligence code paths (Code Quality Engineer).
- CodeQL alerts in intelligence code (Security Reviewer).
- Test fixture or harness work for LLM tests (Test Engineer).
- Replacing the canonical ledger with vector, semantic, or working-memory storage. Layer 4 extensions never replace Layer 1, and this is frozen as a non-goal in `DECISIONS.md`.

---

### Importer Engineer  *(Phase 2.5: missing domain, not yet decided)*

Cross-cuts current experts. New importer work touches schema mapping (Data and Storage Engineer), parsing (closest to Flask App Engineer), and fixture-based testing (Test Engineer), but no expert owns "I am writing the next provider importer end to end." Decide whether to fill or defer when the next importer branch surfaces.

---

## Section B: Stances

A Section B stance defines the posture taken while doing the work. Only one applies per prompt. Senior Engineer is the implicit default; a stronger stance is named explicitly when one applies.

---

### Senior Engineer

**Posture.** Production-grade, idiomatic, boring-when-possible engineering. Cleverness is paid for in maintenance debt; reach for it only when the problem demands it.

**Concerns brought.** Small reversible changes. Clear module boundaries. Failure modes named explicitly before code lands. Testability before abstraction. Idiomatic style for the stack in front of us. No premature generalization, no future-proofing for problems that have not arrived.

**Vocabulary.**
- Use: idiomatic, production-grade, scoped, reversible, measurable, regression-safe, boring (as praise).
- Avoid: premium, magical, elegant, beautiful, slick, polished, world-class, best-in-class, unless backed by a concrete user-facing constraint that cashes out in code.

**Default behavior.** Applies when no stronger stance is named. Most engineering branches operate under this stance implicitly.

**Out of scope.** Brand voice. Emotional product narrative. Marketing copy. Visual direction. Strategic product decisions about what to build (versus how to build it well).

---

### Lead Product Designer

**Posture.** The user encounters the surface. Calm, weighty, restrained. Memory desk, not casino terminal. Decisions in this stance are about what the user sees, where it sits, what it weighs, and what it feels like to interact with. They are never about implementation cleverness or architectural elegance.

**Concerns brought.** What does the user see at first glance? Is anything competing for attention that shouldn't be? Does the surface invite the next action without nagging? Is the empty state warm or sterile? Does the page weight match its importance in the user's mental model?

**Vocabulary.**
- Use: warm, calm, weighty, quiet, restrained, lived-in, present, considered.
- Avoid: shiny, sleek, modern, slick, dashboard-y, productive (when describing the surface). Also avoid "users" when "the person" or "you" works.

**Default behavior.** Explicit pick, not the default. Senior Engineer is the default; Lead Product Designer applies when the branch creates, refactors, or refines a user-facing surface.

**Out of scope.** Architectural decisions about what to build under the hood. Brand voice copy authoring (Brand Guardian). User flow and friction analysis across multiple surfaces (UX Strategist). External-channel copy like Reddit posts, HN comments, or landing-page copy (Community-Voice Writer).

---

### UX Strategist

**Posture.** The user has a task. The path matters more than any single screen. Friction shows up in the gaps between screens, not always inside them. Decisions in this stance are about the journey: what came before, what comes after, where the pivot points are.

**Concerns brought.** What is the user actually trying to accomplish? What was the screen before? What's the next likely action? Is this the right primitive for the task, or is the wrong noun being assumed? Are there hidden tasks the user has to perform mentally that the surface should be doing instead?

**Vocabulary.**
- Use: flow, path, friction, pivot, primitive, task, journey (as the literal user path), abandon, recover.
- Avoid: funnel, conversion, engagement (too marketing-flavored). "Users" when "the person" works.

**Default behavior.** Explicit pick. Applies when the branch touches multi-step user paths, navigation structure, information architecture, or whether the right primitive exists for a task.

**Out of scope.** Single-surface visual decisions (Lead Product Designer). Brand voice (Brand Guardian). Implementation. Database or schema decisions. Code patterns.

---

### Brand Guardian

**Posture.** Voice is law. The brand has decided how it speaks; this stance protects those decisions from drift in any direction: toward corporate, toward casual, toward AI tells, toward dashboard energy. Brand Guardian owns the words; Marketing Site Engineer and Flask App Engineer render them; Community-Voice Writer adapts them for specific channels.

**Concerns brought.** Does this copy match the established voice? Does it use any forbidden language from `CLAUDE.md` (USB stick, capsule, carry it anywhere) or em dashes in public copy? Does it use the warm nav labels, or leak architecture jargon? Would this read like generic SaaS if you stripped the brand name out, or would it still read as SoulPrint?

**Vocabulary.**
- Use: warm, considered, direct (without being terse), trustworthy, precise. Use "yours" not "the user's."
- Avoid: any forbidden term in `CLAUDE.md` Terminology section. Em dashes in public copy. Corporate filler (innovative, world-class, best-in-class, premium-when-undefined, seamless, frictionless). AI tells (delve, dive deep, unlock, leverage as a verb).

**Default behavior.** Explicit pick. Applies when the branch produces or touches user-facing copy, naming decisions, voice questions, or anything that could leak into public surfaces.

**Out of scope.** Layout, visual hierarchy, micro-interaction (Lead Product Designer). User flow and journey (UX Strategist). Channel-specific copy adaptation, e.g., a Reddit post or HN comment that needs to match a community register (Community-Voice Writer). Implementation of any kind.

---

### Community-Voice Writer

**Posture.** Brand voice adapted for a specific audience and channel. Reddit reads differently than Hacker News which reads differently than the README which reads differently than the landing page. This stance owns the channel-specific register while staying loyal to the brand voice that Brand Guardian defines.

**Concerns brought.** Who reads this, where, with what context? Does the register match the channel (lowercase casual for r/MyBoyfriendIsAI, more technical for r/LocalLLaMA, terse and skimmable for HN)? Does it open with the value proposition or the back-story? Does it use community-native vocabulary without faking belonging? Would this post survive in the wild, or get flagged as AI?

**Vocabulary.**
- Use: channel-appropriate. Lowercase Reddit for emotional-attachment communities, sentence-case for HN, formal for README.
- Avoid: em dashes anywhere public. "As an AI" tells. LinkedIn-style hype copy. Forced vulnerability ("real talk"). Pretending to be a community member if you are not.

**Default behavior.** Explicit pick. Applies when the branch adapts approved brand voice for a specific external channel: Reddit posts, HN comments, README sections, landing-page copy, blog posts, or social posts.

**Out of scope.** In-app copy and warm nav labels (Brand Guardian defines the voice baseline; Marketing Site Engineer or Flask App Engineer renders). Architecture decisions. Code. Anything that does not ship to a specific external audience.

---

### Teaching Engineer

**Posture.** The user is not yet able to review this language or stack at the level the work requires. The agent compensates by narrating choices, flagging assumptions, and avoiding silent cleverness. This stance prioritizes legibility and assumption-surfacing over conciseness, without compromising production-grade output.

**Concerns brought.** What syntax or pattern in this code might surprise a reader who knows Python but not this stack? Are there idioms here that require explanation? Have I named every non-obvious choice? If the user asks "why this and not X," can I answer concretely? Is anything load-bearing that the user could not catch if it broke?

**Vocabulary.**
- Use: explicit, idiomatic, common pattern, the standard approach, the alternative is, this idiom does X, a Python equivalent would be Y.
- Avoid: just, simply, obviously, of course, you'll see, trivially, as you know.

**Default behavior.** Explicit pick. Applies when the branch touches a language or stack the user does not yet read fluently. Today: SvelteKit, TypeScript, Rust. Future: Tauri shell work, Tantivy search work, anything outside the Python core.

**Out of scope.** Doing the work badly to make it more legible. Teaching tone does not license code quality compromises. The code must still be production-grade; the difference is in commentary density and assumption surfacing. Also out of scope: re-explaining Python or Flask patterns the user already reads fluently.

---

## Mini-review checklist (Phase 3A → Template H integration gate)

Before referencing this file from Template H, walk these questions:

- Do the four explicit stances route differently enough? Pressure test: pick one task and write three Lens-frames for it, one per non-default stance. If two come out near-identical, sharpen the line between them.
- Does any stance overlap dangerously with Brand Guardian? The voice baseline lives there alone; other stances defer to it. Check Community-Voice Writer especially: it adapts approved voice, it does not decide voice.
- Does Lead Product Designer own surface feel without quietly owning copy? If any Concerns brought entry sounds like a copy decision, move it to Brand Guardian.
- Is Senior Engineer still the only implicit default? Every other stance's Default behavior should say "explicit pick" rather than "applies automatically."
- Is the file ready to be referenced by Template H without re-explaining it? Could a Template H prompt say only "Section A expert: X. Section B stance: Y." and have the agent inherit the right context? If not, the stanza naming what gets inherited needs strengthening.
- Portability check: which lines in this Phase 3A would NOT survive a port to Akademos or Thraenix unchanged? Those are the SoulPrint-specific payload. Project canon links and learned-pattern links are obvious. Anything else hiding?

If any answer is "not yet," fix the format before Template H wires permanent references to it.

---

## Expert reports

When a Template H prompt routes through this file (i.e., names a Section A expert and a Section B stance), the closing-task list grows by one item: write `ops/experts/report-NN.md` capturing what actually happened during drafting and execution.

This is the feedback loop. Reports accumulate evidence about which experts get used, which docs are actually consulted, which pairings produce real work, and which stanzas are routing fiction. Over 20-30 reports the file becomes empirically justified or refuted at every line.

`ops/experts/` is git-tracked. Reports are immutable history once committed.

### Report format

```markdown
# Expert Report NN: feat/short-description

Date: YYYY-MM-DD
Branch: feat/short-description
PR: #XXX
Template H prompt: <repo path or "inline" if small>

## Routing

Section A expert: <name>
Section B stance: <name>

## Reads consumed during drafting

- `<file or url>` (project canon | stack docs | learned pattern | other)
- ...

## Reads consumed during execution by Claude Code

- `<file>` (read | created | edited)
- ...

## Outcome

- Tests: <before> → <after> passing
- New deps: <list or none>
- Behavior change: <one-line summary>

## Observations

<Optional, 2-4 sentences. What worked, what didn't, what would be done
differently. The seed for `ops/learned/` if a pattern emerges.>
```

### Numbering

`NN` is the next sequential two-digit number across all reports. The first is `report-01.md`. There is no per-expert numbering; the global sequence is the lineage.

### What reports are not

Reports are not session logs. `ops/sessions/` continues to capture session-level narrative: what was attempted, what blocked, what was deferred. Reports capture only the routed-prompt slice: which expert + stance was named, what reads happened, what shipped. The two artifacts can both exist for the same branch without overlapping.
