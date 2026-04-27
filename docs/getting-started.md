# Getting Started

This guide covers installing SoulPrint and running it locally.

## Install From Source (Recommended)

The current source tree ships features the packaged builds may predate. For
the newest behavior, install from source.

Requirements: Python 3.12.

```bash
git clone https://github.com/Celestialchris/SoulPrint-Canonical.git
cd SoulPrint-Canonical
pip install -e .
soulprint
```

Open http://127.0.0.1:5678 and import an export file.

For intelligence features (Ask, Distill, Recurring Themes, Continuity Packet):

```bash
pip install -e ".[intelligence]"
```

See the README's Ollama section for a fully local intelligence setup.

## Packaged Builds (v0.6.0)

Older packaged builds for Windows, macOS, and Linux are available on
[GitHub Releases](https://github.com/Celestialchris/SoulPrint-Canonical/releases/latest),
but they currently trail the source version. Use the source install for the
newest features and fixes.

## Run Tests

```bash
python -m pytest tests/ -v
```

## Import Sample Data

Sample exports for supported providers ship in `sample_data/`.

```bash
python -m src.importers.cli sample_data/chatgpt.json --db instance/soulprint.db
python -m src.importers.cli sample_data/claude.json --db instance/soulprint.db
python -m src.importers.cli sample_data/claude_code.jsonl --db instance/soulprint.db
python -m src.importers.cli sample_data/gemini_takeout.json --db instance/soulprint.db
python -m src.importers.cli sample_data/grok.json --db instance/soulprint.db
```

The importer auto-detects the provider from the file's payload shape.

## Export and Validate a Memory Passport

```bash
python -m src.passport.cli export exports/passports --db instance/soulprint.db
python -m src.passport.cli validate exports/passports/memory-passport-v1
```

For machine-readable output: `--json`.

## Notes

- SoulPrint is local-first. The core archive runs against local files and a local SQLite ledger.
- The canonical ledger is authoritative. Exports, traces, and derived artifacts do not replace it.
- Native and imported lanes remain explicit unless composed read-only through retrieval or browsing.
- Derived layers never overwrite canonical truth.
