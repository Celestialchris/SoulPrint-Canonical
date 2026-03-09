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

## Minimal ChatGPT import CLI (local/dev)

Use the importer CLI to load one ChatGPT export fixture or file into SQLite:

```bash
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db
```

## Minimal imported conversation query CLI (local/dev)

After importing, you can inspect imported conversations and view one conversation with ordered messages:

```bash
python -m src.importers.query_cli --db instance/soulprint.db list
python -m src.importers.query_cli --db instance/soulprint.db search "trip"
python -m src.importers.query_cli --db instance/soulprint.db show 1
```

You can verify imported rows with SQLite:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect('instance/soulprint.db')
print('conversations:', conn.execute('select count(*) from imported_conversation').fetchone()[0])
print('messages:', conn.execute('select count(*) from imported_message').fetchone()[0])
PY
```
