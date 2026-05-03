# Session Attachments Spec

> **Status (2026-04-27):** Phases 1 through 4 shipped. Asset ledger,
> conversation-level attachments, message-level attachments, and
> attachment-aware export bundles are in production. The "Current
> state" section below documents the pre-implementation state and is
> preserved as design history. Verify against `src/app/models/__init__.py`
> and `src/app/__init__.py` for current shape. Session logs covering
> Implementation status: partially shipped across April 2026 attachment/export work. Private session logs are maintained outside the public distribution tree.

Target path in repo: `docs/specs/session-attachments-spec.md`
Scope: product and architecture spec only. No implementation in this branch.

## Purpose

SoulPrint currently preserves conversations, derived intelligence, Obsidian exports, handoffs, and continuity artifacts. The missing limb is artifact custody: files that were part of a conversation should travel with that conversation without turning the SQLite database into file storage.

This spec defines how SoulPrint should support session attachments, message-bound attachments, and later project state snapshots while preserving the current local-first, provenance-first architecture.

## Current state

Verified against the uploaded `SoulPrint-Canonical-main.zip` used for this review.

- `src/app/models/__init__.py` currently defines `MemoryEntry`, `ImportedConversation`, `ImportedMessage`, and `ImportRun`. There is no asset, conversation-asset, or message-asset model yet.
- `ImportedConversation.messages` already orders messages by `ImportedMessage.sequence_index`, which gives a stable transcript spine for turn-bound attachment placement.
- `src/app/__init__.py` contains `render_conversation_markdown(conversation, messages)`, which emits text-only markdown with conversation metadata, messages, timestamps, and separators.
- `/imported/<int:conversation_id>/export` and `/imported/export-selected` both call `render_conversation_markdown(...)` for markdown export.
- `SOULPRINT_EXPORT_DIR` currently controls whether single and multi-conversation markdown exports write to an Obsidian/raw-style directory or fall back to browser download/zip mode.
- Existing export tests live in `tests/test_conversation_export.py` and `tests/test_multi_select_export.py`.
- Current attachment-related test names in export tests refer to HTTP `Content-Disposition: attachment`, not user-uploaded conversation files.

## Product principle

A SoulPrint conversation is not just text. It can be:

```text
conversation = messages + artifacts + relationships + provenance
```

The file itself is evidence. The database should remember that the evidence exists, where it lives, how it relates to the conversation, and whether it has been exported. The database must not carry the binary weight.

## Core law

```text
SQLite stores metadata and relationships.
The filesystem stores bytes.
SHA256 proves identity.
The manifest proves context.
Markdown preserves human-readable placement.
Derived intelligence interprets later.
```

## Non-goals for the MVP

Do not include these in the first implementation branch:

- PDF text extraction
- DOCX parsing
- XLSX sheet extraction
- OCR
- image captioning
- embeddings over attachments
- RAG over attachments
- automatic zip unpacking
- repo-diff intelligence
- cloud sync
- mem0/OpenBrain integration
- storage of file bytes inside SQLite BLOB columns

The first implementation should preserve and link files. Parsing and interpretation come later.

## Storage model

### Filesystem storage

Attachments should be content-addressed by SHA256 under the app instance directory.

Recommended layout:

```text
instance/
  assets/
    sha256/
      ab/
        abcdef123456...original-or-safe-name.ext
      9f/
        9f88c2...screenshot.png
```

Rules:

- Compute SHA256 before committing the asset row.
- Store a physical file only once per SHA256.
- Re-uploading the same bytes creates a new relationship row, not a duplicate file.
- Preserve the original filename in metadata.
- Use a safe stored filename on disk.
- Never trust the browser-provided MIME type alone. Store it, but treat extension and content sniffing as future validation concerns.

### SQLite schema

Initial models:

```text
Asset
  id
  stable_id
  sha256
  original_filename
  stored_filename
  mime_type
  extension
  size_bytes
  storage_path
  uploaded_at_unix
  source
  parse_status
  parse_error
```

```text
ConversationAsset
  id
  conversation_id
  asset_id
  role
  note
  attached_at_unix
```

```text
MessageAsset
  id
  message_id
  asset_id
  placement
  caption
  attached_at_unix
```

Recommended relationships:

- `ConversationAsset.conversation_id` references `ImportedConversation.id`.
- `MessageAsset.message_id` references `ImportedMessage.id`.
- Both relationship tables reference `Asset.id`.
- Deleting an imported conversation should remove relationship rows, but should not delete the underlying asset bytes if another relationship still references the same asset.
- A later cleanup command can identify orphaned assets.

### Why both conversation and message relationships exist

Some files belong to the whole conversation:

```text
Here is the repo zip for this debugging session.
```

Other files belong to one exact turn:

```text
Analyze this screenshot.
```

Those are different memories. The schema should preserve the difference from the beginning.

## Attachment classes

### Conversation-level attachment

