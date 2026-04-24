"""Tests for import_runs service module: classifier and DB helpers."""

from __future__ import annotations

import time
import unittest

from src.app.import_runs import classify_import_outcome, latest_import_runs, record_import_run
from src.app.models import ImportRun
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


# ---------------------------------------------------------------------------
# Pure classifier tests — no Flask needed
# ---------------------------------------------------------------------------

class ClassifyImportOutcomeTest(unittest.TestCase):
    def test_classify_not_reached_is_failed(self):
        result = classify_import_outcome(0, 0, 0, reached_importer=False)
        self.assertEqual(result, "failed")

    def test_classify_not_reached_nonzero_counts_still_failed(self):
        # reached_importer=False overrides everything
        result = classify_import_outcome(5, 3, 1, reached_importer=False)
        self.assertEqual(result, "failed")

    def test_classify_imported_only_is_success(self):
        result = classify_import_outcome(3, 0, 0, reached_importer=True)
        self.assertEqual(result, "success")

    def test_classify_imported_with_skipped_is_success(self):
        result = classify_import_outcome(1, 2, 0, reached_importer=True)
        self.assertEqual(result, "success")

    def test_classify_only_skipped_is_duplicate_only(self):
        result = classify_import_outcome(0, 3, 0, reached_importer=True)
        self.assertEqual(result, "duplicate_only")

    def test_classify_only_failed_is_failed(self):
        result = classify_import_outcome(0, 0, 2, reached_importer=True)
        self.assertEqual(result, "failed")

    def test_classify_imported_with_failed_is_partial(self):
        result = classify_import_outcome(1, 0, 1, reached_importer=True)
        self.assertEqual(result, "partial")

    def test_classify_skipped_with_failed_is_partial(self):
        result = classify_import_outcome(0, 1, 1, reached_importer=True)
        self.assertEqual(result, "partial")

    def test_classify_all_zero_reached_is_failed(self):
        result = classify_import_outcome(0, 0, 0, reached_importer=True)
        self.assertEqual(result, "failed")


# ---------------------------------------------------------------------------
# DB-backed tests — Flask app context required
# ---------------------------------------------------------------------------

class ImportRunWriterTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "import-run-writer")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_uri)
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir / 'test.db'}"
        from src.app import create_app
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_record_import_run_persists_row_with_all_fields(self):
        with self.app.app_context():
            row = record_import_run(
                provider="chatgpt",
                filename="export.json",
                status="success",
                conversations_imported=5,
                messages_imported=42,
                conversations_skipped=1,
                conversations_failed=0,
                error_message=None,
            )
            self.assertIsNotNone(row.id)
            fetched = ImportRun.query.get(row.id)
            self.assertEqual(fetched.provider, "chatgpt")
            self.assertEqual(fetched.filename, "export.json")
            self.assertEqual(fetched.status, "success")
            self.assertEqual(fetched.conversations_imported, 5)
            self.assertEqual(fetched.messages_imported, 42)
            self.assertEqual(fetched.conversations_skipped, 1)
            self.assertEqual(fetched.conversations_failed, 0)
            self.assertIsNone(fetched.error_message)
            self.assertAlmostEqual(fetched.imported_at, time.time(), delta=5)

    def test_record_import_run_truncates_error_message_to_500(self):
        long_msg = "x" * 600
        with self.app.app_context():
            row = record_import_run(
                provider=None,
                filename=None,
                status="failed",
                conversations_imported=0,
                messages_imported=0,
                conversations_skipped=0,
                conversations_failed=0,
                error_message=long_msg,
            )
            fetched = ImportRun.query.get(row.id)
            self.assertEqual(len(fetched.error_message), 500)

    def test_record_import_run_accepts_null_provider(self):
        with self.app.app_context():
            row = record_import_run(
                provider=None,
                filename="file.json",
                status="failed",
                conversations_imported=0,
                messages_imported=0,
                conversations_skipped=0,
                conversations_failed=0,
                error_message="no provider",
            )
            self.assertIsNone(ImportRun.query.get(row.id).provider)

    def test_record_import_run_accepts_null_filename(self):
        with self.app.app_context():
            row = record_import_run(
                provider="chatgpt",
                filename=None,
                status="failed",
                conversations_imported=0,
                messages_imported=0,
                conversations_skipped=0,
                conversations_failed=0,
                error_message="no file",
            )
            self.assertIsNone(ImportRun.query.get(row.id).filename)

    def test_latest_import_runs_returns_newest_first(self):
        with self.app.app_context():
            t1 = time.time() - 100
            t2 = time.time() - 50
            t3 = time.time()
            for ts, prov in [(t1, "chatgpt"), (t2, "claude"), (t3, "gemini")]:
                db_row = ImportRun(
                    provider=prov,
                    filename=None,
                    imported_at=ts,
                    status="success",
                    conversations_imported=1,
                    messages_imported=1,
                    conversations_skipped=0,
                    conversations_failed=0,
                    error_message=None,
                )
                from src.app.models.db import db
                db.session.add(db_row)
            from src.app.models.db import db
            db.session.commit()

            runs = latest_import_runs()
            self.assertEqual(runs[0].provider, "gemini")
            self.assertEqual(runs[1].provider, "claude")
            self.assertEqual(runs[2].provider, "chatgpt")

    def test_latest_import_runs_respects_limit(self):
        with self.app.app_context():
            from src.app.models.db import db
            for i in range(15):
                db.session.add(ImportRun(
                    provider="chatgpt",
                    filename=None,
                    imported_at=time.time() + i,
                    status="success",
                    conversations_imported=1,
                    messages_imported=1,
                    conversations_skipped=0,
                    conversations_failed=0,
                    error_message=None,
                ))
            db.session.commit()
            runs = latest_import_runs(limit=5)
            self.assertEqual(len(runs), 5)

    def test_latest_import_runs_empty_db_returns_empty_list(self):
        with self.app.app_context():
            self.assertEqual(latest_import_runs(), [])


if __name__ == "__main__":
    unittest.main()
