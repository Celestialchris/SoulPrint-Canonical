Here is the clean hybrid spine.

The core correction is this: the **real product wedge is not “better chat memory” in the abstract, it is continuity under user custody**. The docs converge on the same point: giant chatboxes degrade quality because they accumulate undifferentiated context, so SoulPrint should convert each chat into a canonical shard and generate compact, provenance-bound continuity handoffs instead of trying to keep one immortal mega-thread alive. The continuity packet is therefore not a side feature. It is the missing weapon.  

The second correction is architectural: **continuity belongs inside the existing intelligence boundary**, using the same provider interface already used for summaries, topics, and digests. It should be stored as a derived artifact with source conversation IDs, provider, timestamp, and prompt version. mem0 stays optional, downstream, and non-authoritative. 

The third correction is sequencing: Claude’s action-plan rhythm is right, but the order needs one override. Keep Claude’s **one-branch, one-task, branch/paste/test/merge** discipline, and keep the five distribution PRs for brand, landing, desktop, freemium, and Wrapped. But those now come **after** the continuity spine, not before it. The 30-day vision defines the distribution path clearly, and the design guidance already says the public face should be lucid while the deeper glow is concentrated in high-meaning surfaces.   

## Final repo order

**Phase 0 — Freeze the law**
Lock README, DECISIONS, and ROADMAP so the repo stops re-litigating itself.

**Phase 1 — Continuity Packet MVP**
Define the typed continuity artifact, persist it, generate it through the existing LLMProvider boundary, expose it through a route/action, and let the user copy it into a new chat. This is Lane 1 and it ships before lineage. 

**Phase 2 — Bridge Assembly**
Build the minimal next-chat handoff from one or more packets plus cited canonical snippets. The target is a compact 1k–3k token seed, not a corpse-dragging mega-context. 

**Phase 3 — Lineage Suggestions**
Only after packets exist, add inspectable parent-thread suggestions: continue, fork, revisit, supersede. These links stay derived, never canonical. 

**Phase 4 — Distribution**
Now Claude’s original release path applies in order:
brand identity, landing page, desktop wrapper, freemium gate, Wrapped summary.  

**Phase 5 — Soft launch**
Release tag, screenshots, landing page live, posts, signup list. 

## Non-negotiable rules for every agent task

Use these as law for Codex or Claude Code:

* Work on **one task only**.
* Do **not** begin the next phase.
* Do **not** widen scope.
* Do **not** change unrelated files.
* Keep canonical truth and derived intelligence clearly separated.
* If blocked, state the blocker and stop.
* Run relevant tests before finishing.
* End with a concise summary of changed files, tests run, and anything deferred.

Below are paste-ready prompts. Each one is bounded to a single task.

---

## Prompt 0 — Freeze README / DECISIONS / ROADMAP

```text
git checkout main && git pull
git checkout -b chore/project-spine

Read the current repo files that define project identity and planning, especially:
- README.md
- ROADMAP.md
- DECISIONS.md
- docs/product/visual-direction.md (if present)

Task:
Create or update the repo’s project spine so the current strategy is explicit and frozen.

Required outcomes:
1. README.md must state:
   - SoulPrint one-liner
   - current status in concise terms
   - architecture layers
   - what is next: continuity packets
   - pointer to ROADMAP.md and DECISIONS.md

2. DECISIONS.md must record only settled decisions:
   - SQLite canonical ledger
   - derived artifacts store provenance
   - mem0 optional/downstream/non-authoritative
   - continuity packet ships before lineage suggestions
   - continuity engine lives in existing intelligence boundary
   - design/distribution comes after continuity MVP
   - free vs paid boundary at a high level

3. ROADMAP.md must define the actual sequence:
   - Phase 0: project spine
   - Phase 1: continuity packet MVP
   - Phase 2: bridge assembly
   - Phase 3: lineage suggestions
   - Phase 4: brand, landing, desktop, freemium, wrapped
   - Phase 5: soft launch

Strict rules:
- Work only on these documentation files.
- Do not change app code, templates, routes, CSS, DB schema, or tests.
- Do not add speculative future architecture beyond the listed phases.
- If the files already exist, update them minimally instead of rewriting everything.
- Stop after the docs are coherent.

Definition of done:
- README, DECISIONS, and ROADMAP agree with each other
- continuity packets are clearly marked as the next engineering milestone
- no application code changes were made
```

---

## Prompt 1 — Continuity artifact schema and persistence

