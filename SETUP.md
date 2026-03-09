# SoulPrint Setup (Milestone 1)

This repo currently runs as a **Flask + SQLite** app. For Milestone 1, use the minimal dependency path by default.

## 1) Create and activate a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

### Minimal runtime path (recommended for Milestone 1)

Installs only what the active runtime uses today:

```bash
pip install -r requirements-minimal.txt
```

### Broader dependency path (optional)

Use this only if you explicitly need optional/future modules:

```bash
pip install -r requirements.txt
```

`requirements.txt` includes `requirements-minimal.txt` plus optional packages that are not required to boot the current app runtime.

## 3) Run the app

From the repo root:

```bash
flask --app src.run:app run --debug
```

Or with Python:

```bash
python -m flask --app src.run:app run --debug
```

## 4) Verify SQLite boot path

On first start, Flask-SQLAlchemy creates the database at:

- `instance/soulprint.db`

This file is the canonical Milestone 1 storage layer.
