# SoulPrint Canonical Repo Audit (Milestone 1)

## Scope
Inspected only the current repository contents and code paths relevant to Milestone 1:
- app boots
- DB initializes
- `/save` works
- `/chats` works
- no mem0/RAG

## File Structure Summary

Top-level:
- `README.md` (very brief project description)
- `SETUP.md` (currently empty)
- `requirements.txt`
- `src/`

`src/`:
- `run.py` (creates app via `create_app()`)
- `config.py` (Flask/SQLAlchemy config)
- `app/`
  - `__init__.py` (Flask app factory + routes: `/`, `/save`, `/chats`)
  - `models.py` (`MemoryEntry` model)
  - `storage.py` (`ChatLog` model, currently unused by routes)
  - `models/db.py` (SQLAlchemy `db` instance)
  - `templates/index.html` and `templates/view.html`
  - `utils/encryption.py` (present but not in current request path)
- `tools/` and `prompts/` contain non-Milestone-1 files (`*.txt`, yaml prompts)

## Milestone 1 Status (Based on Current Code)

### What already exists
- App factory exists and registers routes in `src/app/__init__.py`.
- DB init call exists (`db.init_app(app)` + `db.create_all()`).
- `/save` route exists and writes `MemoryEntry` rows.
- `/chats` route exists and lists recent entries, with optional `tag` filtering.
- No mem0/RAG runtime integration in the active Flask path.

### Blockers to Milestone 1

1. **Runtime dependencies are not installed by default in this environment**
   - Importing the app currently fails with `ModuleNotFoundError: No module named 'flask'` unless dependencies are installed.
   - This blocks boot and endpoint verification until environment setup is completed.

2. **`instance/` directory is missing, but configured SQLite path expects it**
   - `Config.SQLALCHEMY_DATABASE_URI` points to `../instance/soulprint.db`.
   - Current repo state has no `instance/` directory.
   - This is a likely DB initialization blocker in a fresh checkout unless directory creation is handled externally.

3. **`SETUP.md` is empty**
   - There is no in-repo setup/run instruction path for Milestone 1 validation.
   - This increases boot/setup failure risk even though code for routes exists.

### Non-blocking observations
- `src/app/storage.py` defines `ChatLog`, while routes use `MemoryEntry` in `src/app/models.py`; this appears to be legacy/parallel model code, not an immediate Milestone 1 blocker.
- `requirements.txt` includes heavier packages (`chromadb`, `sentence-transformers`) that are out of current Milestone 1 scope, but this is not a blocker to core Flask+SQLite behavior if minimal dependencies are installed.

## Smallest Viable Path to Clear Milestone 1
1. Install required dependencies from `requirements.txt` (or minimally Flask + Flask-SQLAlchemy).
2. Ensure `instance/` exists before first boot.
3. Run app and smoke-test:
   - boot app
   - POST `/save`
   - GET `/chats`

No mem0/RAG additions are needed for Milestone 1.