```text
git checkout main && git pull
git checkout -b feature/continuity-schema

Read:
- README.md
- ROADMAP.md
- DECISIONS.md
- src/intelligence/provider.py
- any existing derived-artifact persistence code for summaries/topics/digests

Task:
Implement the typed continuity artifact schema and persistence layer only.

Required outcomes:
1. Create a continuity package under src/intelligence/continuity/ with at least:
   - __init__.py
   - models.py
   - store.py

2. Define typed continuity artifacts for:
   - summary
   - decisions
   - open_loops
   - entity_map
   - bridge

3. Each stored continuity artifact must include:
   - artifact_id
   - artifact_type
   - source_conversation_ids
   - parent_packet_ids (optional)
   - llm_provider_used
   - prompt_template_version
   - generation_timestamp
   - content_text and/or content_json
   - confidence_notes or ambiguity_notes

4. Add persistence support using the existing canonical app database patterns.
   - Continuity artifacts are derived, not canonical
   - Do not mutate canonical conversation rows
   - If the repo has an existing derived-artifact table pattern, follow it
   - Otherwise add the smallest clean table(s) needed

5. Add tests for:
   - round-trip persistence
   - artifact type validation
   - source conversation ID storage
   - timestamp/provider/prompt version persistence

Strict rules:
- Work only on schema + persistence.
- Do not implement generation logic.
- Do not add routes, templates, or UI.
- Do not introduce mem0, vector DBs, or any hosted services.
- Keep the change minimal and idiomatic to the existing repo.

Definition of done:
- continuity artifacts can be created and stored locally
- tests for schema/persistence pass
- no UI or route changes exist in this PR
```

---

## Prompt 2 — Continuity generation service

```text
git checkout main && git pull
git checkout -b feature/continuity-generation

Read:
- src/intelligence/provider.py
- existing summary/topic/digest generation code
- src/intelligence/continuity/models.py
- src/intelligence/continuity/store.py

Task:
Implement the continuity packet generation service using the existing LLMProvider boundary.

Required outcomes:
1. Create src/intelligence/continuity/service.py

2. Implement a function equivalent to:
   generate_continuity_packet(conversation_id, db/session, provider_config, prompt_version="v1")

3. The generator must:
   - read one canonical conversation and its ordered messages
   - build a compact continuity prompt
   - call the existing provider boundary, not a new engine
   - produce typed outputs for:
     - summary
     - decisions
     - open_loops
     - entity_map
   - persist those artifacts through continuity/store.py

4. Use BYOK provider config via the repo’s existing pattern.
   - If no provider is configured, fail gracefully with a useful error
   - Do not introduce mem0
   - Do not add a second intelligence system

5. Add tests for:
   - successful generation with stub provider
   - graceful failure when provider is missing
   - persisted artifacts contain provider name and prompt version
   - no canonical data is mutated

Strict rules:
- Work only on the generation service.
- Do not add routes, templates, buttons, or UI.
- Do not implement bridge assembly in this task.
- Reuse existing provider interfaces exactly where possible.

Definition of done:
- one canonical conversation can produce stored continuity artifacts
- the service runs through the existing provider boundary
- tests pass
```

---

## Prompt 3 — Continuity endpoint

```text
git checkout main && git pull
git checkout -b feature/continuity-endpoint

Read:
- existing app route patterns
- src/intelligence/continuity/service.py
- any existing intelligence routes for summaries/topics/digests

Task:
Add the server-side endpoint to generate and retrieve continuity packets.

Required outcomes:
1. Add a POST endpoint:
   /intelligence/continuity/<conversation_id>

2. Add a GET endpoint or equivalent retrieval surface to view the latest continuity packet for a conversation.

3. POST behavior:
   - resolve the canonical conversation
   - call the continuity generation service
   - return a success response with packet/artifact identifiers
   - return a friendly error if no provider is configured

4. GET behavior:
   - show the latest continuity artifacts for the selected conversation
   - clearly label them as derived / non-canonical

5. Add tests for:
   - successful POST generation
   - missing-provider error path
   - GET renders continuity data
   - response does not imply canonical authority

Strict rules:
- Work only on routes/controller logic and tests.
- Do not add visual polish beyond the minimum needed to render the data.
- Do not add the “Copy for New Chat” UX yet.
- Do not change unrelated routes.

Definition of done:
- continuity generation is callable from the app
- continuity packets are retrievable
- tests pass
```

---

## Prompt 4 — Continuity UI: generate + view + copy

