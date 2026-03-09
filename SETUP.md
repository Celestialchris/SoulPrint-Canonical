# Setup (Milestone 1 Baseline)

This repository is currently stabilized around the verified Milestone 1 runtime:
- app boot
- `POST /save`
- `GET /chats`

No mem0, RAG, agent orchestration, or importer expansion is included in this baseline.

## 1) Create and activate a virtual environment

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux/macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

For Milestone 1 runtime (Flask + SQLite only):

```bash
pip install -r requirements-minimal.txt
```

Optional broader dependency set (not required for Milestone 1 smoke runtime):

```bash
pip install -r requirements.txt
```

## 3) Run the app

### Windows PowerShell

```powershell
python -m src.run
```

### Linux/macOS

```bash
python -m src.run
```

On first boot, the app ensures `instance/` exists and initializes SQLite at `instance/soulprint.db`.

## 4) Run the Milestone 1 smoke test

```bash
python -m unittest tests.test_milestone1_smoke
```

The smoke test verifies:
- app import path works
- app factory boots
- Flask route map includes `/`, `/save`, and `/chats`

## Import duplicate policy

ChatGPT imports are deduplicated by `(source, source_conversation_id)` during persistence.
Re-importing the same export will skip already-imported conversations and report skip counts in CLI output.

## 5) Import one ChatGPT export into SQLite (local/dev)

```bash
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db
```

Quick verification:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect('instance/soulprint.db')
print(conn.execute('select count(*) from imported_conversation').fetchone()[0])
print(conn.execute('select count(*) from imported_message').fetchone()[0])
PY
```


## 6) Export one imported conversation to markdown (local/dev)

```bash
python -m src.importers.query_cli --db instance/soulprint.db export-md 1 exports/conversation-1.md
```

## 7) Query federated retrieval across both lanes (local/dev)

```bash
python -m src.retrieval.cli --db instance/soulprint.db
python -m src.retrieval.cli --db instance/soulprint.db "trip"
```
