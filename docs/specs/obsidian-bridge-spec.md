# SoulPrint Obsidian Bridge — v1 Spec

*One-way export from SoulPrint's canonical ledger to an Obsidian-native vault.*

---

## What the Bridge Does

The Obsidian Bridge reads canonical conversations and derived intelligence from SoulPrint, then renders them as structured markdown notes in an Obsidian vault. It is a **derived, read-only export layer** — same authority rules as Memory Passport. SoulPrint stays canonical. Obsidian is the thinking interface.

If the vault is deleted, the bridge rebuilds it from SoulPrint.

## What the Bridge Is Not

- Not bidirectional sync (v1 is strictly SoulPrint → Obsidian)
- Not a live watcher or daemon (run manually via CLI)
- Not a replacement for the web UI (the transcript explorer stays for full-text browsing)
- Not dependent on any Obsidian plugin (works with vanilla Obsidian)

---

## Design Principles (from Stefango/Kepano's system)

1. **File over app.** Plain markdown. If Obsidian disappears, the files survive.
2. **Near-flat structure.** Minimal folders. Organization through frontmatter properties and categories, not deep folder trees.
3. **Categories as the spine.** Category notes use Obsidian bases (Dataview-like smart tables) to list related notes. No manual index maintenance.
4. **Link everything on first mention.** The bridge emits wiki-links to themes, providers, and related conversations — even if those target notes don't exist yet. Backlinks do the rest.
5. **Templates are composable.** Each note type has a template. Multiple templates can stack on one note.
6. **Daily notes as temporal anchors.** Daily notes exist to receive backlinks via the `created` property. The bridge doesn't write into them.

---

## Vault Layout

```
<vault>/
    Chats/                          ← one note per conversation
        <provider>--<conv-id>.md
    Themes/                         ← one note per detected topic
        <topic-label>.md
    References/                     ← provider notes, concept stubs
        ChatGPT.md
        Claude.md
        Gemini.md
    Daily/                          ← auto-generated daily notes (empty shells)
        YYYY-MM-DD.md
    Templates/                      ← Obsidian templates (exported by bridge)
        chat.md
        theme.md
        daily.md
    Attachments/                    ← reserved for future use
    .obsidian/                      ← vault config (generated on first export)
```

Notes:
- `Chats/` is the only conversation folder. Keeps root clean for the user's own manual notes.
- `Themes/` contains intelligence-derived notes, not empty stubs.
- `References/` holds things "outside the user's world" per Stefango's rule.
- `Daily/` notes are created as empty shells. Obsidian's backlinks panel fills them.
- Everything except `.obsidian/` is plain markdown. Portable forever.

### File naming

Chat notes: `chatgpt--142.md` (provider, double-dash, SoulPrint conversation ID).

Theme notes: `retrieval-architecture.md` (slugified topic label).

Daily notes: `2026-03-22.md` (ISO date).

Provider refs: `ChatGPT.md`, `Claude.md`, `Gemini.md`.

No date prefixes on chat notes. Dates live in frontmatter where Obsidian can query them.

---

## Note Types and Frontmatter

### Chat Note

The primary export unit. **Not the raw transcript.** The note contains the intelligence layer's output — summary, decisions, open loops, entity mentions — plus a header linking back to the full transcript in SoulPrint's web UI.

```yaml
---
type: chat
source: soulprint
stable_id: "imported_conversation:142"
provider: "[[ChatGPT]]"
lane: imported
title: "Retrieval architecture for federated search"
created: "[[2026-03-22]]"
updated: 2026-03-22T18:30:00Z
categories:
  - "[[Chat]]"
tags:
  - chat
  - imported
  - chatgpt
render_version: 1
soulprint_url: "http://127.0.0.1:5678/imported/142/explorer"
---
```

Body structure:

```markdown
# Retrieval architecture for federated search

> **Provider:** [[ChatGPT]] · **Messages:** 47 · **Created:** [[2026-03-22]]

<!-- SOULPRINT:BEGIN AUTO -->

## Summary
{derived summary text, if exists}

## Key Decisions
{from continuity artifact type=decisions, if exists}

## Open Loops
{from continuity artifact type=open_loops, if exists}

## Entities
{from continuity artifact type=entity_map, if exists}

## Related Conversations
- [[chatgpt--138]] — continues (title overlap: retrieval, federated)
- [[claude--45]] — forks_from (shared content keywords)

## Themes
- [[Retrieval Architecture]]
- [[Federated Search]]

<!-- SOULPRINT:END AUTO -->
```

