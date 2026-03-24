Import a sample fixture and verify it persisted correctly.
Usage: /project:import-test

Steps:
1. Run: python -m src.importers.cli sample_data/chatgpt_export_sample.json --db instance/test_import.db
2. Verify row count in SQLite
3. Clean up instance/test_import.db
