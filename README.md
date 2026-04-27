# SoulPrint

[![Tests](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml/badge.svg)](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-green)](SECURITY.md)
[![No Telemetry](https://img.shields.io/badge/Telemetry-None-brightgreen)]()
[![Local Only](https://img.shields.io/badge/Cloud-None-brightgreen)]()
[![Latest Release](https://img.shields.io/github/v/release/Celestialchris/SoulPrint-Canonical)](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest)

**Your AI conversations, home.**

SoulPrint is a local-first memory archive for AI conversations. It imports chats from ChatGPT, Claude, Claude Code, Gemini, and Grok into a private SQLite ledger, then lets you browse, search, continue, and export the work with provenance intact.

![Workspace](docs/screenshots/workspace.png)

---

## Install

For the latest version, install from source:

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical
pip install -e .
soulprint
```

Open http://127.0.0.1:5678 and import an export file.

Older packaged builds for Windows, macOS, and Linux are available on [GitHub Releases](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest), but they currently trail the source version. Use the source install for the newest features and fixes.

---

## Why this exists

I use AI tools every day for research, code, strategy, writing, and long-running project work. The problem is not that conversations disappear. The problem is that they remain technically exportable but practically dead: scattered across platforms, stripped of continuity, and hard to reuse when the work needs to continue.

In March 2026, Google and Anthropic both launched features that import your AI conversations into *their* silos. SoulPrint does the opposite. The archive is a file you own, with provenance you can verify, and intelligence you can export.

Read the full [manifesto](docs/manifesto.md).

---

## What SoulPrint does

- **Bring conversations home.** Import ChatGPT `.zip`, Claude `.json`, Claude Code `.jsonl`, Gemini Takeout, and Grok `.json`. Provider auto-detected. Deduplicated. Normalized into one SQLite file on your machine.
- **Preserve raw transcripts.** The full message text, in order, with original timestamps and source identity. The canonical ledger is authoritative; nothing summarizes over it.
- **Search exact messages.** SQLite FTS5 across all providers, with snippet highlighting and deep links from results back to the precise message in the transcript explorer.
- **Ask with evidence.** Optional grounded answering over your archive, with traces showing which conversations and messages backed each response.
- **Continue old threads.** Distill, Continuity Packets, and bridge handoffs turn a selection of conversations into paste-ready context for the next chat. Pick up where you left off, even after a model update.
- **Export without lock-in.** Memory Passport (manifest, JSONL, provenance index, checksums), Markdown exports, attachment-aware zip bundles, and a one-way Obsidian raw-inbox bridge.
- **Keep custody local.** No cloud accounts, no analytics, no telemetry, no background sync. The archive is a SQLite file on your disk that you can open in any database viewer.

---

## Architecture

```text
Provider exports
  ChatGPT / Claude / Claude Code / Gemini / Grok
        |
        v
Importers
  normalize conversations, messages, timestamps, providers
        |
        v
SQLite ledger
  conversations, messages, tags, stars, imports, attachments
        |
        +--> FTS5 retrieval
        |      exact-message search and federated search
        |
        +--> Intelligence layer
        |      Ask, Distill, Recurring Themes, Continuity Packet
        |
        +--> Export layer
               Markdown, Obsidian raw inbox, Memory Passport,
               attachment-aware zip and <stem>.assets/ bundles
```

| Layer | Implementation |
|-------|----------------|
| App runtime | Python 3.12, Flask |
| Storage | SQLite, SQLAlchemy |
| Search | SQLite FTS5 |
| Interface | Jinja2, HTML, CSS |
| Local intelligence | Ollama through OpenAI-compatible endpoint |
| Integrations | CLI, MCP, Obsidian export |
| File custody | Filesystem storage with SHA-256 metadata |
| Export | Markdown, JSONL, manifests, zip bundles |

For the full architecture reference, repo map, surface map, and development setup, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Data and trust

SoulPrint is built around custody, not access.

- No analytics.
- No telemetry.
- No hosted account required.
- No background sync.
- The core archive is local: import, browse, search, notes, exports, passport, and the answer-trace browser all run with no network.
- The SQLite database is inspectable in any viewer (DB Browser for SQLite, the `sqlite3` CLI, or any tool that reads SQLite).
- Attached files live as ordinary files on disk; SoulPrint records SHA-256, MIME type, original filename, size, and provenance metadata in the ledger.
- Intelligence features (Ask, Distill, Recurring Themes, Continuity Packet) contact only the LLM provider you have explicitly configured, and only when you trigger them.
- The Ollama path is fully local: no API key, no network egress beyond `localhost`.

See [SECURITY.md](SECURITY.md) for the security model, network behavior, and vulnerability reporting.

---

## Exports

- **Markdown.** Single conversation or multi-select, with metadata block and full transcript.
- **Attachment-aware bundles.** Conversations with attached files export as a `.zip` containing the markdown, a `<stem>.assets/` subtree of the attached files, and a `manifest.json` with provenance. Directory exports write the same `<stem>.assets/` folder as a sibling next to the markdown.
- **Obsidian raw-inbox bridge.** Drop conversations into a vault's `raw/` directory; your vault's own librarian decides how to file them. See [docs/obsidian-raw-inbox.md](docs/obsidian-raw-inbox.md).
- **Memory Passport.** Versioned export contract with manifest, canonical JSONL lanes, provenance index, and checksums. Validate any passport against the contract.

---

## Optional: fully local intelligence (Ollama + Gemma 4)

Ask, Distill, and Recurring Themes run against any OpenAI-compatible endpoint. For a fully local setup with zero cloud calls and no API key, point SoulPrint at [Ollama](https://ollama.com) running Gemma 4.

Install the optional intelligence dependencies:

```bash
pip install -e ".[intelligence]"
```

**One-time:** `ollama pull gemma4`

**Every run, terminal A (Ollama server):**

```bash
# macOS / Linux
OLLAMA_CONTEXT_LENGTH=65536 ollama serve

# Windows (PowerShell)
$env:OLLAMA_CONTEXT_LENGTH="65536"; ollama serve
```

**Every run, terminal B (SoulPrint):**

```bash
# macOS / Linux
export SOULPRINT_LLM_PROVIDER=openai
export SOULPRINT_LLM_BASE_URL=http://localhost:11434/v1
export SOULPRINT_LLM_MODEL=gemma4
soulprint

# Windows (PowerShell)
$env:SOULPRINT_LLM_PROVIDER="openai"
$env:SOULPRINT_LLM_BASE_URL="http://localhost:11434/v1"
$env:SOULPRINT_LLM_MODEL="gemma4"
soulprint
```

`OLLAMA_CONTEXT_LENGTH` must be set in the shell that runs `ollama serve`, not the shell that runs SoulPrint. Skipping this caps context at 4096 tokens and silently truncates Distill output. See [CLAUDE.md § LLM Configuration](CLAUDE.md#llm-configuration) for the Gemma 4 model-size matrix and cloud alternatives.

---

## Providers

| Provider | Format | Status |
|----------|--------|--------|
| ChatGPT | `.zip` from OpenAI | Supported |
| Claude | `.json` from Anthropic | Supported |
| Claude Code | `.jsonl` from Claude Code session files | Supported |
| Gemini | Google Takeout `MyActivity.json` or Chrome extension JSON | Supported |
| Grok | `.json` from xAI export | Supported |

---

## MCP server

Connect SoulPrint to Claude Code, Cursor, or any MCP-compatible AI tool. Past conversations become searchable context in every coding session.

```bash
# Add to your .mcp.json or Claude Code settings:
{
  "mcpServers": {
    "soulprint": {
      "command": "python",
      "args": ["-m", "src.mcp_server"]
    }
  }
}
```

---

## Interface roadmap

SoulPrint is intentionally simple today: Python, Flask, SQLite, Jinja2, HTML, CSS, and Markdown docs. That stack is the right foundation for a local memory ledger.

The long-term interface direction is gradual, not rewrite-first:

1. Keep Flask and Jinja2 while the product core becomes coherent.
2. Add clean JSON endpoints around conversations, messages, search, attachments, continuity, and export.
3. Build SvelteKit and TypeScript cockpit surfaces for workflows that need richer interaction.
4. Consider Tauri when desktop distribution becomes real.

The rule is simple: the interface may become more fluid, but it must never become the source of truth. SQLite remains canonical. Python remains the local engine. The frontend views, searches, filters, and triggers controlled actions through backend boundaries.

Read the full doctrine: [`docs/specs/frontend-evolution-doctrine.md`](docs/specs/frontend-evolution-doctrine.md).

---

## Support

If your conversations with an AI have become meaningful to you, this tool is for you too. Maybe you've worried about a platform update changing how a companion talks, or about losing months of chat history when a service shuts down. Install from source above. Drop your ChatGPT or Claude export. That's it. Conversations now live as a file on your computer. Nobody can update them away.

SoulPrint is built by one person. If it is useful:

- **Star this repo** to help people find it
- **[Buy me a coffee](https://buymeacoffee.com/chrsp)** to keep it going
- **[Report a bug](https://github.com/Celestialchris/SoulPrint-Canonical/issues)** to make it better
- **Tell someone**, word of mouth is everything for indie tools

---

## License

Apache-2.0. See [LICENSE](LICENSE).