Notes:
- The `<!-- SOULPRINT:BEGIN AUTO -->` block is regenerable. The bridge overwrites only this block on re-export.
- Content above or below the block is user-owned and survives re-export.
- If no intelligence data exists (no summary, no continuity), the note still exports with the header and a "No intelligence data yet" note. The bridge works without BYOK keys — it just produces thinner notes.
- Related conversations come from the lineage engine. Wiki-links use the filename format so Obsidian resolves them.
- Theme links come from the latest topic scan's clusters.

### Theme Note

Generated from topic scan clusters + digests. Not empty stubs — they carry synthesized content.

```yaml
---
type: theme
source: soulprint
topic_label: "Retrieval Architecture"
categories:
  - "[[Theme]]"
confidence: high
conversation_count: 7
render_version: 1
---
```

Body:

```markdown
# Retrieval Architecture

<!-- SOULPRINT:BEGIN AUTO -->

## Digest
{digest_text from DerivedDigest for this topic, if exists}

## Conversations
- [[chatgpt--142]] — Retrieval architecture for federated search
- [[chatgpt--138]] — Lane-aware search design
- [[claude--45]] — Federated retrieval boundary

<!-- SOULPRINT:END AUTO -->
```

If no digest exists for a topic, the Theme note still lists its conversations. The digest section says "Run a digest in SoulPrint to populate this section."

### Daily Note

Empty shell. Exists so `created: "[[2026-03-22]]"` in chat notes resolves to a real file.

```yaml
---
type: daily
date: 2026-03-22
---
```

Body: empty. Obsidian's backlinks panel shows every chat note created that day.

### Provider Reference Note

One per provider. Exists so `provider: "[[ChatGPT]]"` resolves.

```yaml
---
type: provider
provider_id: chatgpt
---
```

Body:

```markdown
# ChatGPT

Conversations imported from OpenAI's ChatGPT export.

<!-- SOULPRINT:BEGIN AUTO -->
**Conversation count:** 882
<!-- SOULPRINT:END AUTO -->
```

Backlinks automatically show every chat note from that provider.

### Category Notes

`Chat.md` and `Theme.md` sit in root. Each contains a simple Obsidian base/dataview query.

Chat.md:
```markdown
---
type: category
---
# Chats
```dataview
TABLE provider, created, title
FROM "Chats"
SORT created DESC
```​
```

Theme.md:
```markdown
---
type: category
---
# Themes
```dataview
TABLE conversation_count, confidence
FROM "Themes"
SORT conversation_count DESC
```​
```

Note: Dataview queries require the Dataview community plugin. If the user doesn't have it, the notes still work — the query text is visible but inert. The bridge does NOT require Dataview; it's a recommendation.

---

## Data Flow

```
ImportedConversation (canonical DB)
    + DerivedSummary (JSONL)
    + ContinuityArtifact [summary, decisions, open_loops, entity_map] (JSONL)
    + TopicScan clusters (JSONL)
    + DerivedDigest (JSONL)
    + LineageSuggestion (computed at export time)
    ↓
    renderer.py
    ↓
    Obsidian markdown notes with frontmatter + wiki-links
    ↓
    exporter.py → writes to vault path
```

The bridge reads from:
- SQLite: `ImportedConversation`, `ImportedMessage` (for message count, dates, titles)
- `instance/derived_summaries.jsonl`
- `instance/continuity_artifacts.jsonl`
- `instance/topic_scans.jsonl`
- `instance/derived_digests.jsonl`
- Lineage engine: called at export time per conversation

It writes to:
- The target vault directory (specified by `--vault` flag)

---

## CLI Interface

```bash
# Full export — all conversations, themes, daily notes, provider refs, config
python -m src.obsidian.cli export \
    --db instance/soulprint.db \
    --vault /path/to/ObsidianVault

# Export only new conversations (not yet in vault)
python -m src.obsidian.cli export \
    --db instance/soulprint.db \
    --vault /path/to/ObsidianVault \
    --incremental

# Refresh intelligence data in existing notes (re-render AUTO blocks)
python -m src.obsidian.cli refresh \
    --db instance/soulprint.db \
    --vault /path/to/ObsidianVault

# Dry run — show what would be created/updated without writing
python -m src.obsidian.cli export \
    --db instance/soulprint.db \
    --vault /path/to/ObsidianVault \
    --dry-run
```

