# Getting Started

This guide covers the smallest practical path to running SoulPrint locally, loading sample data, and exercising the Memory Passport flow against the current repo.

## Minimal Setup

Create a Python 3.12 virtual environment and install the project dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Linux or macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the App

Start the local app:

```bash
pip install -e .
soulprint
```

Alternatively, for development without installing:

```bash
python -m src.run
```

On first boot, SoulPrint creates `instance/` if needed and initializes the canonical ledger at `instance/soulprint.db`.

The current web surfaces are available locally after boot:

- `/` for the workspace
- `/import` for the live web import surface
- `/ask` for the live in-app Ask surface
- `/passport` for the current capability/status surface around Memory Passport export and validation

## Run Tests

Run the current unit test suite:

```bash
python -m pytest tests/ -v
```

## Import Sample Data

Import any of the real sample exports already included in `sample_data/`:

```bash
python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/soulprint.db
python -m src.importers.cli sample_data/claude_export_sample.json --db instance/soulprint.db
python -m src.importers.cli sample_data/gemini_takeout_sample.json --db instance/soulprint.db
python -m src.importers.cli sample_data/gemini_conversations_sample.json --db instance/soulprint.db
```

The importer auto-detects supported providers from payload shape. Use `--provider` only when you need to force a provider boundary with one of the supported values.

The current read and inspection surfaces include `/imported`, `/imported/<id>/explorer`, `/federated`, and `/answer-traces`. The web import surface remains available at `/import`, the in-app Ask surface remains available at `/ask`, and `/passport` remains a bounded capability/status surface rather than a full artifact-inspection workflow.

## Export a Memory Passport

Export a Memory Passport package from the current canonical ledger:

```bash
python -m src.passport.cli export exports/passports --db instance/soulprint.db
```

This writes `memory-passport-v1/` under `exports/passports/`.

## Validate a Memory Passport

Validate an exported package:

```bash
python -m src.passport.cli validate exports/passports/memory-passport-v1
```

For machine-readable validation output:

```bash
python -m src.passport.cli validate exports/passports/memory-passport-v1 --json
```

## Windows Executable

To build a standalone Windows executable:

```powershell
cmd /c "scripts\build_windows.bat"
```

Prerequisites:
- Python 3.12 installed and on PATH
- The build script creates its own venv if `.venv` doesn't exist

The script will:
1. Install dependencies
2. Run the full test suite (build aborts if any test fails)
3. Package the app with PyInstaller
4. Create `dist\SoulPrint-windows.zip`

Double-click `dist\SoulPrint\SoulPrint.exe` to launch.
The app opens your browser automatically.

## Notes

- SoulPrint is local-first. The default workflow runs against local files and a local SQLite ledger.
- The canonical ledger is authoritative. Exports, traces, and other derived artifacts do not replace SQLite truth.
- Native and imported lanes remain explicit unless they are composed read-only through retrieval or browsing surfaces.
- Derived layers never overwrite canonical truth. Answers, traces, and exports must stay traceable back to stable IDs and timestamps.
