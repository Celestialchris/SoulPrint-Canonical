# Roadmap

## Completed

- Phase 1: Repo face cleanup
- Phase 2: README/docs truth alignment
- Phase 3: Canonical workspace on `/`
- Phase 4: Import lifecycle UI
- Phase 5: In-app Ask
- Phase 6: Passport capability/status surface on `/passport`

## Current Milestone

### Phase 0 — Project spine freeze
- Align README and ROADMAP with the current strategy
- Freeze the next milestone and execution order

### Phase 1 — Continuity Packet MVP
- Define typed continuity artifacts
- Persist them locally as derived artifacts with provenance
- Generate them through the existing intelligence provider boundary
- Expose a minimal UI to generate, inspect, and copy a next-chat handoff

### Phase 2 — Bridge assembly
- Build compact next-chat bridges from continuity artifacts
- Keep handoff size bounded and operational

### Phase 3 — Lineage suggestions
- Propose inspectable continue / fork / revisit / supersede links
- Keep lineage derived and non-authoritative

### Phase 4 — Distribution
- Brand identity
- Landing page
- Desktop wrapper
- Freemium gate
- Wrapped summary page

### Phase 5 — Soft launch
- Release tag
- Screenshots
- Landing page live
- Signup / feedback loop

## Not In Current Milestone

- mem0 activation
- Hosted sync
- Vector DB expansion
- Mobile app
- Large-scale design overhaul before continuity ships

# SoulPrint — Roadmap

*Sequenced build plan. Phases are ordered. Do not skip ahead.*

---

## Phase 1: Continuity Packet MVP

**Goal:** A user can end a thread, generate a structured handoff, and start the next chat without dragging the full conversation behind them.

**Branch:** `feature/continuity-packet`

### Deliverables

1. **Schema** — `DerivedContinuityPacket` dataclass with fields:
   - `packet_id` (stable, generated)
   - `source_conversation_ids` (list of canonical IDs)
   - `packet_type` (enum: `handoff`, `decision-ledger`, `open-loops`, `entity-map`, `bridge`)
   - `summary` (text)
   - `decisions_made` (list)
   - `constraints_established` (list)
   - `unresolved_questions` (list)
   - `next_steps` (list)
   - `key_entities` (list)
   - `working_vocabulary` (dict)
   - `generation_timestamp`
   - `llm_provider_used`
   - `prompt_template_version`
   - `confidence_notes` (optional)

2. **Module** — `src/intelligence/continuity.py`
   - `generate_continuity_packet(conversation_id) -> DerivedContinuityPacket`
   - Uses `provider_from_config()` (same boundary as summaries/digests)
   - Reads canonical conversation + ordered messages
   - Builds structured prompt requesting typed fields
   - Persists result as derived artifact with full provenance

3. **Persistence** — continuity packet table in SQLite
   - Linked to source conversation(s) via stable IDs
   - Queryable by conversation, by type, by date

4. **Endpoint** — `POST /intelligence/continuity/<conversation_id>`
   - Returns generated packet
   - Stores in DB

5. **UI** — Two interactions:
   - "Generate Continuity Packet" button on conversation detail view
   - "Copy for New Chat" action on packet view (copies formatted handoff to clipboard)

6. **Tests** — Schema validation, generation with stub provider, persistence, endpoint, empty conversation edge case

### Not in scope
- Automatic lineage detection (Phase 3)
- Bridge assembly from multiple packets (Phase 2)
- LLM-free fallback for packet generation (future — unlike topics, packets need structured synthesis)

---

## Phase 2: Bridge Assembly

**Goal:** Build a minimal next-chat context packet from one or more continuity packets plus cited canonical snippets.

**Branch:** `feature/continuity-bridge`

### Deliverables

1. **Module** — `src/intelligence/bridge.py`
   - `assemble_bridge(packet_ids, max_tokens=3000) -> BridgePacket`
   - Takes latest relevant packet + optional ancestor packets
   - Adds cited canonical snippets if needed
   - Produces a compact, copy-ready handoff under token budget

2. **UI** — "Start New Chat from Continuity" action
   - Shows last relevant packet
   - Lets user confirm/edit before copying
   - Clear provenance: "Based on packet from [conversation title], generated [date]"

3. **Tests** — Bridge assembly, token budget enforcement, multi-packet merge

---

## Phase 3: Lineage Suggestions

**Goal:** Detect likely parent threads and propose continuation/fork/revisit links.

**Branch:** `feature/lineage-suggestions`

### Deliverables

1. **Module** — `src/intelligence/lineage.py`
   - `suggest_parent_threads(conversation_id) -> list[LineageSuggestion]`
   - Uses: temporal proximity, title/keyword overlap, shared entities, user tags
   - Heuristic-first (no LLM required for basic matching)
   - LLM-enhanced ranking when provider configured

2. **Schema** — `continuity_link` table
   - `source_id`, `target_id`, `link_type` (continues/forks/revisits/supersedes)
   - `confidence`, `suggested_by` (heuristic/llm/user), `confirmed_by_user` (bool)
   - Derived, not canonical. Links never mutate the ledger.

3. **UI** — On import: "This looks related to N previous threads. Continue from one?"
   - User confirms, edits, or dismisses
   - Confirmed links stored, dismissed links logged

4. **Tests** — Heuristic matching, suggestion ranking, link persistence, user confirmation flow

---

## Phase 4: Distribution

**Goal:** Package the product for real users. Execute the 30-Day Vision features.

**Prerequisite:** Phases 1-3 stable, or at minimum Phase 1 merged.

### Sub-phases (each is a separate branch and PR):

**4a. Brand Identity**
- Logo SVG, favicon, brand.md, base.html update
- See `roadmap/BRAND-PROMPTS.md` → Prompt 1

**4b. Landing Page**
- Static HTML/CSS at `landing/`
- Hero, product loop, "what it is not," features, trust, email capture
- See `roadmap/BRAND-PROMPTS.md` → Prompt 2

**4c. Desktop Wrapper**
- PyWebView at `desktop/launcher.py`
- See `roadmap/BRAND-PROMPTS.md` → Prompt 3

**4d. Freemium Gate**
- Local license key, free/pro split, upgrade prompts
- See `roadmap/BRAND-PROMPTS.md` → Prompt 4

**4e. Wrapped Summary Page**
- `/summary` route, shareable visual summary, growth hook
- See `roadmap/BRAND-PROMPTS.md` → Prompt 5

### Execution rule
Each sub-phase is self-contained. Merge and test before starting the next.

---

## Phase 5: Future Providers

**Goal:** Expand import coverage after the core product loop is solid.

Near-term: Grok, Copilot, Perplexity
Medium-term: Ollama, DeepSeek, Mistral Le Chat

Each follows the established contract: adapter, detector, registry, fixture, tests.

---

## Phase 6: Auto-Hook UX

**Goal:** Full continuity workflow — new import arrives, SoulPrint proposes parent thread, builds bridge packet, user launches new chat with handoff.

This is the compound feature that ties Phases 1-3 into a single product loop. Only build after all three are stable.

---

## Priority Rules

1. Continuity packets before distribution. The spine before the skin.
2. Each phase ships working, tested code. No speculative scaffolding.
3. Design is frozen until Phase 1 merges. The Torchlit Vault spec is the contract.
4. If a phase is too broad, narrow to the smallest executable step and state that.
5. Every PR answers: does this make the product more useful, more coherent, or more shippable?