Output:

```
Exported 882 chat notes to Chats/
Generated 23 theme notes in Themes/
Created 147 daily notes in Daily/
Created 3 provider references in References/
Written .obsidian/ config (templates, daily notes, appearance)

Done. Open /path/to/ObsidianVault in Obsidian.
```

---

## Incremental and Overwrite Behavior

### New conversations
If a chat note file does not exist in the vault, create it.

### Existing conversations (re-export)
If the file exists:
1. Read the file
2. Find `<!-- SOULPRINT:BEGIN AUTO -->` and `<!-- SOULPRINT:END AUTO -->` markers
3. Replace only the content between markers with fresh rendered data
4. Preserve everything outside the markers (user's own annotations)
5. If markers don't exist (user deleted them), skip the file and log a warning

### Theme notes
Same marker-based overwrite. Digest text and conversation lists refresh. User annotations outside markers survive.

### Daily notes
Never overwritten. Created once if missing.

### Provider notes
Conversation count in AUTO block refreshes. User content survives.

### .obsidian/ config
Created on first export only. Never overwritten (user customizes their Obsidian settings).

---

## .obsidian/ Configuration (Generated)

The bridge generates a minimal `.obsidian/` folder on first export:

- `app.json` — sets attachment folder to `Attachments/`
- `daily-notes.json` — sets daily note folder to `Daily/`, format `YYYY-MM-DD`
- `templates.json` — sets template folder to `Templates/`
- `appearance.json` — dark theme default (matches Torchlit Vault)
- `community-plugins.json` — empty array (Dataview recommended but not required)

This gives the user a working vault on first open. They can customize freely after.

---

## Module Structure

```
src/obsidian/
    __init__.py
    cli.py          ← CLI entry point (argparse)
    renderer.py     ← takes canonical + intelligence data → markdown strings
    exporter.py     ← writes rendered notes to vault, handles incremental
    config.py       ← generates .obsidian/ config files
```

No new dependencies. Uses only stdlib + existing SoulPrint modules.

---

## What the Bridge Does NOT Do (v1)

- No Obsidian → SoulPrint sync
- No file watcher or auto-import trigger
- No Obsidian plugin dependency
- No NER / entity detection beyond what continuity already provides
- No embedding or vector search in the vault
- No custom Obsidian CSS/theme generation
- No dream/substance/archetype note types

---

## Test Plan

```
tests/test_obsidian_renderer.py
    - Chat note renders with correct frontmatter fields
    - Chat note without intelligence data renders thin but valid
    - Theme note renders with digest text when available
    - Theme note renders conversation list without digest
    - Daily note renders as empty shell with date
    - Provider note renders with conversation count
    - Lineage suggestions become wiki-links with correct filenames
    - Topic clusters become theme wiki-links
    - AUTO markers present in all generated notes
    - Markdown is valid (no broken frontmatter)

tests/test_obsidian_exporter.py
    - Full export creates expected directory structure
    - Incremental export skips existing files
    - Refresh overwrites only AUTO block content
    - User annotations outside AUTO block survive refresh
    - Missing markers → file skipped with warning
    - Dry run creates no files
    - .obsidian/ config created on first export only
    - .obsidian/ config not overwritten on re-export
    - Empty database produces empty vault with config only

tests/test_obsidian_cli.py
    - export subcommand works with valid args
    - refresh subcommand works
    - --dry-run flag respected
    - --incremental flag respected
    - Missing --vault arg errors clearly
    - Missing --db arg errors clearly
```

---

## Done Criteria

The bridge is done when:

1. `python -m src.obsidian.cli export --db instance/soulprint.db --vault /tmp/test-vault` produces a vault that opens in Obsidian without errors
2. Chat notes display summaries, decisions, open loops, lineage links, and theme links from existing intelligence data
3. Theme notes contain digest text and conversation backlinks
4. Daily notes accumulate backlinks from chat notes via the `created` property
5. Provider notes accumulate backlinks from their conversations
6. Re-running export preserves user annotations outside AUTO blocks
7. All tests pass
8. No new dependencies added
