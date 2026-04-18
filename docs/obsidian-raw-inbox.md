# SoulPrint ↔ Obsidian — The Raw Inbox Bridge

**What this is.** A simple, one-way pipeline that drops your AI conversations as plain markdown files into an Obsidian vault's `raw/` inbox, where the vault's own librarian (an LLM agent guided by your vault's `CLAUDE.md` or `AGENTS.md`) decides how to file, tag, cross-link, and compile them into structured notes.

**Who this is for.** You already run an Obsidian vault with a librarian workflow — probably a [Kepano-style](https://github.com/kepano/kepano-obsidian) setup where content lives in `References/` and categories are assigned via frontmatter. You want your ChatGPT, Claude, Gemini, and Grok conversations flowing into that system so your vault's compile pass picks them up alongside web clips, book notes, and meeting notes.

**If you just want to look at your conversations inside SoulPrint, skip this doc.** This is only for people wiring SoulPrint into a larger knowledge-management stack.

---

## The two Obsidian paths in SoulPrint

SoulPrint has two distinct ways to hand data to Obsidian. Know which one you want.

| Path | What it does | When to use |
|------|--------------|-------------|
| **Structured Bridge** (`src/obsidian/`, CLI) | Renders opinionated structured notes with themes, daily anchors, and SoulPrint-specified layout. Writes into a dedicated vault path with SoulPrint's schema. | You want SoulPrint to dictate structure. You don't have your own librarian rules. |
| **Raw Inbox** (this doc) | Drops plain markdown conversation transcripts into your vault's `raw/` inbox. Your vault's own rules decide what happens next. | You have your own vault conventions (Kepano, ACCESS, PARA, whatever) and want SoulPrint to feed them without imposing structure. |

The rest of this doc is about the Raw Inbox path. For Structured Bridge, see [`docs/specs/obsidian-bridge-spec.md`](specs/obsidian-bridge-spec.md).

---

## Quick start (3 steps)

### 1. Point SoulPrint at your vault's `raw/` directory

Set the `SOULPRINT_EXPORT_DIR` environment variable to the absolute path of your vault's inbox directory.

**Windows (PowerShell, permanent via user env):**

```powershell
[Environment]::SetEnvironmentVariable(
  "SOULPRINT_EXPORT_DIR",
  "C:\Users\chr\Obsidian-Vault\kepano-obsidian-main\raw",
  "User"
)
```

Restart your terminal after setting. Verify with `echo $env:SOULPRINT_EXPORT_DIR`.

**macOS / Linux (`~/.zshrc` or `~/.bashrc`):**

```bash
export SOULPRINT_EXPORT_DIR="$HOME/Obsidian-Vault/kepano-obsidian-main/raw"
```

### 2. Export conversations from SoulPrint

Two ways, both respect `SOULPRINT_EXPORT_DIR` when set:

- **Single conversation.** Open any conversation in the transcript explorer, click "Export as markdown." The file lands in `raw/`.
- **Bulk.** Go to `/imported`, tick the conversations you want, click "Export selected." All files land in `raw/` as individual `.md` files.

When `SOULPRINT_EXPORT_DIR` is unset or invalid, SoulPrint falls back to browser downloads automatically. No breakage for users who haven't configured the bridge.

### 3. Let your vault's librarian compile

In Obsidian (or via Claude Code pointed at the vault), run your compile workflow. For a Kepano vault following the conventions in your vault's `CLAUDE.md`, that means: "compile" → the librarian reads every file in `raw/`, extracts key exchanges, writes a compiled note into `References/` with proper frontmatter, topics as wiki-links, and cross-references to existing notes.

The raw file stays in `raw/` after compile. It's the source of truth for the full transcript. The `References/` note is the distilled, cross-linked version your knowledge base actually uses.

---

## What SoulPrint writes

Every export is a single `.md` file with two parts: a metadata block and the transcript.

### Filename convention

```
<slug-of-conversation-title>.md
```

Slug rules:

- lowercase ASCII, hyphens instead of spaces
- dots in the title preserved (`my.notes.v2` → `my.notes.v2.md`)
- non-ASCII and punctuation stripped
- on collision with an existing file in `raw/`, SoulPrint appends the conversation's stable ID: `<slug>-<id>.md`

You will not get filename conflicts silently overwriting your data. Collisions always disambiguate.

### File contents

```markdown
# <Conversation title>

**Provider:** chatgpt
**Created:** 2026-03-14T09:22:41Z
**Updated:** 2026-03-14T11:05:12Z
**Messages:** 47
**Exported from:** SoulPrint v0.7.0-alpha.1 · conversation_id=142

---

### User · 2026-03-14T09:22:41Z

[first message content]

### Assistant · 2026-03-14T09:23:02Z

[first response content]

... (full transcript in order, message by message)
```

The metadata block is machine-readable (colon-delimited key-value pairs, first 6 lines after the H1). Your librarian can parse it deterministically to extract provider, date, and stable ID.

### What's NOT in the export

- No summaries, topics, or derived content. Those are SoulPrint's internal intelligence layer; the raw export is canonical-only.
- No embeds, attachments, or images. SoulPrint's canonical ledger is text-first; if a conversation referenced an image URL, the URL appears in the message content verbatim but no image is downloaded or embedded.
- No cross-references to other SoulPrint conversations. Your vault's librarian adds those based on its own rules.

This is deliberate. The raw export is a faithful transcript. Interpretation happens vault-side.

---

## What the vault does with it

This section describes what happens AFTER SoulPrint hands off. If your vault's `CLAUDE.md` already documents this, skip ahead — the librarian's behavior is configured there, not here.

For a Kepano-style vault following conventions like those in [kepano-obsidian](https://github.com/kepano/kepano-obsidian), the expected compile flow is:

1. **Librarian reads `raw/`.** Each SoulPrint-written `.md` file is one AI conversation.
2. **Extract metadata.** Parse the provider/date/id block. Map provider to a wiki-link: `chatgpt → [[ChatGPT]]`, `claude → [[Claude]]`, `gemini → [[Gemini]]`, `grok → [[Grok]]`.
3. **Identify topics.** Scan the transcript for technologies, projects, people, decisions. Each becomes a `[[wiki link]]` in frontmatter.
4. **Write to `References/`.** Using the AI Conversation template, create a compiled note with: summary (from SoulPrint's summary if one is present, otherwise librarian-generated), key takeaways, notable exchanges (2-3 substantive turns, not the full transcript), and a pointer back to the raw file.
5. **Cross-link.** Add `[[wiki links]]` to any existing notes that cover the same topics.
6. **Preserve the raw file.** The `References/` note is the compiled version. The raw file stays as the full-fidelity source.

An example vault contract is in your vault's own `CLAUDE.md`. That file is authoritative for the vault side — SoulPrint has no opinion on it.

---

## Configuration reference

### `SOULPRINT_EXPORT_DIR`

**Type:** string (absolute filesystem path)
**Default:** unset (empty string)
**Behavior:**

| State | Single-conv export | Multi-select export |
|-------|--------------------|----------------------|
| Unset | Browser download | Browser download (zip) |
| Set, directory exists, writable | Writes `.md` to dir, redirects with flash | Writes one `.md` per conversation to dir, flash with count |
| Set, directory does not exist | Falls back to browser download (warning flash) | Falls back to zip download |
| Set, directory not writable (read-only, permission denied) | Falls back to browser download (warning flash) | Falls back to zip download |

SoulPrint never creates the directory for you. If `SOULPRINT_EXPORT_DIR` points at a path that doesn't exist, the export falls back to browser download and warns. This is deliberate — we don't want SoulPrint silently creating random directories on your filesystem.

### Recommended setup for a multi-vault workflow

If you run multiple vaults (a work vault and a personal vault, say), swap `SOULPRINT_EXPORT_DIR` before exporting:

```powershell
# Export conversations into the work vault
$env:SOULPRINT_EXPORT_DIR = "C:\Users\chr\Work-Vault\raw"
# ... export from SoulPrint UI ...

# Switch to personal vault
$env:SOULPRINT_EXPORT_DIR = "C:\Users\chr\Obsidian-Vault\kepano-obsidian-main\raw"
# ... export ...
```

Setting it per-terminal-session gives you ad-hoc routing without losing the permanent default.

---

## Troubleshooting

### "I configured `SOULPRINT_EXPORT_DIR` but exports still download to my browser."

Three things to check:

1. **The shell SoulPrint is running in can actually see the variable.** Environment variables set in one terminal don't automatically propagate to others. If you set via `$env:...` in PowerShell, only that terminal has it. Use `[Environment]::SetEnvironmentVariable(..., "User")` for permanence, then restart your terminal.
2. **The directory exists.** SoulPrint does not create missing directories. Run `Test-Path $env:SOULPRINT_EXPORT_DIR` (PowerShell) or `ls -la "$SOULPRINT_EXPORT_DIR"` (bash) to verify.
3. **SoulPrint was started AFTER you set the variable.** If you started `soulprint` before setting the env var, restart it.

After clicking Export, watch for a flash message. A warning flash tells you which specific check failed.

### "Files are overwriting each other."

They shouldn't — SoulPrint disambiguates on collision by appending the conversation's stable ID. If this is happening, either (a) two different SoulPrint instances wrote at the same moment (unlikely in local-first usage), or (b) you're pointing `SOULPRINT_EXPORT_DIR` at a directory the vault's librarian is simultaneously writing into. Keep `raw/` write-only from SoulPrint's perspective; the librarian should move or leave files, never overwrite with the same filename pattern.

### "The librarian is compiling the same file twice."

SoulPrint is one-way: it writes to `raw/` and walks away. It does not track which files the librarian has already processed. That's the vault's job. Kepano's pattern is: compiled files stay in `raw/` but the compile pass checks `References/` for an existing compiled note with a matching stable ID in frontmatter, and skips if present. Your vault's `CLAUDE.md` should document this check.

### "I want the exports to go somewhere other than `raw/`."

`SOULPRINT_EXPORT_DIR` is the full path; it doesn't have to end in `raw`. Point it anywhere:

```bash
export SOULPRINT_EXPORT_DIR="$HOME/Downloads/soulprint-exports"
```

But then your vault's librarian has to be configured to process that location. Most Kepano-style setups expect `<vault>/raw/` by convention; deviating means rewriting the librarian's compile rule.

### "Can SoulPrint watch a directory and export automatically as new conversations arrive?"

No. SoulPrint is explicitly pull-based (you trigger the export). Live capture is on the long-term roadmap (see ROADMAP.md "Shape 1 — Capture pipeline") but not implemented, and would come as a browser extension rather than a filesystem watcher.

---

## Related

- [Memory Passport spec](specs/memory-passport-spec.md) — the canonical JSON export format; orthogonal to the raw-inbox markdown path.
- [Obsidian Bridge spec](specs/obsidian-bridge-spec.md) — the structured bridge (the other Obsidian path).
- [Landscape and positioning](product/landscape.md) — why SoulPrint is pull-based and file-first.

---

*This document describes SoulPrint's side of the handoff only. For what happens inside your vault after files land in `raw/`, see your vault's own `CLAUDE.md` or `AGENTS.md`.*
