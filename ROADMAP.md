# Roadmap

## Active

### Phase 1 — Repo Face Cleanup
Stratify docs, add LICENSE/CONTRIBUTING/CHANGELOG, CI workflow. No runtime changes.

### Phase 2 — README & Docs Alignment
Rewrite README to reflect current product state. Update docs to match post-cleanup paths.

### Phase 3 — Workspace Polish
Import UI surface, empty state refinements, visual polish pass.

### Phase 4 — Import UI
Web-based import flow for supported providers (ChatGPT, Claude, Gemini).

## Deferred

- **In-app Ask** — web answering surface (currently CLI-only)
- **Passport surface** — web UI for export/validate (currently CLI-only)
- **Derived intelligence** — topic clustering, conversation summaries, "what have I explored?" views
- **UI polish** — spacing, typography, mobile-friendliness
- **Growth** — additional provider importers, community contributions

## Explicitly removed

- Portable data-root / USB / capsule framing
- Desktop packaging (Tauri, Electron, PyWebView)
- mem0 activation (adapter exists, gated off by design)