```text
git checkout main && git pull
git checkout -b feature/continuity-ui

Read:
- templates and route outputs related to conversation detail / explorer views
- continuity endpoint outputs
- docs/product/visual-direction.md if present

Task:
Add the minimum continuity UI needed for a user to generate, inspect, and copy a continuity packet.

Required outcomes:
1. In the appropriate conversation detail or explorer surface, add:
   - a “Generate Continuity Packet” action
   - only where it makes product sense

2. Create a continuity view/template that displays:
   - summary
   - decisions
   - open loops
   - entity map
   - explicit derived / non-canonical labeling
   - provenance references to the source conversation

3. Add a “Copy for New Chat” action that copies a compact handoff text to clipboard.
   - If clipboard support is awkward, provide a selectable text area as fallback

4. The handoff text should be compact and operational, not verbose.
   - objective
   - decisions made
   - constraints
   - open loops
   - next-step seed

5. Add UI tests if the repo uses them, otherwise add route/template tests that prove the view renders.

Strict rules:
- Work only on the continuity UI.
- Do not redesign the app globally.
- Do not implement bridge assembly or lineage suggestions here.
- Keep visual changes local and minimal.

Definition of done:
- a user can generate a packet, inspect it, and copy a next-chat handoff
- the UI makes the derived status unmistakable
- tests pass
```

---

## Prompt 5 — Bridge assembly

```text
git checkout main && git pull
git checkout -b feature/continuity-bridge

Read:
- continuity models/store/service
- copied handoff format from the current continuity UI
- any retrieval utilities already used by Ask/traces

Task:
Implement bridge assembly for the next-chat handoff.

Required outcomes:
1. Create src/intelligence/continuity/bridge.py

2. Implement logic that assembles a compact next-chat bridge from:
   - the latest relevant continuity packet
   - optionally one or two parent packets
   - a few cited canonical snippets if needed

3. Output target:
   - compact operational handoff
   - roughly 1k–3k tokens max
   - never raw mega-context dumps

4. The bridge should include:
   - prior objective
   - last confirmed state
   - key decisions
   - constraints
   - open loops
   - suggested next-step prompt seed

5. Add tests for:
   - bridge assembly from one packet
   - bridge assembly with parents
   - token/length guardrails
   - graceful behavior when parent packets do not exist

Strict rules:
- Work only on bridge assembly.
- Do not add lineage inference here.
- Do not redesign existing UI.
- Keep outputs provenance-aware and derived.

Definition of done:
- the repo can build a compact next-chat bridge from continuity artifacts
- tests pass
```

---

## Prompt 6 — Lineage suggestions

```text
git checkout main && git pull
git checkout -b feature/lineage-suggestions

Read:
- continuity models and bridge logic
- import metadata for conversations
- any search/retrieval utilities already present

Task:
Implement inspectable lineage suggestions for imported conversations.

Required outcomes:
1. Create src/intelligence/continuity/lineage.py

2. Add a derived lineage suggestion model that can express:
   - continues
   - forks_from
   - revisits
   - supersedes

3. Suggestion heuristics may use:
   - temporal proximity
   - title overlap
   - keyword overlap
   - shared entities
   - explicit continuation keywords if present

4. Suggestions must be inspectable and non-authoritative.
   - never mutate canonical conversation rows
   - never silently assert lineage as truth

5. Add a minimal UI surface that says:
   - “This conversation may relate to…”
   - shows the top suggestions
   - makes clear that these are proposed links

6. Add tests for:
   - heuristic scoring
   - relation labeling
   - no mutation of canonical records

Strict rules:
- Work only on lineage suggestions.
- Do not revisit packet generation or bridge assembly.
- Do not add mem0.
- Keep the feature inspectable, explicit, and reversible.

Definition of done:
- the app can propose likely parent/related threads
- proposals are clearly derived suggestions
- tests pass
```

---

## Prompt 7 — Brand identity

```text
git checkout main && git pull
git checkout -b feature/brand-identity

Read:
- CLAUDE.md if present
- docs/product/visual-direction.md
- README.md
- ROADMAP.md

Task:
Create SoulPrint’s brand identity assets and formalize the visual system for the public face.

Required outcomes:
1. Create or update docs/product/brand.md with:
   - mission
   - one-liner
   - voice
   - palette
   - typography
   - logo usage rules

2. Create:
   - src/app/static/logo.svg
   - src/app/static/favicon.svg

3. Update src/app/templates/base.html to use logo + wordmark and favicon.

4. Keep the app calm and trustworthy.
   - no fantasy-software drift
   - no dashboard bloat
   - concentrate the glow only in meaning-bearing moments

Strict rules:
- Work only on brand identity assets and base chrome.
- Do not build the landing page in this task.
- Do not refactor unrelated templates or routes.
- Do not start desktop/freemium/wrapped work.

Definition of done:
- SoulPrint has a coherent brand guide, logo, and favicon
- base app branding is updated
- tests still pass
```

