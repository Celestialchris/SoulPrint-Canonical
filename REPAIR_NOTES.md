# Milestone 1 Repair Notes

## Scope
This repair is intentionally minimal and only targets Milestone 1 readiness:
- app boot
- SQLite initialization in a fresh checkout
- `/save` working
- `/chats` working

## What changed

1. **Made SQLite path handling robust for fresh checkout**
   - Updated `src/config.py` to define a stable `INSTANCE_DIR` and use it for the default SQLite DB path.
   - Result: default DB location remains `instance/soulprint.db`, but path handling is clearer and explicit.

2. **Ensured required directory creation before DB initialization**
   - Updated `src/app/__init__.py` in `create_app()` to:
     - inspect `SQLALCHEMY_DATABASE_URI`
     - if it is file-based SQLite (`sqlite:///...`), create the parent directory with `os.makedirs(..., exist_ok=True)`.
   - Result: first run no longer depends on pre-existing `instance/`.

3. **Reduced dependencies to Milestone 1 minimum**
   - Updated `requirements.txt` to only include:
     - `Flask`
     - `Flask-SQLAlchemy`
     - `python-dotenv`
   - Result: faster, lower-risk install for current milestone.

4. **Filled in `SETUP.md` with exact run and verification commands**
   - Added venv setup, dependency install, app run command, and smoke test commands for `/save` and `/chats`.

## Verification performed

- Ran `python3 -m compileall src SETUP.md REPAIR_NOTES.md` successfully to validate syntax.
- Attempted dependency install from `requirements.txt`, but package index access is blocked in this execution environment.
- Because dependencies could not be installed here, runtime endpoint smoke tests are documented in `SETUP.md` but could not be executed in this container.

## Why this is minimal and reversible

- No schema redesign.
- No route changes to `/save` or `/chats` behavior.
- No new architecture or subsystems.
- Only targeted config/startup hardening + docs + dependency trimming for Milestone 1.
