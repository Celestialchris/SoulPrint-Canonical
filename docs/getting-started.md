# Getting Started

This guide covers installing SoulPrint and running it locally.

## Install from Release

Download the latest release for your platform from [GitHub Releases](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest).

**Windows:** Download `SoulPrint-Setup.exe` (or the zip) and run it. Or use the bootstrap script:

```powershell
bootstrap\install_windows.bat
```

**macOS:** Download `SoulPrint-macos.zip`, unzip, and move `SoulPrint.app` to `~/Applications/`. Or use the bootstrap script:

```bash
bash bootstrap/install_macos.sh
```

If macOS blocks the app, go to System Settings → Privacy & Security and click "Open Anyway".

**Linux:** Download `SoulPrint-linux.tar.gz` and extract to `~/.local/share/SoulPrint/`. Or use the bootstrap script:

```bash
bash bootstrap/install_linux.sh
```

The bootstrap scripts handle downloading, extracting, and preserving your existing data automatically.

---

## From Source (Development)

For development or if you want to run from source:

## Minimal Setup

Create a Python 3.12 virtual environment and install dependencies:

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

For intelligence features (summaries, topics, digests, ask, distill, continuity):

```bash
pip install -e ".[intelligence]"
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

The web app is available at `http://127.0.0.1:5678`.

## Run Tests

```bash
python -m pytest tests/ -v
```

## Import Sample Data

Import any of the sample exports included in `sample_data/`:

```bash
python -m src.importers.cli sample_data/chatgpt.json --db instance/soulprint.db
python -m src.importers.cli sample_data/claude.json --db instance/soulprint.db
python -m src.importers.cli sample_data/gemini_takeout.json --db instance/soulprint.db
python -m src.importers.cli sample_data/gemini_conv.json --db instance/soulprint.db
```

The importer auto-detects the provider from the file's payload shape.

## Export a Memory Passport

```bash
python -m src.passport.cli export exports/passports --db instance/soulprint.db
```

## Validate a Memory Passport

```bash
python -m src.passport.cli validate exports/passports/memory-passport-v1
```

For machine-readable output:

```bash
python -m src.passport.cli validate exports/passports/memory-passport-v1 --json
```

## Windows Executable

```powershell
cmd /c "scripts\build_windows.bat"
```

The script creates a venv, installs dependencies, runs the test suite, and packages with PyInstaller. Output: `dist\SoulPrint\SoulPrint.exe`.

## Notes

- SoulPrint is local-first. Everything runs against local files and a local SQLite ledger.
- The canonical ledger is authoritative. Exports, traces, and derived artifacts do not replace it.
- Native and imported lanes remain explicit unless composed read-only through retrieval or browsing.
- Derived layers never overwrite canonical truth.
