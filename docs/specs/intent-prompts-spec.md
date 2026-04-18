# Intent Prompts — SoulPrint Spec v1

**Status:** Authoritative. All four blocking decisions committed 2026-04-18.
**UI label:** *Directive prompts* (per Section 6).
**Taxonomy:** Workflow-stage, seven values (Section 3, Option A).
**Curation model:** Strictly-derived prompts + first-class annotations keyed on canonical anchor (Section 7, Option 1).
**Trigger:** On-demand via explicit user action (Section 8, Step 7).

---

## 1. What Intent Prompts are

An Intent Prompt is a directive user message extracted from an imported conversation and surfaced as a reusable unit in SoulPrint's Interpretation section.

The underlying observation: when a user works with an AI over months, they develop a personal library of effective prompts — the ones that reliably produce the output they need. Those prompts are currently trapped inside conversation transcripts, reachable only by scrolling through the whole chat to find them. *Directive prompts* surfaces them as a browsable, filterable, curatable library.

The feature answers the user question: *"What prompts have I written that actually worked? Give me my own library."*

---

## 2. The three-axis model

Every Directive Prompt is positioned on three independent axes. Storing all three means the library supports multiple slice-and-dice views without reshaping the data.

**Stage** — the workflow phase the prompt belongs to. Assigned by the classifier (Section 4). See Section 3 for the taxonomy.

**Topic** — inherited from SoulPrint's existing topic clustering (the same mechanism that powers Recurring Themes and Topics on the Intelligence page). No new classifier; the topic a conversation already belongs to flows down to its prompts.

**Source** — canonical provenance. The stable ID of the `ImportedMessage` the prompt was extracted from, plus the `ImportedConversation` it lives in, plus the provider. A user viewing a prompt can one-click back to the original conversation to see what the prompt *did* — what the AI said in response, how the user refined it. This preserves SoulPrint's canonical/derived authority boundary: **source records remain canonical; prompt rows are derived; user annotations are first-class but keyed on the canonical anchor.**

---

## 3. Taxonomy — the stage axis (locked)

**Decision:** Option A — workflow-stage, seven closed values. Committed 2026-04-18.

### The seven values

A small closed set mirroring the OpenSpec flow already in use:

- **Explore** — "help me understand X," "what are the options for Y," "walk me through Z"
- **Propose** — "draft a plan for X," "give me three approaches to Y"
- **Apply** — "implement X," "write the code for Y," "execute this plan"
- **Archive** — "summarize what we decided," "save the key points"
- **Review** — "audit this for errors," "what did I miss," "critique this"
- **Ship** — "draft the commit message," "write the release notes," "prepare the handoff"
- **Other** — catch-all for messages that are directive but don't fit the above

Rationale: small closed set (seven values), mirrors a workflow the user already thinks in (OpenSpec), produces filters that map to real user intent, and lets the classifier commit to a specific label rather than free-text tagging.

### Rejected alternatives (recorded for traceability)

- **Structural-type** (Read Block, Objective, Scope Lock, Stop Condition). Rejected because it classifies by *form*, not *purpose*.
- **Domain** (Frontend, Database, Tests, Docs). Rejected because domain is already captured by the Topic axis (Section 2) via existing topic clustering.

---

## 4. Classifier approach

The classifier is a binary-plus-tag call on each user message in each imported conversation.

**Step 1 — directive vs. conversational.** For each `ImportedMessage` where `role == "user"`, the classifier asks: *is this a directive prompt (asking the AI to do something) or a conversational exchange (discussing, reacting, acknowledging)?* Directive messages proceed to Step 2; conversational messages are dropped.

**Step 2 — stage tagging.** For each directive message, the classifier assigns one of the seven workflow-stage values from Section 3.

**Model.** Gemma4 via Ollama, using the existing `LLMProvider` boundary with `openai-compat/gemma4` provider naming. Same infrastructure already powering Summaries and Digests. No new provider, no new dependencies.

**Prompt template.** Deterministic system prompt describing the taxonomy, few-shot examples for each stage, and strict output format (single token per message: one of `explore|propose|apply|archive|review|ship|other|conversational`). The `conversational` output is the Step-1 signal that this message shouldn't enter the library.

