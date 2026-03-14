# Milestone 1 Repair Notes

## Scope of this corrective pass

This pass only addresses Milestone 1 stability items requested for:
1. model import conflict cleanup
2. dependency file split and deduplication
3. config simplification
4. setup/repair documentation accuracy

No route, schema, or architecture expansion was introduced.

## File-level changes

- Removed conflicting top-level model module: `src/app/models.py`
- Defined and exported `MemoryEntry` from package module: `src/app/models/__init__.py`
- Simplified DB config path logic in `src/config.py` to a single explicit SQLite path
- Added explicit `instance/` directory creation in `src/app/__init__.py` before DB initialization
- Added `requirements-minimal.txt` for Flask + SQLite runtime dependencies only
- Updated `requirements.txt` to include `requirements-minimal.txt` plus optional/future deps
- Rewrote `docs/getting-started.md` (formerly `SETUP.md`) to match what was actually validated

## Validation actually performed

These checks were run after the fixes:
- `python -c "import src.run"`
- `python -c "from src.app import create_app; app = create_app(); print('boot-ok')"`
- `python -c "from src.app import create_app; app = create_app(); print(sorted([r.rule for r in app.url_map.iter_rules()]))"`

## Validation not performed in this pass

- Browser-based UI interaction checks
- Full workflow checks for import/normalize/store/retrieve
- Non-minimal optional dependency feature validation

## Windows SQLite test cleanup note

- Import/query test paths now explicitly call `db.session.remove()` and `db.engine.dispose()` after SQLite operations to release pooled file handles before `TemporaryDirectory` teardown on Windows.
- This is a lifecycle cleanup fix only; schema and runtime import/query behavior are unchanged.
