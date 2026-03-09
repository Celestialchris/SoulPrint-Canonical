# SoulPrint-Canonical
SoulPrint began as a sovereign memory project: an attempt to capture logs, reflections, imports, and symbolic meaning in one auditable system. The early practical form was a Flask + SQLite + Markdown application. The deeper ambition was larger: a memory engine that could hold lived experience, agent reflections, long-term retrieval, and later multi-agent orchestration through an Obsidian-friendly vault.

## Current Milestone 1+ importer capability

The repository now includes a first importer path for ChatGPT exports:

- parse ChatGPT `conversations.json`-style data
- normalize into stable conversation/message records
- persist normalized records into SQLite (`ImportedConversation`, `ImportedMessage`)

See:

- parser: `src/importers/chatgpt.py`
- persistence: `src/importers/persistence.py`
- sample fixture: `sample_data/chatgpt_export_sample.json`
- tests: `tests/test_chatgpt_importer.py`