**Batching.** One LLM call per message for v1. If throughput becomes a bottleneck, consider a single-call-per-conversation pattern with structured JSON output. Flag for post-v1; do not prematurely complicate v1.

**Confidence.** Record as a simple enum (`high | medium | low`) based on whether the classifier's output matches the expected format exactly, includes hedging, or fell back to `other`. Low-confidence prompts still enter the library but display with a subtle indicator.

**Provenance.** Every prompt row stores: `source_message_id`, `source_conversation_id`, `provider`, `classifier_provider_name` (e.g., `openai-compat/gemma4`), `classifier_prompt_version`, `generated_at_unix`, `confidence`. Matches the Answer Trace provenance pattern.

---

## 5. Data model

Two tables. The split is the architectural point of this whole spec: **classifier output is strictly derived and recomputable; user annotations are first-class and keyed on the canonical anchor so they survive any rebuild.**

```sql
-- Strictly derived. Safe to DROP and rebuild anytime without losing user data.
CREATE TABLE intent_prompt (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- Canonical anchors (immutable)
  source_message_id INTEGER NOT NULL UNIQUE,    -- one prompt per source message
  source_conversation_id INTEGER NOT NULL,      -- denormalized for query speed
  provider TEXT NOT NULL,                       -- "chatgpt" | "claude" | "gemini" | "grok"
  prompt_text TEXT NOT NULL,                    -- the user message content, verbatim

  -- Classifier output
  stage TEXT NOT NULL,                          -- "explore" | "propose" | "apply" | ... | "other"
  topic_id INTEGER,                             -- FK to existing topic clustering (nullable)
  confidence TEXT NOT NULL,                     -- "high" | "medium" | "low"

  -- Classifier provenance
  classifier_provider_name TEXT NOT NULL,       -- e.g., "openai-compat/gemma4"
  classifier_prompt_version TEXT NOT NULL,
  generated_at_unix INTEGER NOT NULL,

  FOREIGN KEY (source_message_id) REFERENCES imported_message(id) ON DELETE CASCADE,
  FOREIGN KEY (source_conversation_id) REFERENCES imported_conversation(id) ON DELETE CASCADE
);

CREATE INDEX idx_intent_prompt_stage ON intent_prompt(stage);
CREATE INDEX idx_intent_prompt_topic ON intent_prompt(topic_id);
CREATE INDEX idx_intent_prompt_provider ON intent_prompt(provider);

-- First-class user annotations. Survives classifier rebuilds via canonical-anchor key.
CREATE TABLE intent_prompt_user_annotation (
  source_message_id INTEGER PRIMARY KEY,        -- canonical anchor; one annotation per source
  starred BOOLEAN NOT NULL DEFAULT 0,
  hidden BOOLEAN NOT NULL DEFAULT 0,
  user_note TEXT,
  created_at_unix INTEGER NOT NULL,
  updated_at_unix INTEGER NOT NULL,
  FOREIGN KEY (source_message_id) REFERENCES imported_message(id) ON DELETE CASCADE
);

CREATE INDEX idx_annotation_starred ON intent_prompt_user_annotation(starred) WHERE starred = 1;
CREATE INDEX idx_annotation_hidden ON intent_prompt_user_annotation(hidden) WHERE hidden = 1;
```

### Key design notes

- **`intent_prompt` is derived.** `DELETE FROM intent_prompt` is a safe operation — the classifier can rebuild every row from canonical data. This is the zero-cost "try a better classifier prompt" path.
- **`intent_prompt_user_annotation` is first-class** but stays small (one row per annotated prompt, keyed on the canonical anchor). It is **never** deleted during a classifier rebuild.
- **The join is always LEFT.** Query pattern: `intent_prompt p LEFT JOIN intent_prompt_user_annotation a ON p.source_message_id = a.source_message_id`. Missing annotations render as default (not starred, not hidden, no note).
- **Orphaned annotations are tolerated.** If a future classifier re-decides that message X is conversational (and therefore no `intent_prompt` row exists for it), the annotation persists. If a later classifier re-decides it *is* directive, the annotation reattaches automatically because the canonical key matches. No data loss in either direction.
- **`prompt_text` is denormalized into `intent_prompt`** so the list view can render without joining back to `imported_message`. It's technically redundant data but classifier output includes it as a side effect and the read-path win is real.
- **`ON DELETE CASCADE`** from `imported_message` for both tables. If a user deletes a conversation, prompts and annotations both go with it. The conversation-delete UI should warn: *"This will also delete N prompts and M annotations in your library."*