Use when a file belongs to the session as a whole.

Examples:

- repo zip used as context for the whole thread
- research PDF pack
- notes bundle
- source archive

### Message-level attachment

Use when a file was uploaded with or belongs to one message.

Examples:

- screenshot attached to a user turn
- PDF referenced in a specific question
- DOCX draft attached for review

### Project-level snapshot, later

Large repeated artifacts such as repo zips should eventually become project snapshots rather than normal conversation attachments.

This is a separate spec or later extension:

```text
ProjectSnapshot
  id
  project_id
  branch
  commit_sha
  tree_hash
  zip_asset_id
  manifest_path
  created_at_unix
```

Do not build this in the first session-attachments branch. Keep the concept visible so repo zips do not distort the message-attachment model.

## Export behavior

### Markdown transcript placement

Message-level attachments should render under the exact message where they belong.

Example:

```markdown
### User
*2026-04-25T10:02:35Z*

Can you analyze this screenshot?

#### Attachments

- ![[Dream Summit Discovery.assets/msg-017-screenshot.png]]
- [[Dream Summit Discovery.assets/msg-017-report.pdf]]

---
```

Conversation-level attachments should render near the top after metadata.

Example:

```markdown
## Attachments

| File | Type | SHA256 | Placement |
|---|---|---|---|
| [[Dream Summit Discovery.assets/repo.zip]] | application/zip | abc123... | conversation |
```

### Obsidian directory export

When `SOULPRINT_EXPORT_DIR` points to a directory, export should eventually write:

```text
raw/
  Dream Summit Discovery.md
  Dream Summit Discovery.assets/
    manifest.json
    msg-017-screenshot.png
    msg-017-report.pdf
    repo.zip
```

The markdown file remains readable without opening the assets folder. The assets folder preserves evidence.

### Browser download export

When `SOULPRINT_EXPORT_DIR` is unset, a conversation with attachments should eventually export as a zip bundle:

```text
Dream Summit Discovery.zip
  Dream Summit Discovery.md
  Dream Summit Discovery.assets/
    manifest.json
    msg-017-screenshot.png
```

A conversation without attachments may continue to download as a plain `.md` file for backward compatibility.

### Multi-select export

For multi-select export, each conversation should retain its own sibling assets directory inside the zip or configured export directory.

Example zip layout:

```text
soulprint-export-2.zip
  Conversation A.md
  Conversation A.assets/
    manifest.json
    msg-002-image.png
  Conversation B.md
  Conversation B.assets/
    manifest.json
    source.pdf
```

Avoid a shared global `assets/` folder in export bundles because it weakens human inspection and makes copied files harder to understand.

## Manifest format

Each `.assets/manifest.json` should describe the exported assets and their relationship to the transcript.

Minimal shape:

```json
{
  "schema": "soulprint.attachments.v1",
  "conversation_id": 123,
  "source": "chatgpt",
  "source_conversation_id": "external-provider-id",
  "title": "Dream Summit Discovery",
  "exported_from": "SoulPrint",
  "assets": [
    {
      "asset_id": 1,
      "stable_id": "asset:sha256:abcdef...",
      "sha256": "abcdef...",
      "original_filename": "screenshot.png",
      "stored_filename": "msg-017-screenshot.png",
      "mime_type": "image/png",
      "size_bytes": 2481931,
      "relationship": "message",
      "message_id": 17,
      "message_sequence_index": 17,
      "role": "user",
      "placement": "after_message_content",
      "caption": ""
    }
  ]
}
```

Rules:

- Manifest should be deterministic enough for tests.
- Manifest should not contain absolute machine paths.
- Manifest should include SHA256 for each asset.
- Manifest should distinguish conversation-level and message-level relationships.
- Manifest should be useful to Claude Code, Codex, Obsidian, and future tools without requiring database access.

## UI behavior

### MVP UI: conversation-level only

First UI branch should add a simple attachment block on the conversation explorer page:

```text
Attachments
[Attach file]
- screenshot.png · image/png · 241 KB
- repo.zip · application/zip · 82 MB
```

Actions:

- upload attachment to conversation
- view/download attachment
- show duplicate reuse notice when hash already exists

### Later UI: message-level attach

After conversation-level attachments are stable, allow attaching files to a specific message from the explorer.

Possible UI:

```text
Message actions:
[Clip to notes] [Attach file]
```

The message-level UI must make placement visible. A user should be able to tell exactly which turn owns a file.

## Service boundary

Create a small service module rather than putting storage logic directly inside route handlers.

Recommended module:

```text
src/app/assets.py
```

Possible functions:

```text
store_asset(file_stream, original_filename, mime_type) -> Asset
attach_asset_to_conversation(conversation_id, asset_id, role="context", note="") -> ConversationAsset
attach_asset_to_message(message_id, asset_id, placement="after_message_content", caption="") -> MessageAsset
list_conversation_assets(conversation_id) -> list[...]
list_message_assets(message_ids) -> dict[int, list[...]]
copy_assets_for_export(conversation, export_target_dir, assets_by_message) -> manifest dict
```

