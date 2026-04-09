![SoulPrint](docs/screenshots/banner.png)

# SoulPrint

[![Tests](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml/badge.svg)](https://github.com/Celestialchris/SoulPrint-Canonical/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-green)](SECURITY.md)
[![No Telemetry](https://img.shields.io/badge/Telemetry-None-brightgreen)]()
[![Local Only](https://img.shields.io/badge/Cloud-None-brightgreen)]()
[![Latest Release](https://img.shields.io/github/v/release/Celestialchris/SoulPrint-Canonical)](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest)

**Your AI conversations are scattered everywhere. SoulPrint brings them home.**

![Workspace](docs/screenshots/workspace.png)

---

## Download

Grab the latest release for your platform from [GitHub Releases](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest):

- **Windows:** `SoulPrint-Setup.exe` (installer) or `SoulPrint-windows.zip`
- **macOS:** `SoulPrint-macos.zip` — unzip and move to Applications
- **Linux:** `SoulPrint-linux.tar.gz` — extract and run

Or use the bootstrap scripts in `bootstrap/` to automate the download and install.

**From source:**

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical
pip install -r requirements.txt
python -m src.run
# Open http://127.0.0.1:5678
```

Drop an export file on the Import page. Your conversations appear in seconds.

---

## Why This Exists

I use ChatGPT, Claude, and Gemini every day. My conversation history, 
research, decisions and creative work is scattered across three platforms
that don't talk to each other. Their exports sit dead on disk as unusable
zip files.

In March 2026, Google and Anthropic both launched features to import your
AI conversations into *their* silos. SoulPrint does the opposite: it
gives you a local file you own, with provenance you can verify, and
intelligence you can export.

Read the full [manifesto →](docs/manifesto.md)

---

## What It Does

**Import.** Drop a ChatGPT `.zip`, Claude `.json`, or Gemini Takeout. Provider auto-detected. Deduplicated. Normalized into one SQLite file on your machine.

**Browse and Search.** Workspace dashboard with stats and quick actions. Conversation list by provider. Transcript explorer with prompt-level TOC and minimap. Full-text search across all providers with message-level hits and highlighted snippets.

**Distill.** Cross-conversation themes. Summaries. Multi-conversation distillation into a handoff briefing you can paste into your next AI chat and pick up where you left off. *(Pro)*

**Export.** Memory Passport with manifest, canonical JSONL lanes, provenance index, and checksums. Validate any passport against the contract. The archive is a file you own.

---

## What It's Not

SoulPrint is not a hosted service, your data never leaves your machine.
Not a developer SDK, this is for people, not infrastructure. 
Not a browser extension, it's a local app with a canonical file you own.

---

## Trust

SoulPrint makes no network calls. There is no analytics, no telemetry, no phone-home. Your archive is a SQLite file on your machine that you can open in any database viewer and verify yourself.

The only exception: intelligence features (Ask, Distill, Themes) send conversation chunks to your configured LLM provider when you explicitly use them. This requires your own API key. Without a key, everything else works fully offline.

See [SECURITY.md](SECURITY.md) for architecture details and vulnerability reporting.

---

## Providers

| Provider | Format | Status |
|----------|--------|--------|
| ChatGPT | `.zip` from OpenAI | Supported |
| Claude | `.json` from Anthropic | Supported |
| Gemini | Google Takeout `MyActivity.json` or Chrome extension JSON | Supported |

---

## Roadmap

SoulPrint v0.1 ships with 3-provider import, full-text search, grounded answering, continuity engine, and Memory Passport export.

**Coming next:**
- Cross-model compare: same topic, different providers, side by side
- Paste-into-AI handoff loop
- More providers, more export formats

[Full roadmap →](ROADMAP.md)

---

## Support

SoulPrint is built by one person. If it's useful to you:

⭐ **Star this repo** — it helps people find it
🐛 **[Report a bug](https://github.com/Celestialchris/SoulPrint-Canonical/issues)** — every report makes it better
📣 **Tell someone** — word of mouth is everything for indie tools

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, architecture, test commands, and PR guidelines.

---

## License

Apache-2.0 — [inspect the code yourself](LICENSE).

---

*Your memory, on your machine, under your custody.*
