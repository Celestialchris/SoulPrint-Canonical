"""Route-level tests for conversation-level attachment upload, listing, and download."""
from __future__ import annotations

import io
import re
import unittest
from pathlib import Path

from src.app import create_app
from src.app.assets import asset_absolute_path, attach_asset_to_conversation, store_asset
from src.app.models import Asset, ConversationAsset, ImportedConversation
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class ConversationAssetRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-assets-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.workdir / "test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"
        self.app = create_app()
        # Override instance_path so all route-triggered store_asset writes land in
        # the temp dir rather than the real instance directory.
        self.app.instance_path = str(self.workdir)
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _create_conversation(self, source_id: str = "conv-test-001") -> int:
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id=source_id,
                title="Test Conversation",
                created_at_unix=1710000000.0,
                updated_at_unix=1710000500.0,
            )
            db.session.add(conv)
            db.session.commit()
            return conv.id

    def test_upload_conversation_attachment_creates_asset_and_relationship(self):
        conv_id = self._create_conversation()
        data = b"test file content for upload" * 10

        response = self.client.post(
            f"/imported/{conv_id}/attachments",
            data={"attachment_file": (io.BytesIO(data), "upload_test.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/imported/{conv_id}/explorer", response.headers["Location"])

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 1)
            self.assertEqual(ConversationAsset.query.count(), 1)
            ca = ConversationAsset.query.first()
            self.assertEqual(ca.conversation_id, conv_id)
            asset = Asset.query.first()
            abs_path = asset_absolute_path(asset, instance_root=Path(self.app.instance_path))
            self.assertTrue(abs_path.exists(), f"File not found at {abs_path}")

    def test_explorer_lists_conversation_attachments(self):
        conv_id = self._create_conversation(source_id="conv-list-test")
        data = b"attachment content for listing" * 5

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "notes.pdf",
                "application/pdf",
                instance_root=Path(self.app.instance_path),
            )
            attach_asset_to_conversation(conv_id, asset.id)

        response = self.client.get(f"/imported/{conv_id}/explorer")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn("Attachments", html)
        self.assertIn("notes.pdf", html)
        self.assertIn("application/pdf", html)
        download_url = f"/imported/{conv_id}/attachments/"
        self.assertIn(download_url, html)

    def test_duplicate_upload_same_conversation_reuses_asset_and_relationship(self):
        conv_id = self._create_conversation(source_id="conv-dedup-test")
        data = b"identical content for dedup test" * 8

        self.client.post(
            f"/imported/{conv_id}/attachments",
            data={"attachment_file": (io.BytesIO(data), "dedup.txt")},
            content_type="multipart/form-data",
        )
        self.client.post(
            f"/imported/{conv_id}/attachments",
            data={"attachment_file": (io.BytesIO(data), "dedup.txt")},
            content_type="multipart/form-data",
        )

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 1)
            self.assertEqual(
                ConversationAsset.query.filter_by(conversation_id=conv_id).count(), 1
            )

        response = self.client.get(f"/imported/{conv_id}/explorer")
        html = response.get_data(as_text=True)
        links = re.findall(rf"/imported/{conv_id}/attachments/\d+/download", html)
        self.assertEqual(len(links), 1)

    def test_same_asset_can_attach_to_different_conversations_through_route(self):
        conv_a = self._create_conversation(source_id="conv-same-asset-a")
        conv_b = self._create_conversation(source_id="conv-same-asset-b")
        data = b"shared bytes for two conversations" * 6

        self.client.post(
            f"/imported/{conv_a}/attachments",
            data={"attachment_file": (io.BytesIO(data), "shared.pdf")},
            content_type="multipart/form-data",
        )
        self.client.post(
            f"/imported/{conv_b}/attachments",
            data={"attachment_file": (io.BytesIO(data), "shared.pdf")},
            content_type="multipart/form-data",
        )

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 1)
            self.assertEqual(ConversationAsset.query.count(), 2)
            conv_ids = {ca.conversation_id for ca in ConversationAsset.query.all()}
            self.assertEqual(conv_ids, {conv_a, conv_b})

    def test_missing_file_upload_redirects_with_error_and_creates_no_rows(self):
        conv_id = self._create_conversation(source_id="conv-missing-file")

        response = self.client.post(
            f"/imported/{conv_id}/attachments",
            data={},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Choose a file before attaching", html)

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 0)
            self.assertEqual(ConversationAsset.query.count(), 0)

    def test_download_attachment_returns_bytes_and_original_filename(self):
        conv_id = self._create_conversation(source_id="conv-download-test")
        data = b"downloadable content bytes" * 12

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "report.pdf",
                "application/pdf",
                instance_root=Path(self.app.instance_path),
            )
            ca = attach_asset_to_conversation(conv_id, asset.id)
            ca_id = ca.id

        response = self.client.get(
            f"/imported/{conv_id}/attachments/{ca_id}/download"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)
        content_disposition = response.headers.get("Content-Disposition", "")
        self.assertIn("report.pdf", content_disposition)

    def test_download_attachment_not_linked_to_conversation_returns_404(self):
        conv_a = self._create_conversation(source_id="conv-scope-a")
        conv_b = self._create_conversation(source_id="conv-scope-b")
        data = b"scoped content bytes" * 8

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "scoped.txt",
                "text/plain",
                instance_root=Path(self.app.instance_path),
            )
            ca = attach_asset_to_conversation(conv_a, asset.id)
            ca_id_on_a = ca.id

        response = self.client.get(
            f"/imported/{conv_b}/attachments/{ca_id_on_a}/download"
        )
        self.assertEqual(response.status_code, 404)

    def test_missing_conversation_upload_returns_404(self):
        data = b"test data for missing conv" * 5

        response = self.client.post(
            "/imported/999999/attachments",
            data={"attachment_file": (io.BytesIO(data), "test.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
