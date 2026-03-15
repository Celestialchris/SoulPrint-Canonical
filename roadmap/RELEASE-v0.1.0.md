# SoulPrint v0.1.0 — First Public Release

**Your AI conversations are scattered everywhere. SoulPrint brings them home.**

## What's included

### Import
- ChatGPT `.zip` exports (from OpenAI data export)
- Claude `.json` exports (from Anthropic)
- Gemini exports (Google Takeout and Chrome extension JSON)
- Auto-detection — drop any supported file and SoulPrint figures it out
- Duplicate guards prevent re-importing the same conversation

### Browse & Search
- Workspace dashboard with provider coverage and recent activity
- Imported conversation browser with per-provider filtering
- Transcript explorer with prompt-level table of contents and minimap
- Native memory for notes created directly in SoulPrint
- Federated view across all providers with explicit provenance
- Full-text search across all lanes

### Intelligence (BYOK)
- Per-conversation summaries
- Cross-conversation topic detection
- Multi-conversation digests
- Continuity packets for handoff into new chats
- Bridge assembly and lineage suggestions
- Requires your own OpenAI or Anthropic API key

### Answering
- Grounded answering from your conversation record
- Every answer cites specific source conversations
- Returns `insufficient_evidence` rather than guessing
- Append-only answer trace audit trail

### Export
- Memory Passport with manifest, canonical JSONL lanes, and provenance index
- Passport validation against the canonical contract
- Reports: `valid`, `valid_with_warnings`, or `invalid`

## Quick Start

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical
pip install -r requirements-minimal.txt
python -m src.run
```

Open http://127.0.0.1:5678 and drop an export file on the Import page.

## Stats

- 10 web surfaces
- 41 test files, 365 test methods
- Python 3.12, Flask, SQLite
- Apache-2.0 licensed

## What's next

- Desktop wrapper (PyWebView)
- Freemium gate with local license validation
- "AI Memory Wrapped" shareable summary page
- Additional providers (Grok, Copilot, Perplexity)

---

*Local-first. Your memory, under your custody.*