---

## 6. UI placement

New route `/prompts`. Navigation label in the sidebar's Interpretation section: **"Directive prompts"**.

The Interpretation section currently contains: Recurring themes, Create a digest, How answers were found. *Directive prompts* sits alongside these as a fourth interpretive surface over the imported archive.

**List view.** Table of prompts with columns for stage, topic, provider, prompt preview (truncated), starred indicator, and a link back to the source conversation. Filters on stage, topic, provider, and curation state (starred-only, hide-hidden). Search by prompt text via FTS5.

**Detail view.** Full prompt text, the AI's response (from the immediately following `assistant` message in the source conversation), provenance footer, "Copy prompt" button, "View in conversation" handoff link. User-editable controls: star toggle, hide toggle, notes textarea. (Stage is **not** user-editable in v1; if users need to re-categorize, that's the signal the classifier needs work, not that the row does. Flag for post-v1.)

**Empty state.** Clear language for a user with no classified prompts yet: *"Your prompt library is empty. Extract directive prompts from your imported conversations. This requires an LLM provider — local Ollama + Gemma 4 is recommended. See [LLM Configuration](../../CLAUDE.md#llm-configuration)."* Button labeled **"Build my prompt library"** triggers the classification batch.

**Partial-build state.** If some conversations have been classified and new ones have been imported since: *"N new conversations since your last scan. Extend your library?"* with a **"Scan new conversations"** button that runs the classifier only over the new messages.

**Rebuild option.** Advanced action tucked under a disclosure or settings page: *"Rebuild library from scratch"* — truncates `intent_prompt` and re-runs the full classifier. Annotations survive. For users who want to try a better classifier after a tuning round.

---

## 7. Curation model (locked: Option 1)

**Decision:** Strictly-derived `intent_prompt` table + separate `intent_prompt_user_annotation` table keyed on `source_message_id`. Committed 2026-04-18.

### What this buys

- **Zero-cost classifier rebuild.** `DELETE FROM intent_prompt; <run classifier>; INSERT ...` is safe. Annotations live in a different table and are untouched.
- **Preserved canonical/derived boundary.** Classifier output is derived and recomputable. User annotations are first-class, but they're keyed on a canonical anchor (the source message ID), which makes them structurally coupled to the ledger rather than to the derived layer.
- **Simpler mental model.** "Prompts are what the classifier says they are; annotations are what you say about them." Two tables, two purposes, no coupling between their lifecycles.

### The merge behavior (concrete)

- Running the classifier for the first time: INSERT new `intent_prompt` rows. No annotations exist yet.
- Running the classifier again after new conversations imported: INSERT new `intent_prompt` rows for messages that don't have one. Existing rows are untouched (idempotent by `UNIQUE(source_message_id)`).
- Running a *rebuild*: `DELETE FROM intent_prompt` first, then full re-classification. All existing annotations remain and reattach to new rows via the canonical key.
- User stars/hides/notes a prompt: UPSERT into `intent_prompt_user_annotation` keyed on `source_message_id`. Never touches `intent_prompt`.

### What does *not* change under this model

- `imported_message` and `imported_conversation` remain the canonical ledger.
- The classifier never writes to canonical tables.
- The user can never mutate `prompt_text` (the original user message as typed). If they want to say something different, they write a note.

---

## 8. Build sequence (for future Template H prompts)

One prompt per task. Small scope. Strict scope-lock. Merge between each.

1. **Migration.** Add `intent_prompt` and `intent_prompt_user_annotation` tables per Section 5. Test: tables exist, indexes present, `UNIQUE(source_message_id)` enforced on `intent_prompt`, `PRIMARY KEY` on `intent_prompt_user_annotation.source_message_id` works as an implicit unique constraint, `ON DELETE CASCADE` verified from both parent tables for both child tables.

