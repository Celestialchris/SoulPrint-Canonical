# Experts: Project Routing Doctrine

## Purpose

This file is the routing doctrine for SoulPrint implementation prompts. It is a project-specific instance of a portable drafting pattern. The structure can travel to future projects. The SoulPrint payload should not.

The file exists to answer one question before a Template H prompt is drafted:

```text
Which technical domain owns this branch, and which stance should shape the work?
```

It is a routing reference, not a persona library and not a substitute for Template H.

## Portable pattern

Every real implementation prompt uses this order:

1. Pick one Section A technical expert.
2. Pick one Section B stance.
3. Read only the stack docs, project canon, and learned-pattern links attached to those two picks.
4. Draft the implementation prompt with `context/template-h.md`.
5. Close the branch with the required session journal and expert report.

Two rules carry across every project that adopts this pattern:

- **One technical expert, one stance per prompt.** If a task needs two Section A experts, it is two prompts on two branches.
- **Out of scope is load-bearing.** Trigger overlap with another expert means the boundary needs sharpening, not that multiple experts should be merged.

## Current SoulPrint status

Section A has eight filled experts and one parked placeholder:

- Code Quality Engineer
- Flask App Engineer
- Marketing Site Engineer
- Data and Storage Engineer
- Security Reviewer
- Test Engineer
- Intelligence/Answering Engineer
- Docs/Canon Steward
- Importer Engineer, parked until empirical importer friction surfaces

Section B has six stances:

- Senior Engineer, the implicit default
- Lead Product Designer
- UX Strategist
- Brand Guardian
- Community-Voice Writer
- Teaching Engineer

Routed reports 01, 02, and 04 plus the Phase 5 self-audit validated the loop. Docs/Canon Steward is now active for doctrine-integrity work and the `audit-NN.md` series. Routing Examples, Importer Engineer, Release/Ops Engineer, and audit-20 remain parked doctrine backlog unless explicitly reopened.

## Source material boundary

Chris's original SoulPrint Layer 1 product-surface prompt is origin material, not active execution doctrine. It established early surface principles:

- "Never start from scratch with AI again."
- The import, continue, handoff wedge as the first product slice.
- "Memory desk, not a casino terminal" as the surface-feel constraint.
- User-facing language over architecture jargon.
- One intent at a time. No silent roll into the next phase.

Those principles inform the non-default stances, especially Lead Product Designer, UX Strategist, Brand Guardian, and Community-Voice Writer. They do not override the routed expert and stance chosen for a branch.

---

## Section A: Technical Experts

A Section A expert defines the technical domain of a branch. Only one applies per prompt.

---

### Code Quality Engineer

**Lens.** Measurable code hardening through SoulPrint's quality toolchain. The toolchain combines coverage and cyclomatic complexity into CRAP-style scores, ranks risky functions, and ratchets thresholds over time. It is a pressure system, not an excuse for broad rewrites.

**Owns.** `src/quality/`, CRAP scoring, coverage-and-complexity reports under `ops/quality/`, `quality-thresholds.json`, threshold ratchets, post-feature hardening branches that consume quality reports, regression-proofing fixed bugs, mutation-testing workflow, mutation survivor reports, survivor triage, and mutation-killing hardening branches.

**Stack docs.**

