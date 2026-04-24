"""Route tests for the web import lifecycle page."""

from __future__ import annotations

import io
import unittest
from pathlib import Path

import time

from src.app import create_app
from src.app.models import ImportedConversation, ImportRun
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class ImportRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "import-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        self.sqlite_path = self.workdir / "import_route_test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.sqlite_path}"

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_get_import_route_renders(self):
        response = self.client.get("/import")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Bring conversations home", html)
        self.assertIn('name="export_file"', html)

    def test_submit_no_file_shows_validation_error(self):
        response = self.client.post("/import", data={}, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Choose an export file before importing.", html)

    def test_valid_supported_fixture_imports_successfully(self):
        fixture_bytes = Path("sample_data/chatgpt.json").read_bytes()

        response = self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt.json")},
            content_type="multipart/form-data",
        )

        # First import on empty DB redirects to /summary
        self.assertEqual(response.status_code, 302)
        self.assertIn("/summary", response.headers.get("Location", ""))

        with self.app.app_context():
            self.assertEqual(ImportedConversation.query.count(), 2)

    def test_duplicate_import_shows_skip_feedback(self):
        fixture_bytes = Path("sample_data/chatgpt.json").read_bytes()

        self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt.json")},
            content_type="multipart/form-data",
        )
        second = self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt.json")},
            content_type="multipart/form-data",
        )

        self.assertEqual(second.status_code, 200)
        html = second.get_data(as_text=True)
        self.assertIn("Conversations imported: 0", html)
        self.assertIn("Duplicates skipped: 2", html)
        self.assertIn("No new conversations were imported", html)

    def test_invalid_json_shows_clean_error(self):
        response = self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(b"{not json"), "invalid.json")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Import could not be completed", html)
        self.assertIn("Import file is not valid JSON", html)

    def test_unsupported_format_shows_clean_error(self):
        response = self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(b'{"hello": "world"}'), "unknown.json")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Import could not be completed", html)
        self.assertIn("could not recognize this export format", html.lower())


    # --- ImportRun instrumentation tests ---

    def test_successful_import_creates_success_run(self):
        fixture_bytes = Path("sample_data/chatgpt.json").read_bytes()
        self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt.json")},
            content_type="multipart/form-data",
        )
        with self.app.app_context():
            self.assertEqual(ImportRun.query.count(), 1)
            run = ImportRun.query.first()
            self.assertEqual(run.status, "success")
            self.assertEqual(run.provider, "chatgpt")
            self.assertEqual(run.filename, "chatgpt.json")
            self.assertGreater(run.conversations_imported, 0)

    def test_duplicate_import_creates_duplicate_only_run(self):
        fixture_bytes = Path("sample_data/chatgpt.json").read_bytes()
        self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt.json")},
            content_type="multipart/form-data",
        )
        self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(fixture_bytes), "chatgpt.json")},
            content_type="multipart/form-data",
        )
        with self.app.app_context():
            self.assertEqual(ImportRun.query.count(), 2)
            latest = ImportRun.query.order_by(ImportRun.imported_at.desc()).first()
            self.assertEqual(latest.status, "duplicate_only")
            self.assertEqual(latest.conversations_imported, 0)

    def test_no_file_creates_failed_run(self):
        self.client.post("/import", data={}, content_type="multipart/form-data")
        with self.app.app_context():
            self.assertEqual(ImportRun.query.count(), 1)
            run = ImportRun.query.first()
            self.assertEqual(run.status, "failed")
            self.assertIsNone(run.provider)
            self.assertIsNone(run.filename)

    def test_malformed_file_creates_failed_run(self):
        self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(b"{not json"), "invalid.json")},
            content_type="multipart/form-data",
        )
        with self.app.app_context():
            self.assertEqual(ImportRun.query.count(), 1)
            self.assertEqual(ImportRun.query.first().status, "failed")

    def test_unrecognized_format_creates_failed_run(self):
        self.client.post(
            "/import",
            data={"export_file": (io.BytesIO(b'{"hello": "world"}'), "unknown.json")},
            content_type="multipart/form-data",
        )
        with self.app.app_context():
            self.assertEqual(ImportRun.query.count(), 1)
            self.assertEqual(ImportRun.query.first().status, "failed")

    def test_get_shows_no_imports_yet_when_empty(self):
        response = self.client.get("/import")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No imports yet.", html)

    def test_get_shows_recent_runs_table_after_import(self):
        with self.app.app_context():
            db.session.add(ImportRun(
                provider="chatgpt",
                filename="export.json",
                imported_at=time.time(),
                status="success",
                conversations_imported=3,
                messages_imported=12,
                conversations_skipped=0,
                conversations_failed=0,
                error_message=None,
            ))
            db.session.commit()

        response = self.client.get("/import")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Recent imports", html)
        self.assertIn("chatgpt", html)
        self.assertIn("success", html)


if __name__ == "__main__":
    unittest.main()
