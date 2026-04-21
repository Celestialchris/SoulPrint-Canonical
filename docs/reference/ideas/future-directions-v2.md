---
status: archive-only
authority: non-authoritative
active_truth:
  - README.md
  - ROADMAP.md
  - docs/product/
  - docs/specs/
---

# Future Directions (Archived Ideation)

> [!NOTE]
> **Archive-only ideation — non-authoritative.**
> This file preserves speculative product thinking for traceability.
> It is not current roadmap or doctrine.
> Active truth lives in `README.md`, `ROADMAP.md`, `docs/product/*`, and `docs/specs/*`.

---

## Desktop Packaging

The Flask + SQLite stack is straightforward to package as a desktop application. Three viable options, ordered by fit:

**Tauri** — Lightweight, uses the system's native webview, runs the Python backend as a sidecar process. Smallest bundle size. Aligns with the local-first, minimal-footprint identity.

**PyWebView** — Wraps the Flask app in a native window with minimal code. Less polished than Tauri but fastest to prototype. Suitable as a stepping stone.

**Electron** — Functional but heavy. Conflicts with the product identity of lightweight local-first tooling. Not recommended unless Tauri proves insufficient.

The drag-and-drop import flow is a UI layer over the existing CLI pipeline. The auto-detection system already handles all three providers. The desktop app would call `import_conversation_export_to_sqlite()` directly from a drop zone.

---

## Derived Intelligence Layer

The core architectural question: generate derived notes, summaries, topic extractions, and insights that live alongside canonical records — without replacing them.

This maps onto Layer C (Intelligence) extended into additional derived output types. The constraint already in doctrine: **derived content never replaces canonical records.**

### Derived artifact types

- **Per-conversation summaries** — Single-conversation distillation with key decisions and topics.
- **Cross-conversation topic threads** — Multi-conversation arcs across providers and time ranges.
- **Personal knowledge notes** — Synthesized preferences and decisions from multiple conversations.
- **Periodic digests** — Weekly or monthly rollups of conversation activity and substance.

### Provenance requirements

Every derived artifact carries: source conversation stable IDs, generation timestamp, LLM provider, prompt template version, and output text. Non-canonical. Clearly labeled. Traceable to source records. Same pattern as Answer Traces.

### LLM integration options

**Option A — Local models only (Ollama, llama.cpp).** Purest local-first choice. Nothing leaves the machine. Lower quality ceiling and hardware requirements limit audience.

**Option B — User-provided API key.** User connects their OpenAI/Anthropic/Google key. Conversation chunks sent to API, summaries stored locally as derived artifacts. Pragmatic middle ground. Requires transparency about data leaving the machine.

**Option C — Hybrid.** Local models for lightweight operations (topic extraction, keyword tagging), external API for heavy operations (long summaries, cross-conversation synthesis). User controls the boundary.

Recommendation: Option B as the starting point. Fastest to build, best result quality, and aligns with the existing BYOK configuration pattern.

---

## Codebase Structure for Intelligence Layer

```
src/
  intelligence/
    __init__.py
    summarizer.py      # per-conversation summaries
    threads.py         # cross-conversation topic detection
    digest.py          # periodic rollups
    notes.py           # user-facing derived notes
    store.py           # derived artifact persistence
```

This structure already exists in the codebase. Future expansion follows the same pattern.

---

## Suggested Build Sequence

**Phase A** — Desktop wrapper. Wrap current Flask app in PyWebView or Tauri. Add drag-and-drop import UI. Add visual summary dashboard.

**Phase B** — Intelligence layer. API key connection. Per-conversation summarizer. Derived artifact storage with provenance. UI integration alongside transcripts.

**Phase C** — Cross-conversation synthesis. Topic threads, periodic digests, personal knowledge extraction.

**Phase D** — Distribution polish. Installer packages, landing page, onboarding flow.
