# Testing Rules
- Every route needs tests. Every importer needs tests.
- No route without tests, no import without duplicate guards.
- Tests use make_test_temp_dir() and release_app_db_handles() from tests/temp_helpers.py.
- conftest.py sets SOULPRINT_LICENSE_OVERRIDE=true so all tests pass without a key.
- Run: python -m pytest tests/ -v (or just: pytest)
- CI uses the same command in .github/workflows/tests.yml.
