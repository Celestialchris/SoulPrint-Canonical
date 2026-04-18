# SoulPrint

[![Tests](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml/badge.svg)](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-green)](SECURITY.md)
[![No Telemetry](https://img.shields.io/badge/Telemetry-None-brightgreen)]()
[![Local Only](https://img.shields.io/badge/Cloud-None-brightgreen)]()
[![Latest Release](https://img.shields.io/github/v/release/Celestialchris/SoulPrint-Canonical)](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest)

**Your AI conversations, home.**

SoulPrint imports your ChatGPT, Claude, and Gemini history into a single searchable archive on your machine. No cloud. No accounts. No telemetry. The archive is a file you own, one SQLite database you can open in any tool and verify yourself.

![Workspace](docs/screenshots/workspace.png)

---

## Download

**Non-technical?** Download a packaged build from [GitHub Releases](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest).

- Windows: `SoulPrint-Setup.exe` (installer) or `SoulPrint-windows.zip`
- macOS: `SoulPrint-macos.zip`
- Linux: `SoulPrint-linux.tar.gz`

**Developer?** Install from source in 60 seconds:

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical
pip install -e .                    # core: import, browse, search, export
pip install -e ".[intelligence]"    # + Ask, Distill, Themes (requires Ollama or API key)
soulprint
```

Open `http://127.0.0.1:5678`. Drop an export file. Your conversations appear in seconds.

---

### Optional: fully local intelligence (Ollama + Gemma 4)

Ask, Distill, and Recurring Themes run against any OpenAI-compatible endpoint. For a fully local setup — zero cloud calls, no API key — point SoulPrint at [Ollama](https://ollama.com) running Gemma 4.

**One-time:** `ollama pull gemma4`

**Every run — terminal A (Ollama server):**

```bash
# macOS / Linux
OLLAMA_CONTEXT_LENGTH=65536 ollama serve

# Windows (PowerShell)
$env:OLLAMA_CONTEXT_LENGTH="65536"; ollama serve
```

**Every run — terminal B (SoulPrint):**

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

## What it does

**Import.** Drop a ChatGPT `.zip`, Claude `.json`, or Gemini Takeout. Provider auto-detected. Deduplicated. Normalized into one SQLite file on your machine.

**Browse and search.** Workspace dashboard, conversation list by provider, transcript explorer with prompt-level TOC and minimap, full-text search across all providers with highlighted snippets. Clip moments from any conversation into personal notes with full source provenance.

**Distill.** Select any set of conversations and get a paste-ready handoff document, what was decided, what was built, what's open. Paste it into a new chat and pick up exactly where you left off. No more starting from zero after a model update.

**Export.** Memory Passport with manifest, canonical JSONL, provenance index, and checksums. Validate any passport against the contract. The archive is a file you own.

---

## Why this exists

I use ChatGPT, Claude, and Gemini every day. My conversation history, research, decisions, and creative work is scattered across three platforms that don't talk to each other. Their exports sit dead on disk as unusable zip files.

In March 2026, Google and Anthropic both launched features to import your AI conversations into *their* silos. SoulPrint does the opposite: it gives you a local file you own, with provenance you can verify, and intelligence you can export.

Read the full [manifesto](docs/manifesto.md).

---

## Providers

| Provider | Format | Status |
|----------|--------|--------|
| ChatGPT | `.zip` from OpenAI | Supported |
| Claude | `.json` from Anthropic | Supported |
| Gemini | Google Takeout `MyActivity.json` or Chrome extension JSON | Supported |
| Grok | `.json` from xAI export | Supported |

---

## MCP server

Connect SoulPrint to Claude Code, Cursor, or any MCP-compatible AI tool. Your past conversations become searchable context in every coding session.

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

## Trust

SoulPrint makes no network calls. No analytics, no telemetry, no phone-home. Your archive is a SQLite file on your machine that you can open in any database viewer and verify yourself.

The only exception: intelligence features (Ask, Distill, Themes) send conversation chunks to your configured LLM provider when you explicitly use them. Point them at Ollama for a fully-local setup (no key, no network), or bring your own cloud API key (OpenAI, Anthropic). Without a provider, everything else works fully offline.

See [SECURITY.md](SECURITY.md) for architecture details and vulnerability reporting.

---

## Architecture

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture, setup, and development guidelines.

---

## Support

If your conversations with an AI have become meaningful to you, this tool is for you too. Maybe you've worried about a platform update changing how your companion talks, or about losing months of chat history when a service shuts down. Download the installer above. Drop your ChatGPT or Claude export. That's it. Your conversations now live as a file on your computer. Nobody can update them away.

SoulPrint is built by one person. If it's useful:
- **Star this repo** to help people find it
- **[Buy me a coffee](https://buymeacoffee.com/chrsp)** to keep it going
- **[Report a bug](https://github.com/Celestialchris/SoulPrint-Canonical/issues)** to make it better
- **Tell someone** word of mouth is everything for indie tools

---

## License

Apache-2.0. [Inspect the code yourself](LICENSE).