2. **Classifier module.** Add `src/intelligence/intent_prompts.py`. Implement `classify_message(message_text: str) -> tuple[str, str]` returning `(stage_or_conversational, confidence)`. Unit test with fixture conversations covering all seven stages plus conversational examples. Mock the LLM provider; do not call Gemma4 in CI.

3. **Extraction engine.** Implement `extract_from_conversation(db, conversation_id) -> ExtractionResult`. Idempotent: INSERT new rows for messages that don't have one; skip existing. Test INSERT path and skip path. Verify no writes to annotation table.

4. **Rebuild function.** Implement `rebuild_library(db) -> RebuildResult`. Truncates `intent_prompt`, iterates all imported conversations, re-classifies. Test that annotations survive (fixture: add annotation, rebuild, assert annotation still queryable and rejoined correctly).

5. **Batch runner + CLI.** Add `python -m src.intelligence.intent_prompts build --db instance/soulprint.db`. Iterates unclassified conversations, reports counts. Add `... rebuild` for the full-rebuild path. Test with a three-conversation fixture including annotated rows surviving rebuild.

6. **Read API + view model.** Add query functions (list with LEFT JOIN on annotations, filter by stage/topic/provider/starred/hide-hidden, search by FTS5 on `prompt_text`) and a Flask view model following the `workspace.py` / `wrapped.py` pattern.

7. **List UI + on-demand trigger.** Add `/prompts` route and `prompts.html` template with list view, filters, and the **"Build my prompt library"** button on the empty state. Button triggers the batch runner as a background task with progress indicator. Pre-flight cost display: *"This will process ~N messages across ~M conversations."* On-demand only — not automatic on import.

8. **Detail view with annotation editing.** Single-prompt detail page with AI response, provenance, copy button, and three user-editable controls (star, hide, user_note). Edits persist via a PATCH endpoint that UPSERTs into `intent_prompt_user_annotation`. Verify annotation table stays independent of `intent_prompt`.

9. **Rebuild action (post-MVP polish).** Surface the rebuild function from Step 4 as a disclosed action on a settings page. Confirmation dialog: *"This will re-classify all N prompts in your library. Your stars, hides, and notes will be preserved."*

Each step is a merge-able PR on its own. Steps 1–3 can merge even before end-to-end works, because they're pure plumbing.

---

## 9. Why on-demand and not on-import

**Decision:** Classifier runs only on explicit user action. Committed 2026-04-18.

Rationale: a user installing SoulPrint may not yet have an LLM provider configured. Running the classifier automatically on import would either fail silently (bad), crash the import (very bad), or force the user to configure a provider before they can even see their archive (hostile first-run experience).

On-demand means: import always succeeds, the archive is always browsable, and the prompt library is an opt-in intelligence feature the user activates when they're ready. The empty-state messaging in Section 6 points them at the Ollama + Gemma 4 local setup when they reach that moment.

Post-v1, consider an opt-in setting: *"Automatically classify new imports"*, default off. Flag for post-v1; do not add to v1.

---

## 10. Locked decisions (previously blocking)

1. **Taxonomy:** Option A — workflow-stage, seven closed values (Explore, Propose, Apply, Archive, Review, Ship, Other).
2. **Curation model:** Option 1 — strictly-derived `intent_prompt` + first-class `intent_prompt_user_annotation` keyed on canonical `source_message_id`. Zero-cost rebuild preserved.
3. **UI label:** *Directive prompts* (route: `/prompts`).
4. **Classifier trigger:** On-demand only via the "Build my prompt library" button.

No further blocking decisions remain. Section 8 is ready to be executed as a series of Template H prompts for Claude Code.

---

## 11. What this spec does not cover

- Directive prompts for *native* (user-authored) memory entries. Defer to v2.
- Cross-user shared prompt libraries. Deferred indefinitely; conflicts with local-first principles.
- Editing of `prompt_text` itself. Intentionally disallowed per Section 5 design notes.
- Editing of `stage` by the user. Disallowed in v1 per Section 6; post-v1 may add this if usage signals it's needed.
- Export of the prompt library as a standalone file (JSON or markdown dump). Trivially addable once the tables exist; not v1.
- Automatic classification of new imports. Post-v1 opt-in setting per Section 9.