---

## Prompt 8 — Landing page

```text
git checkout main && git pull
git checkout -b feature/landing-page

Read:
- docs/product/brand.md
- docs/product/visual-direction.md
- README.md

Task:
Create a static landing page for SoulPrint.

Required outcomes:
1. Create landing/ with:
   - index.html
   - style.css
   - assets/

2. The landing page must communicate in 10 seconds:
   - what SoulPrint is
   - local-first trust
   - multi-provider import
   - provenance
   - exportability
   - the “what it is not” differentiation

3. Include sections for:
   - hero
   - product loop
   - what it is not
   - features
   - trust
   - email capture placeholder
   - footer

4. The public face should be lucid and premium.
   - obvious, not mystical
   - calm, not startup-flashy
   - dark hero + lighter product sections

Strict rules:
- Work only on landing/.
- Do not modify app routes or templates.
- Do not start desktop wrapper or monetization.
- Keep it static: no build system.

Definition of done:
- landing page works as a standalone static site
- communicates SoulPrint clearly and credibly
- existing app code remains untouched
```

---

## Prompt 9 — Desktop wrapper

```text
git checkout main && git pull
git checkout -b feature/desktop-app

Read:
- CLAUDE.md if present
- current app startup/run instructions

Task:
Create the minimal desktop wrapper for SoulPrint using PyWebView.

Required outcomes:
1. Create:
   - desktop/__init__.py
   - desktop/launcher.py
   - requirements-desktop.txt

2. launcher.py must:
   - start the Flask app in a daemon thread
   - use a free local port
   - disable reloader
   - open a PyWebView window titled “SoulPrint — Your AI Memory”

3. Add minimal docs for desktop mode.

4. Add tests that verify launcher importability and app startup compatibility.
   - do not test real window creation in CI

Strict rules:
- Work only on desktop packaging.
- Do not redesign the app.
- Do not add installer tooling beyond PyWebView.
- Do not start freemium or Wrapped work.

Definition of done:
- python -m desktop.launcher opens SoulPrint in a native window
- tests pass
```

---

## Prompt 10 — Freemium gate

```text
git checkout main && git pull
git checkout -b feature/freemium-gate

Read:
- README.md
- ROADMAP.md
- existing intelligence routes

Task:
Implement the local-only freemium gate.

Required outcomes:
1. Add local license validation using instance/license.key
2. Free tier keeps:
   - import
   - browse
   - passport
   - native memory
   - traces
   - summary/wrapped

3. Paid tier gates:
   - Ask
   - summaries/topics/digests
   - other intelligence-triggering actions

4. Add:
   - upgrade template/page
   - workspace tier badge
   - dev override env var for testing

Strict rules:
- Work only on licensing and feature gating.
- No server auth.
- No login/account flow.
- Do not change the free-tier experience into a crippled shell.
- Do not begin Wrapped implementation here.

Definition of done:
- free tier remains useful and complete
- paid intelligence features are gated locally
- tests pass
```

---

## Prompt 11 — Wrapped summary

```text
git checkout main && git pull
git checkout -b feature/wrapped-summary

Read:
- docs/product/brand.md
- docs/product/visual-direction.md
- current viewmodel patterns

Task:
Create SoulPrint’s shareable Wrapped summary page.

Required outcomes:
1. Add a summary/wrapped viewmodel that computes:
   - total conversations
   - total messages
   - provider breakdown
   - dominant provider
   - date range
   - most active month
   - longest conversation
   - topic highlights if available
   - average messages per conversation

2. Add GET /summary

3. Create a premium, screenshot-worthy summary template.
   - dark, cinematic, share-ready
   - still honest and provenance-aware
   - this is the strongest glow surface in the product

4. Keep /summary on the free tier.

5. Add tests for accuracy and graceful empty state rendering.

Strict rules:
- Work only on the Wrapped feature.
- Do not revisit licensing, landing, or desktop.
- Do not widen this into a full analytics dashboard.

Definition of done:
- /summary is visually strong enough to share
- stats are computed correctly from canonical data
- tests pass
```

## Final call

So the merged rule is simple:

**Spine first. Skin second.**
**Continuity packet before lineage.**
**Lineage before polish.**
**Then Claude’s five release PRs, one at a time.**  

If you want, next I’ll compress this into an even tighter **Phase 1-only pack**: just the first 4 prompts needed to ship the continuity MVP without the later launch work.