- [pytest](https://docs.pytest.org/en/stable/)

**Project canon.**

- `src/quality/README.md`: current quality-toolchain wiring and report shape.
- `.claude/rules/soulprint-testing.md`: `unittest.TestCase` discipline, custom temp helpers, and test anti-patterns.
- `.claude/rules/python-patterns.md`: language idioms and the storage two-lane pattern.

**Learned patterns.**

- `ops/learned/per-function-coverage-from-line-data.md`: coverage.py line data joined to radon function spans.

**Triggers.**

- "Run the quality report on the canonical tree."
- "Drive CRAP score down on this module."
- "Ratchet the threshold after this hardening branch."
- "Improve test coverage on X."
- "Add a regression test for the bug we just fixed."
- "Run mutation testing and triage surviving mutants."

**Proof required.**

- Quality report path written to `ops/quality/`.
- Coverage and complexity values before and after the branch.
- Tests run and passing counts before and after.
- Threshold change in `quality-thresholds.json`, if any, with reason.
- Target chosen from a current CRAP-ranked report, not from taste.
- Mutation report path or survivor count before and after, when mutation testing is in scope.
- Surviving mutations killed, ignored, or explicitly deferred with rationale.

**Out of scope.**

- New product behavior or features.
- UI polish, CSS, or visual direction.
- Public copy or marketing language.
- CodeQL canonical-shape compliance, which belongs to Security Reviewer.
- Sweeping cross-module refactors.
- Treating off-the-shelf tools as the answer. The toolchain may consume them, but the routing target is SoulPrint's own quality pressure system.

---

### Flask App Engineer

**Lens.** Server-side Python, route handlers, Jinja templates, vanilla CSS, and request lifecycle behavior. The work should be idiomatic Flask and small enough to reverse.

**Owns.** Routes under `src/app/`, Jinja templates, server-side forms, viewmodel boundaries, vanilla CSS in `src/app/static/app.css`, session and request lifecycles, flash messages, and redirect targets. Uses SQLAlchemy ORM for canonical reads and writes, but does not own schema shape.

**Stack docs.**

- [Flask](https://flask.palletsprojects.com/en/stable/)
- [Jinja2](https://jinja.palletsprojects.com/en/stable/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

**Project canon.**

- `.claude/rules/python-patterns.md`: language idioms and the ORM/raw-SQLite split.
- `.claude/rules/coding-style.md`: TypeScript and JavaScript style for inline template scripts.
- `docs/product/design-doctrine-quiet-archive.md`: visual tokens and surface rules for CSS work.
- `docs/product/brand.md`: warm nav labels and user-facing language.

**Learned patterns.**

- `ops/learned/flask-abort-log-before-discard.md`: log structured request context before `abort()`.
- `ops/learned/redirect-after-action-safety.md`: canonical `next` parameter sanitizer pattern.
- `ops/learned/typography-self-reference.md`: typography-rule documentation can reintroduce forbidden artifacts.

**Triggers.**

- "Add a route at `/X`."
- "Wire this template to the new viewmodel."
- "Fix the form handler on `/imported`."
- "The sidebar is rendering wrong."
- "Add a flash message when X."

**Proof required.**

- Routes added, modified, or removed are named.
- Templates touched are named.
- Tests for new behavior are added or existing coverage is explicitly sufficient.
- If redirect behavior or `next` handling changed, the canonical sanitizer is inlined at every redirect sink.
- No design-token bypass and no inline hex literals introduced.

**Out of scope.**

- Database schema changes, which belong to Data and Storage Engineer.
- FTS5 query construction or indexing, which belongs to Data and Storage Engineer.
- SvelteKit marketing-site work under `site/`, which belongs to Marketing Site Engineer.
- CodeQL alert closure, which belongs to Security Reviewer.
- Test fixture or harness architecture, which belongs to Test Engineer.
- Coverage hardening, which belongs to Code Quality Engineer.

---

### Marketing Site Engineer

**Lens.** Static-rendered marketing surfaces under `site/`. The site is a public surface, not the canonical ledger and not the Flask app.

**Owns.** Everything under `site/`: SvelteKit routes, layouts, build configuration, prerender contract, static assets, and future deployment cutover from the legacy `landing/` surface when explicitly scheduled.

**Stack docs.**

- [SvelteKit](https://svelte.dev/docs/kit/introduction)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [Vite](https://vite.dev/guide/)

**Project canon.**

- `site/README.md`: current marketing-site scope.
- `docs/specs/frontend-evolution-doctrine.md`: long-term frontend direction and cockpit boundary.
- `docs/product/brand.md`: public voice, naming, and warm-language rules.
- `ops/sessions/2026-04-30-netlify-to-cloudflare-pivot.md`: Netlify is not the default forward path unless reopened deliberately.

**Learned patterns.**

- *(empty until a follow-up marketing-site branch produces a reusable pattern.)*

**Triggers.**

- "Add a page to the marketing site."
- "Implement approved landing hero copy."
- "Wire SEO metadata for `/privacy`."
- "Migrate the public site deployment."
- "Add design tokens to the marketing site."

**Proof required.**

- Page or component shipped is named.
- SvelteKit prerender contract passes.
- No runtime integration with Flask or the canonical ledger is introduced.
- Brand voice rules are honored, or copy was authored under Brand Guardian in a prior branch.
- Local fonts only. No web-font CDN introduced.

**Out of scope.**

- Flask app templates and routes, which belong to Flask App Engineer.
- The future cockpit surface, which is gated behind clean JSON endpoints.
- SSR-dependent features. The marketing site is static unless a future deployment decision changes that.
- Database access of any kind.
- Brand voice decisions. This expert renders approved copy; Brand Guardian owns the voice baseline.

---

### Data and Storage Engineer

**Lens.** SQLite schema, FTS5 mechanics, raw `sqlite3` patterns, migration discipline, and the canonical-versus-derived boundary. The ledger is authoritative. Derived structures must be rebuildable.

**Owns.** Schema decisions, idempotent ALTER guards, FTS5 virtual tables, `MATCH` query construction, `sanitize_fts_query`, raw `sqlite3` connection lifecycle, the ORM/raw-SQLite two-lane storage pattern, rebuild paths, and attachment-storage filesystem layout.

**Stack docs.**

- [SQLite](https://www.sqlite.org/docs.html)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)

**Project canon.**

- `.claude/rules/python-patterns.md`: the canonical storage two-lane pattern.
- `CLAUDE.md`: four-layer architecture and the `record -> retrieve -> browse -> answer -> trace -> inspect` trust chain.
- `DECISIONS.md`: schema and FTS decisions that should not be reopened casually.

**Learned patterns.**

- `ops/learned/fts-timestamp-sort-stability.md`: sort by timestamp, not BM25 score, across SQLite versions.
- `ops/learned/transcript-budget-before-provider.md`: token-budget discipline at the ledger/intelligence boundary.

**Triggers.**

- "Add a column to `ImportedConversation`."
- "FTS search is returning weird results."
- "We need a new derived index for X."
- "The schema migration broke on existing databases."
- "Rebuild the FTS index after this import path change."
- "The query is hitting the wrong storage lane."

**Proof required.**

- Schema changes use the established idempotent guard pattern. No Alembic.
- FTS5 structures remain rebuildable from canonical data.
- ORM and raw `sqlite3` lane boundaries are preserved.
- Migration behavior is tested against an existing database shape when relevant.
- No vector or semantic store is introduced as canonical.

**Out of scope.**

- Route handlers and Jinja templates, which belong to Flask App Engineer.
- Test fixture architecture, which belongs to Test Engineer.
- LLM provider boundaries and intelligence outputs, which belong to Intelligence/Answering Engineer.
- Replacing the canonical ledger with vector, semantic, or working-memory storage.

---

### Security Reviewer

**Lens.** Static-analyzer shape compliance, sanitizer canonical patterns, supply-chain hygiene, redirect safety, and path validation. Logical safety is required but not sufficient. CodeQL closure requires analyzer-recognized shape at the sink.

**Owns.** CodeQL alerts and shape-compliant resolutions, `py/path-injection`, `py/url-redirection`, `py/sql-injection`, `py/reflective-xss`, `py/command-line-injection`, redirect-after-action sanitizer placement, supply-chain CVE triage, and security learned patterns.

**Stack docs.**

- [CodeQL Python rules](https://codeql.github.com/codeql-query-help/python/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [GitHub Security Advisories](https://github.com/advisories)

**Project canon.**

- `ops/learned/static-analyzer-shape-matching.md`: static analyzers match shapes, not intent.
- `ops/learned/codeql-taint-vs-relative-to.md`: canonical shapes for path injection and URL redirection.
- `ops/learned/codeql-debugging-commands.md`: local CodeQL commands.
- `ops/learned/redirect-after-action-safety.md`: redirect sanitizer discipline.
- `SECURITY.md`: published threat model and disclosure posture.

**Learned patterns.**

- See the Project canon list. The security corpus already lives there.

**Triggers.**

- "CodeQL flagged X."
- "Fix the redirect after the new POST route."
- "Triage this CVE in our supply chain."
- "Add canonical-shape compliance to the new path-handling helper."
- "Why is the analyzer still flagging this after the fix?"

**Proof required.**

- Security finding is named. If CodeQL-driven, alert ID and post-fix scan result are named.
- Canonical sanitizer shape is inlined at the sink.
- Regression test fails before the fix and passes after, when applicable.
- No stricter-but-unrecognized variant replaces the canonical shape.
- Supply-chain disposition is recorded if a CVE was triaged.

**Out of scope.**

- General code quality and coverage, which belong to Code Quality Engineer.
- Test harness design, which belongs to Test Engineer.
- Broad threat modeling beyond `SECURITY.md`.
- Runtime authn/authz design, unless SoulPrint explicitly adds that domain later.
- Encryption at rest, unless reopened as a dedicated product/security decision.

---

### Test Engineer

**Lens.** Fixture architecture, test harness design, CI reliability, and test ergonomics. SoulPrint runs `unittest.TestCase` under pytest with custom temp helpers. The harness is part of the product's discipline.

**Owns.** `make_test_temp_dir`, `release_app_db_handles`, custom test fixtures, LIFO cleanup ordering, test naming conventions, assertion stability rules, per-test app and DB setup, seeding helper patterns, and GitHub Actions CI reliability.

**Stack docs.**

- [pytest](https://docs.pytest.org/en/stable/)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [GitHub Actions](https://docs.github.com/en/actions)

**Project canon.**

- `.claude/rules/soulprint-testing.md`: canonical test style and anti-patterns.
- `.github/workflows/tests.yml`: CI reality.

**Learned patterns.**

- `ops/learned/github-actions-bot-pr-gating.md`: bot-authored PR job gating and required-status-check caveat.

**Triggers.**

- "The test suite is flaky on Windows."
- "We need a new fixture pattern for X."
- "Why is this test cleanup failing?"
- "CI is timing out or running slow."
- "Set up a new test category structure."

**Proof required.**

- Fixture pattern conforms to the established tempdir and DB-handle discipline.
- No bare `tempfile.TemporaryDirectory()` introduced for DB paths.
- `Config.SQLALCHEMY_DATABASE_URI` is restored after tests that mutate it.
- Full suite is green when Python or harness behavior changes.
- Workflow-only branches document relevant workflow verification.

**Out of scope.**

- Coverage targeting, mutation testing, and complexity reduction, which belong to Code Quality Engineer.
- Adding feature-specific tests while implementing a feature. That belongs to the feature's expert.
- Production code under test. Test Engineer edits the harness, not the system under test.

---

### Intelligence/Answering Engineer

**Lens.** Layer 3 derived intelligence over canonical evidence. Ask answers, Distill outputs, Recurring Themes, and Continuity Packets must trace back to stable IDs. Intelligence never becomes canonical memory.

**Owns.** Ask, Distill, Recurring Themes, Continuity Packets, answer traces, citation handoff, LLMProvider abstraction, Ollama, OpenAI-compatible and Anthropic provider paths, groundedness rules, and prompt/input-budget behavior before provider calls.

**Stack docs.**

- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [OpenAI Chat Completions](https://platform.openai.com/docs/api-reference/chat)
- [Anthropic Messages API](https://docs.claude.com/en/api/messages)

**Project canon.**

- `context/llm-config.md`: provider configuration, model defaults, Gemma 4 model-size matrix, and `OLLAMA_CONTEXT_LENGTH` discipline.
- `CLAUDE.md`: Layer 3 is derived, never canonical.
- `DECISIONS.md`: no vector DB, no semantic replacement of the ledger, and mem0 only as a downstream layer.
- `docs/specs/intent-prompts-spec.md`: classifier reference for intent extraction work.

**Learned patterns.**

- `ops/learned/transcript-budget-before-provider.md`: compute input budget before provider calls.

**Triggers.**

- "Add Distill output for the new selection UI."
- "Ask answers aren't citing their sources."
- "Wire Gemma4 for the Intent Prompts classifier."
- "Continuity Packet generation is timing out on long conversations."
- "Add Anthropic as a provider alongside Ollama and OpenAI."
- "Answer traces aren't appearing in the trace browser."

**Proof required.**

- Citation handoff resolves from stable IDs back to canonical records.
- Answer trace is appended with stable IDs.
- `LLMProvider` boundary remains intact.
- Token budget is computed before provider calls.
- No canonical ledger mutation occurs in intelligence-layer code.

**Out of scope.**

- Schema for storing intelligence outputs, which belongs to Data and Storage Engineer.
- Routes and templates that surface intelligence features, which belong to Flask App Engineer.
- Coverage hardening, which belongs to Code Quality Engineer.
- Security alerts, which belong to Security Reviewer.
- LLM test harness architecture, which belongs to Test Engineer.
- Replacing the canonical ledger with vector, semantic, or working-memory storage.

---

### Docs/Canon Steward

**Lens.** Project memory must remain coherent. Canon files, decisions, learned patterns, expert reports, templates, and session doctrine must not drift into contradiction, duplication, stale instruction, or false authority.

**Owns.** Doctrine-integrity work across `CLAUDE.md`, `DECISIONS.md`, `context/template-h.md`, `context/experts.md`, `ops/learned/`, `ops/experts/`, and the `ops/phase-5/audit-NN.md` series; report-observation promotion into canon; deprecated-rule removal; terminology audits; routing-system audits; doctrine portability checks; and cross-file consistency when canon surfaces disagree.

**Stack docs.**

- None for v1. This expert owns project-canon integrity, not an external technology stack.

**Project canon.**

- `CLAUDE.md`: project orientation and standing-read trigger.
- `DECISIONS.md`: frozen non-goals and architectural commitments.
- `context/experts.md`: this file.
- `context/template-h.md`: the paired execution scaffold.
- `ops/phase-5/audit-phase-5.md`: first routing-system self-audit and empirical baseline for this expert.

**Learned patterns.**

- `ops/learned/typography-self-reference.md`: docs about forbidden typography must not reproduce the forbidden artifact.

**Triggers.**

- "These canon files contradict each other."
- "Promote this report observation into learned patterns or canon."
- "Audit Template H against `experts.md`."
- "Prepare this routing system for another project."
- "Remove stale canon or deprecated rules."
- "The doctrine changed after this branch."
- "Run the next routing-system audit."
- "Clarify whether a session note, expert report, learned pattern, or decision record owns this evidence."

**Proof required.**

- Contradiction, stale claim, or doctrine gap is named.
- Source files checked are named.
- Replacement rule or retained exception is stated.
- Deprecated language is removed or explicitly retained with reason.
- No implementation scope is smuggled into the doctrine edit.

**Out of scope.**

- Feature implementation in `src/`, `site/`, or any code surface.
- Public marketing copy, launch copy, Reddit or HN writing, and brand voice authoring.
- Product strategy decisions about what SoulPrint should build next.
- Visual or surface decisions, which belong to Lead Product Designer.
- Multi-step user paths and information architecture, which belong to UX Strategist.
- Test harness mechanics and CI reliability, which belong to Test Engineer.
- CodeQL alert closure, CVE triage, and sanitizer shape compliance, which belong to Security Reviewer.
- Schema, FTS, raw `sqlite3`, and canonical ledger shape, which belong to Data and Storage Engineer.
- Coverage, complexity, CRAP scoring, and mutation testing, which belong to Code Quality Engineer.
- Intelligence and answering features, which belong to Intelligence/Answering Engineer.
- Importer implementation or importer regression behavior. Importer Engineer remains parked.

---

### Importer Engineer, parked

Importer work currently cross-cuts Data and Storage Engineer, Flask App Engineer, and Test Engineer. No filled expert owns end-to-end provider import work yet.

Keep this expert parked until a real importer branch exposes repeated routing friction. When it is promoted, it should own provider export parsing, malformed export handling, source metadata mapping, duplicate detection policy, importer summaries, skipped/imported counts, source conversation IDs, and importer-specific regression tests.

---

## Section B: Stances

A Section B stance defines the posture taken while doing the work. Only one applies per prompt. Senior Engineer is the implicit default; a stronger stance is named explicitly when it matters.

---

### Senior Engineer

**Posture.** Production-grade, idiomatic, boring-when-possible engineering. Cleverness is paid for in maintenance debt. Use it only when the problem demands it.

**Concerns brought.** Small reversible changes, clear module boundaries, named failure modes, testability before abstraction, idiomatic style, and no premature generalization.

**Vocabulary.**

- Use: idiomatic, production-grade, scoped, reversible, measurable, regression-safe, boring as praise.
- Avoid: premium, magical, elegant, beautiful, slick, polished, world-class, and best-in-class unless backed by a concrete constraint.

**Default behavior.** Applies when no stronger stance is named.

**Out of scope.** Brand voice, emotional product narrative, marketing copy, visual direction, and strategic product decisions about what to build next.

---

### Lead Product Designer

**Posture.** The person encounters the surface. Calm, weighty, restrained. Memory desk, not casino terminal.

**Concerns brought.** First glance, attention weight, empty states, affordance clarity, surface hierarchy, page weight, and whether the next action is invited without nagging.

**Vocabulary.**

- Use: warm, calm, weighty, quiet, restrained, lived-in, present, considered.
- Avoid: shiny, sleek, modern, slick, dashboard-y, productive for surface description, and "users" when "the person" or "you" works.

**Default behavior.** Explicit pick. Applies when a branch creates, refactors, or refines a user-facing surface.

**Out of scope.** Architecture, brand voice copy, multi-surface flow analysis, external-channel writing, and implementation cleverness.

---

### UX Strategist

**Posture.** The person has a task. The path matters more than any single screen. Friction often lives between screens.

**Concerns brought.** User task, previous screen, next likely action, correct primitive, hidden mental work, abandon points, recovery points, and information architecture.

**Vocabulary.**

- Use: flow, path, friction, pivot, primitive, task, journey, abandon, recover.
- Avoid: funnel, conversion, engagement, and "users" when "the person" works.

**Default behavior.** Explicit pick. Applies when a branch touches multi-step paths, navigation structure, information architecture, or task primitives.

**Out of scope.** Single-surface visual decisions, brand voice, implementation, database shape, and code patterns.

---

### Brand Guardian

**Posture.** Voice is law. The brand has decided how it speaks. This stance protects that voice from corporate drift, casual drift, AI tells, and dashboard energy.

**Concerns brought.** Copy fidelity, forbidden language, warm labels, architecture jargon leakage, public tone, naming decisions, and whether text still reads as SoulPrint after the brand name is removed.

**Vocabulary.**

- Use: warm, considered, direct, trustworthy, precise, and "yours" instead of "the user's."
- Avoid: forbidden terms in `CLAUDE.md`, em dashes in public copy, corporate filler, and AI tells.

**Default behavior.** Explicit pick. Applies when a branch produces or touches user-facing copy, naming, voice, or public surfaces.

**Out of scope.** Layout, visual hierarchy, micro-interaction, user journey, external-channel adaptation, and implementation.

---

### Community-Voice Writer

**Posture.** Brand voice adapted for a specific audience and channel. Reddit, Hacker News, README, landing pages, and social posts do not speak the same register.

**Concerns brought.** Audience, channel context, register, opening angle, community-native vocabulary, credibility, and whether the piece would survive in the wild.

**Vocabulary.**

- Use: channel-appropriate language.
- Avoid: em dashes anywhere public, AI tells, LinkedIn-style hype, forced vulnerability, and fake belonging.

**Default behavior.** Explicit pick. Applies when approved brand voice must be adapted for a specific external channel.

**Out of scope.** In-app copy baseline, architecture, code, and any artifact that does not ship to a specific external audience.

---

### Teaching Engineer

**Posture.** The user is not yet able to review this language or stack at the level the work requires. The agent compensates by surfacing assumptions and narrating non-obvious choices.

**Concerns brought.** Surprise syntax, unfamiliar idioms, hidden assumptions, load-bearing choices, reviewability, and whether the user can understand why one approach was chosen over another.

**Vocabulary.**

- Use: explicit, idiomatic, common pattern, standard approach, alternative, this idiom does X, a Python equivalent would be Y.
- Avoid: just, simply, obviously, of course, you'll see, trivially, and as you know.

**Default behavior.** Explicit pick. Applies when a branch touches a language or stack Chris does not yet read fluently. Current examples: SvelteKit, TypeScript, Rust, Tauri, and Tantivy.

**Out of scope.** Lowering code quality to make the work easier to explain. The code stays production-grade; the commentary becomes denser.

---

## Maintenance checklist

Use this checklist when editing this file or porting it to another project:

- Each Section A expert must have the same field order.
- Filled experts must include `Lens`, `Owns`, `Stack docs`, `Project canon`, `Learned patterns`, `Triggers`, `Proof required`, and `Out of scope`.
- Parked experts must remain visibly parked and must not be counted as filled.
- Senior Engineer remains the only implicit default stance.
- Non-default stances must stay meaningfully distinct from Brand Guardian.
- Lead Product Designer owns surface feel, not copy authorship.
- UX Strategist owns paths and primitives, not single-screen visual polish.
- Community-Voice Writer adapts approved voice; it does not define the voice baseline.
- Project-canon and learned-pattern links must stay selective. Do not turn this file into a library swamp.
- Portability edits should preserve structure and replace only project payload.

---

## Expert reports

When a Template H prompt names a Section A expert and a Section B stance, the closing-task list grows by one item: write `ops/experts/report-NN.md`.

Reports are the feedback loop. They show which experts get used, which docs are actually consulted, which pairings produce real work, and which stanzas are routing fiction. Over time, the file becomes empirically justified or refuted.

`ops/experts/` is git-tracked. Reports are immutable history once committed.

### Report format

```markdown
# Expert Report NN: feat/short-description

Date: YYYY-MM-DD
Branch: feat/short-description
PR: #[number]
Template H prompt: [repo path or inline]

## Routing

Section A expert: [name]
Section B stance: [name]

## Reads consumed during drafting

- `[file or url]` (project canon | stack docs | learned pattern | other)
- ...

## Reads consumed during execution by Claude Code

- `[file]` (read | created | edited)
- ...

## Outcome

- Tests: [before] -> [after] passing
- New deps: [list or none]
- Behavior change: [one-line summary]

## Observations

[Optional, two to four sentences. What worked, what failed, and what would be done differently. This can seed `ops/learned/` if a pattern emerges.]
```

### Numbering

`NN` is the next sequential two-digit number across all reports. The first report is `report-01.md`. There is no per-expert numbering; the global sequence is the lineage.

### What reports are not

Reports are not session logs. `ops/sessions/` continues to capture the session-level narrative: what was attempted, what blocked, and what was deferred. Reports capture only the routed-prompt slice: which expert and stance were named, what reads happened, and what shipped.