Keep filesystem operations isolated behind this service so tests can exercise storage without a full browser route.

## Security and safety rules

- Never write uploaded files using the original filename directly.
- Strip path separators and unsafe characters from stored filenames.
- Do not allow `../` traversal through filenames.
- Do not expose absolute local storage paths in exported markdown or manifests.
- Add upload size limits before broad UI exposure. The exact limit can be configured later.
- Treat MIME type as user-controlled metadata until validated.
- Do not execute, unpack, or parse uploaded files in the MVP.
- Do not auto-open uploaded files server-side.

## Testing plan

### Phase 1 tests: schema and storage service

- Asset model exists after `db.create_all()`.
- Storing a file computes SHA256.
- Same file uploaded twice creates one physical file.
- Same file can be linked to two conversations.
- Database stores metadata only, not bytes.

### Phase 2 tests: conversation-level attachments

- Upload route attaches file to conversation.
- Explorer page lists conversation attachments.
- Missing conversation returns 404.
- Duplicate file upload reuses existing asset row or at least existing physical file, depending on chosen implementation.
- Delete imported conversation removes relationship rows without deleting shared asset bytes.

### Phase 3 tests: message-level attachments

- File can be attached to a specific `ImportedMessage`.
- Explorer renders attachment under the correct message.
- Markdown export renders attachment under the correct message.
- Attachment does not appear under neighboring messages.

### Phase 4 tests: export bundles

- Directory export writes `.md` plus sibling `.assets/` folder.
- `manifest.json` exists.
- Image assets use Obsidian embed syntax in Obsidian mode.
- Non-image assets use normal Obsidian link syntax.
- Browser download switches to zip bundle when attachments exist.
- Plain markdown behavior remains unchanged when no attachments exist.

## Implementation phases

### Phase 0: Commit this spec

Docs only.

Target file:

```text
docs/specs/session-attachments-spec.md
```

No app behavior changes.

### Phase 1: Schema and content-addressed storage service

Add models and storage service. No UI yet.

Expected files:

```text
src/app/models/__init__.py
src/app/assets.py
tests/test_assets.py
```

No changes to export routes yet unless needed for import safety.

### Phase 2: Conversation-level attachments UI

Add upload and listing on the conversation explorer.

Expected files:

```text
src/app/__init__.py
src/app/templates/imported_explorer.html
tests/test_conversation_assets_route.py
```

Avoid CSS changes unless absolutely necessary. Use existing UI patterns.

### Phase 3: Message-level attachments

Add the true missing limb: attach to exact message.

Expected files:

```text
src/app/__init__.py
src/app/templates/imported_explorer.html
tests/test_message_assets_route.py
tests/test_conversation_export.py
```

### Phase 4: Export bundles and manifest

Extend markdown export and Obsidian/raw directory export to copy assets beside transcript.

Expected files:

```text
src/app/__init__.py
src/app/assets.py
tests/test_conversation_export.py
tests/test_multi_select_export.py
```

This is the first phase where download behavior may need to branch between `.md` and `.zip`.

### Phase 5: Project State Capsules, separate spec

Do not mix into session attachments. Create a separate project-aware spec once basic attachments work.

## Open questions

These should be decided before implementation, but they do not block committing the spec.

1. Should duplicate assets reuse the same `Asset` row or create separate `Asset` rows pointing to the same SHA256 file? Recommendation: one `Asset` row per SHA256, many relationship rows.
2. What is the initial upload size limit? Recommendation: conservative default with config override.
3. Should assets be deleted when their last relationship is removed? Recommendation: no automatic deletion in MVP. Add explicit cleanup later.
4. Should message-level upload UI ship before conversation-level upload UI? Recommendation: no. Conversation-level first, message-level second.
5. Should historical imports attempt to recover provider-hosted file attachments? Recommendation: no. Only preserve files SoulPrint actually receives.

## Acceptance criteria for the full feature

The feature is complete when:

- A user can attach a file to a conversation.
- A user can attach a file to a specific message.
- Uploaded bytes are stored on disk, not in SQLite.
- Duplicate uploads are deduplicated by SHA256 at the storage layer.
- Explorer displays attachments in the right place.
- Markdown export preserves message-level placement.
- Obsidian/raw export writes a sibling `.assets/` folder and `manifest.json`.
- Exports remain readable even if assets are ignored.
- Existing text-only conversations export exactly as before unless attachments exist.

## Naming

Do not call this feature merely "file upload" in product language.

Preferred internal names:

- Session Attachments
- Turn-Bound Evidence
- Conversation Evidence Pack

Preferred user-facing language:

- Attach files to this conversation
- Attach files to this message
- Export with evidence

Avoid mystical labels in UI. Keep product language calm and legible.
