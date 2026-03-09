# SoulPrint Milestone 1 Setup

These commands were verified in this repository.

## 1) Create and activate a virtual environment

```bash
cd /workspace/SoulPrint-Canonical
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies (minimal Milestone 1)

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Run the app

```bash
export FLASK_APP=src.run:app
flask run --host 127.0.0.1 --port 5000
```

On first run, the SQLite database is created automatically at:

```text
instance/soulprint.db
```

## 4) Smoke test endpoints

In a second terminal (with the venv active):

```bash
curl -s -X POST http://127.0.0.1:5000/save \
  -H 'Content-Type: application/json' \
  -d '{"role":"user","content":"hello from setup smoke test","tags":"smoke"}'
```

Expected response shape:

```json
{"ok": true, "id": 1}
```

Then:

```bash
curl -s http://127.0.0.1:5000/chats
```

Expected: HTML page that includes saved chat entries.

## 5) Optional one-command local smoke check (no running server required)

```bash
python - <<'PY'
from src.app import create_app

app = create_app()
with app.test_client() as client:
    save = client.post('/save', json={
        'role': 'user',
        'content': 'smoke via test_client',
        'tags': 'smoke'
    })
    print('POST /save ->', save.status_code, save.get_json())

    chats = client.get('/chats')
    print('GET /chats ->', chats.status_code, 'bytes=', len(chats.data))
PY
```
