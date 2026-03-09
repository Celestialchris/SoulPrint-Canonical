# Setup

## 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

For Milestone 1 runtime (Flask + SQLite only):

```bash
pip install -r requirements-minimal.txt
```

For broader optional dependencies:

```bash
pip install -r requirements.txt
```

## 3) Run the app

```bash
python -m src.run
```

The app creates `instance/` if needed and initializes the SQLite database at `instance/soulprint.db` on first boot.

## Validation status

This repository repair validated only these checks in an automated shell:
- `import src.run` succeeds
- `create_app()` succeeds
- Flask routes can be listed from the created app object

Local manual verification still required:
- Open the UI in a browser and verify end-to-end interactions (`/`, `/save`, `/chats`)
- Confirm persistence behavior in your local environment
