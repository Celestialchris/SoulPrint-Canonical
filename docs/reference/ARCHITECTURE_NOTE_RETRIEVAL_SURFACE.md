# Architecture Note: Retrieval Surface (Current -> Near-Term)

## Current retrieval surface

SoulPrint currently exposes retrieval through two explicit surfaces:

1. **Native memory retrieval (web app)**
   - `GET /chats`
   - Reads `MemoryEntry` rows, newest-first, optional tag substring filter.

2. **Imported conversation retrieval (import/query module)**
   - `list_imported_conversations(sqlite_path, limit)`
   - `search_imported_conversations(sqlite_path, keyword, limit)`
   - `get_imported_conversation(sqlite_path, conversation_id)`
   - `export_imported_conversation_markdown(sqlite_path, conversation_id, output_path)`
   - CLI adapter: `src/importers/query_cli.py`

These are intentionally separate and preserve current Milestone 1 behavior.

## Evolution guidance (without premature architecture)

Near-term evolution should keep current storage untouched and improve retrieval ergonomics:

- Add a small retrieval boundary per lane (`native_read_service`, `imported_read_service`).
- Add one read-only federated endpoint/CLI mode that composes both lanes and labels provenance.
- Preserve canonical traceability in every row/result (`id`, lane/source, timestamps, source IDs when present).
- Keep markdown export as canonical human-auditable output for imported conversations.

## Guardrails

- Do not replace canonical SQLite truth with derived memory layers.
- Do not introduce mem0/RAG/agent orchestration in Milestone 1 retrieval work.
- Do not merge interpretive context into retrieval contracts.
