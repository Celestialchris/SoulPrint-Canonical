# Roadmap

## Completed

- Phase 1: Repo face cleanup
- Phase 2: README/docs truth alignment
- Phase 3: Canonical workspace on `/`
- Phase 4: Import lifecycle UI
- Phase 5: In-app Ask
- Phase 6: Passport capability/status surface on `/passport`
- Phase 7: Continuity Packet MVP — typed artifacts with provenance
- Phase 8: Bridge assembly — bounded next-chat handoff
- Phase 9: Lineage suggestions — inspectable continuation/fork/revisit/supersede links
- Coherence pass — unified surfaces, fixed entrypoint, closed documentation gaps
- Phase 10 — Distribution (brand, landing, desktop, freemium, wrapped)
- Phase 10.5 — Packaging Infrastructure (PyInstaller, pyproject.toml)
- Phase 12 — Obsidian Bridge — one-way export to Obsidian vault with structured notes, themes, and daily anchors

## Current Milestone

### Phase 11 — Soft launch
- Multi-select export (checkboxes on /imported, bulk markdown download — many files)
- Fresh screenshots for docs + README with real imported data (Quiet Archive v3)
- Landing page refresh (soulprint.dev)
- Reddit posts: r/MyBoyfriendIsAI · r/ChatGPT · r/ClaudeAI
- Resolve deferred P1: loopback restriction on SOULPRINT_LLM_BASE_URL

## Next Milestone (post soft launch)

The feature queue after Phase 11 falls into three product shapes. They mature at different speeds and carry different risk profiles.

### Shape 2 — Composition features (near-term, shippable)

Small, scoped additions that operate on selections of the existing archive. Each is a weekend's work at most. These should ship first because they close specific articulation gaps for power users without reshaping the data model.

**Combine into one Markdown / PDF** — a new button near Distill that merges a user-selected set of conversations into a single document with table of contents, provenance block per conversation, and message-level timestamps. *Design decision pending:* is this the same feature as Phase 11's multi-select export, or a different feature? Multi-select export produces many files (one per conversation, zipped or downloaded together); Combine produces one merged file. These answer different user needs — many files for re-import into other tools, one merged file for pasting into a new AI conversation as context. Recommendation: ship both, label them clearly, put the Combine button near Distill (where a user is already thinking "I want one synthesized output") and keep multi-select export on `/imported` (where a user is already thinking "I want my data out").

**Intent Prompts library** — classifier-driven extraction of directive user messages from conversations, tagged by workflow stage and surfaced as a reusable prompt library in the Interpretation section. Full spec: [`docs/specs/intent-prompts-spec.md`](docs/specs/intent-prompts-spec.md). Blocks on a taxonomy commitment (workflow-stage is the current default; confirm before building the classifier prompt).

### Shape 1 — Capture pipeline (Milestone 2+, bigger scope)

Reshapes how conversations enter SoulPrint. Today's model is pull-based archival: user goes to the platform, exports a file, hands it to SoulPrint. The capture pipeline adds live-capture paths that reduce friction for heavy users but introduce ToS exposure, maintenance burden (UIs change), and data-model reshaping.

**Browser extension** — extension runs in the user's browser, has DOM access to chat.openai.com, claude.ai, gemini.google.com, and scrapes conversation history client-side. No server needed, data stays local, user authorizes by installing. This is how most data-portability tools work in practice, but it requires a ToS-first design: prefer official exports where they exist, fall back to DOM scraping only where no export is available, acknowledge the maintenance burden because platform UIs change.

**Project-aware data model** — Projects become first-class objects above Conversations, not flat tagged lists. Today's schema treats Projects as an optional string field; the capture pipeline use cases (scrape a whole Project's worth of conversations in one action, export a Project as one unit) imply Projects need their own stable IDs, provenance, and lifecycle. This is a schema change, which requires a migration plan and is why the capture pipeline needs a spec before code.

This shape is a heading, not a ticket. Individual tickets (extension manifest, Project schema migration, DOM-scraping fallback for ChatGPT) live under it once the spec is written.

### Shape 3 — Model infrastructure (below features, not a milestone)

**Gemma4 tuning** — the local-LLM stack already works via Ollama. Tuning would improve the quality of Summaries, Digests, Topics, Recurring Themes, and the Intent Prompts classifier. This is infrastructure work that doesn't ship as a feature on its own; it sits below the feature layer and is pulled forward by whichever feature most needs better local output quality. Currently the Intent Prompts classifier is the most likely pull because directive-vs-conversational classification benefits from a model that understands the user's workflow vocabulary. Deferred until at least one Shape-2 feature ships and surfaces a concrete quality gap.

## Not In Current Milestone

- mem0 activation
- hosted sync
- vector DB expansion
- mobile app

## Detail References

- Frozen decisions: `DECISIONS.md`
- Release notes: `docs/releases/RELEASE-v0.1.0.md`
- Launch playbook: `docs/releases/LAUNCH-PLAYBOOK.md`
- Intent Prompts spec: `docs/specs/intent-prompts-spec.md`
- Obsidian Bridge spec: `docs/specs/obsidian-bridge-spec.md`
- Memory Passport spec: `docs/specs/memory-passport-spec.md`
- Landscape and competitive context: `docs/product/landscape.md`
