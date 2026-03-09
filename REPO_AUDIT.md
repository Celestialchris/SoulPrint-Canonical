# SoulPrint Canonical Repo Audit (Current Main Baseline)

## Audit intent
This audit reflects the **current** repository state after Milestone 1 stabilization work. It is focused on baseline runtime reality and repo structure readiness for the next implementation phase.

## Current repository structure

Top-level files/folders relevant to Milestone 1:
- `src/` (active Flask runtime code)
- `tests/` (smoke tests)
- `sample_data/` (reserved for future sample imports)
- `docs/reference/` (reserved for reference documentation)
- `SETUP.md` (cross-platform setup/run guide)
- `REPO_AUDIT.md` (this file)
- `requirements-minimal.txt` (Flask + Flask-SQLAlchemy)
- `requirements.txt` (minimal + optional broader dependencies)

Runtime package structure:
- `src/run.py` loads the Flask app from `src.app.create_app`
- `src/app/__init__.py` contains app factory and routes
- `src/app/models/` contains SQLAlchemy `db` and `MemoryEntry`
- `src/app/templates/` contains UI templates for `/` and `/chats`

## Milestone 1 runtime baseline (current truth)

Implemented and in scope:
- App boot path via `python -m src.run`
- SQLite initialization on app startup (`instance/soulprint.db`)
- `POST /save` persists chat entries
- `GET /chats` renders recent entries (optional tag filter)
- `GET /` renders home page

Out of scope (not implemented in this stabilization task):
- mem0 integration
- RAG/document-QA subsystem
- agent frameworks/orchestration
- importer redesign

## Verification status

Documented as already verified locally on Windows for Milestone 1:
- app boots
- `/save` works
- `/chats` works

Repo-level smoke coverage now exists in `tests/test_milestone1_smoke.py` for:
- import check (`src.run`)
- app factory boot check
- route map contains `/`, `/save`, `/chats`

## Notes

- This audit intentionally treats the current main branch as source of truth.
- The repository is structured for incremental next-phase implementation while preserving Milestone 1 behavior.
