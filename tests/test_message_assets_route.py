"""Route-level tests for message-level attachment upload, listing, and download."""
from __future__ import annotations

import io
import re
import unittest
from pathlib import Path

from src.app import create_app
from src.app.assets import asset_absolute_path, attach_asset_to_message, store_asset
from src.app.models import Asset, ImportedConversation, ImportedMessage, MessageAsset
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class MessageAssetRouteTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "msg-assets-route")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self.addCleanup(self._restore_sqlite_uri)
        sqlite_path = self.workdir / "test.db"
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"
        self.app = create_app()
        self.app.instance_path = str(self.workdir)
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_sqlite_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _create_conversation_with_messages(
        self, source_id: str = "conv-msg-test", n_messages: int = 2
    ) -> tuple[int, list[int]]:
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id=source_id,
                title="Test Conversation",
                created_at_unix=1710000000.0,
                updated_at_unix=1710000500.0,
            )
            db.session.add(conv)
            db.session.flush()
            msg_ids = []
            for i in range(n_messages):
                msg = ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id=f"msg-{i:03d}",
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message {i} content.",
                    sequence_index=i,
                    created_at_unix=1710000100.0 + i,
                )
                db.session.add(msg)
                db.session.flush()
                msg_ids.append(msg.id)
            db.session.commit()
            return conv.id, msg_ids

    def test_upload_creates_one_asset_and_one_message_asset(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-upload-001")
        msg_id = msg_ids[0]
        data = b"test file content for message upload" * 10

        response = self.client.post(
            f"/imported/{conv_id}/messages/{msg_id}/attachments",
            data={"attachment_file": (io.BytesIO(data), "screenshot.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/imported/{conv_id}/explorer", response.headers["Location"])

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 1)
            self.assertEqual(MessageAsset.query.count(), 1)
            ma = MessageAsset.query.first()
            self.assertEqual(ma.message_id, msg_id)
            asset = Asset.query.first()
            abs_path = asset_absolute_path(asset, instance_root=Path(self.app.instance_path))
            self.assertTrue(abs_path.exists(), f"File not found at {abs_path}")

    def test_explorer_lists_attachment_under_correct_message(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-list-001", n_messages=2)
        msg_id = msg_ids[0]
        data = b"attachment for first message" * 5

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "evidence.pdf",
                "application/pdf",
                instance_root=Path(self.app.instance_path),
            )
            attach_asset_to_message(msg_id, asset.id)
            ma = MessageAsset.query.filter_by(message_id=msg_id, asset_id=asset.id).first()
            ma_id = ma.id

        response = self.client.get(f"/imported/{conv_id}/explorer")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn("evidence.pdf", html)
        expected_url = f"/imported/{conv_id}/messages/{msg_id}/attachments/{ma_id}/download"
        self.assertIn(expected_url, html)

    def test_attachment_does_not_appear_under_neighboring_messages(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-scope-001", n_messages=3)
        msg_id_0 = msg_ids[0]
        msg_id_1 = msg_ids[1]
        data = b"only for first message" * 8

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "scoped_evidence.txt",
                "text/plain",
                instance_root=Path(self.app.instance_path),
            )
            attach_asset_to_message(msg_id_0, asset.id)
            ma = MessageAsset.query.filter_by(message_id=msg_id_0, asset_id=asset.id).first()
            ma_id = ma.id

        response = self.client.get(f"/imported/{conv_id}/explorer")
        html = response.get_data(as_text=True)

        # Download URL scoped to message 0 must be present
        url_msg0 = f"/imported/{conv_id}/messages/{msg_id_0}/attachments/{ma_id}/download"
        self.assertIn(url_msg0, html)

        # No download URL should reference message 1 for this asset
        url_msg1 = f"/imported/{conv_id}/messages/{msg_id_1}/attachments/{ma_id}/download"
        self.assertNotIn(url_msg1, html)

    def test_duplicate_upload_same_message_does_not_create_duplicate_rows(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-dedup-001")
        msg_id = msg_ids[0]
        data = b"identical content for dedup" * 8

        self.client.post(
            f"/imported/{conv_id}/messages/{msg_id}/attachments",
            data={"attachment_file": (io.BytesIO(data), "dedup.txt")},
            content_type="multipart/form-data",
        )
        self.client.post(
            f"/imported/{conv_id}/messages/{msg_id}/attachments",
            data={"attachment_file": (io.BytesIO(data), "dedup.txt")},
            content_type="multipart/form-data",
        )

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 1)
            self.assertEqual(
                MessageAsset.query.filter_by(message_id=msg_id).count(), 1
            )

        response = self.client.get(f"/imported/{conv_id}/explorer")
        html = response.get_data(as_text=True)
        download_links = re.findall(
            rf"/imported/{conv_id}/messages/{msg_id}/attachments/\d+/download", html
        )
        self.assertEqual(len(download_links), 1)

    def test_same_bytes_on_different_messages_reuses_asset_creates_separate_message_assets(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-two-msgs-001", n_messages=2)
        msg_id_0 = msg_ids[0]
        msg_id_1 = msg_ids[1]
        data = b"shared bytes across two messages" * 6

        self.client.post(
            f"/imported/{conv_id}/messages/{msg_id_0}/attachments",
            data={"attachment_file": (io.BytesIO(data), "shared.pdf")},
            content_type="multipart/form-data",
        )
        self.client.post(
            f"/imported/{conv_id}/messages/{msg_id_1}/attachments",
            data={"attachment_file": (io.BytesIO(data), "shared.pdf")},
            content_type="multipart/form-data",
        )

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 1)
            self.assertEqual(MessageAsset.query.count(), 2)
            bound_message_ids = {ma.message_id for ma in MessageAsset.query.all()}
            self.assertEqual(bound_message_ids, {msg_id_0, msg_id_1})

    def test_missing_file_redirects_with_error_and_creates_no_rows(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-nofile-001")
        msg_id = msg_ids[0]

        response = self.client.post(
            f"/imported/{conv_id}/messages/{msg_id}/attachments",
            data={},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Choose a file before attaching", html)

        with self.app.app_context():
            self.assertEqual(Asset.query.count(), 0)
            self.assertEqual(MessageAsset.query.count(), 0)

    def test_download_returns_bytes_and_original_filename(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-dl-001")
        msg_id = msg_ids[0]
        data = b"downloadable message attachment bytes" * 12

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "report.pdf",
                "application/pdf",
                instance_root=Path(self.app.instance_path),
            )
            ma = attach_asset_to_message(msg_id, asset.id)
            ma_id = ma.id

        response = self.client.get(
            f"/imported/{conv_id}/messages/{msg_id}/attachments/{ma_id}/download"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, data)
        content_disposition = response.headers.get("Content-Disposition", "")
        self.assertIn("report.pdf", content_disposition)

    def test_download_from_wrong_conversation_returns_404(self):
        conv_a_id, msg_ids_a = self._create_conversation_with_messages("conv-scope-a-001")
        conv_b_id, _ = self._create_conversation_with_messages("conv-scope-b-001")
        msg_id = msg_ids_a[0]
        data = b"scoped content" * 8

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "scoped.txt",
                "text/plain",
                instance_root=Path(self.app.instance_path),
            )
            ma = attach_asset_to_message(msg_id, asset.id)
            ma_id = ma.id

        response = self.client.get(
            f"/imported/{conv_b_id}/messages/{msg_id}/attachments/{ma_id}/download"
        )
        self.assertEqual(response.status_code, 404)

    def test_download_from_wrong_message_returns_404(self):
        conv_id, msg_ids = self._create_conversation_with_messages("conv-wrong-msg-001", n_messages=2)
        msg_id_0 = msg_ids[0]
        msg_id_1 = msg_ids[1]
        data = b"message scoped attachment" * 8

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "msg0_only.txt",
                "text/plain",
                instance_root=Path(self.app.instance_path),
            )
            ma = attach_asset_to_message(msg_id_0, asset.id)
            ma_id = ma.id

        # ma_id is linked to msg_id_0; passing msg_id_1 must return 404
        response = self.client.get(
            f"/imported/{conv_id}/messages/{msg_id_1}/attachments/{ma_id}/download"
        )
        self.assertEqual(response.status_code, 404)

    def test_upload_to_message_outside_conversation_returns_404(self):
        conv_a_id, _ = self._create_conversation_with_messages("conv-cross-a-001")
        _, msg_ids_b = self._create_conversation_with_messages("conv-cross-b-001")
        msg_id_from_b = msg_ids_b[0]
        data = b"cross-conversation attachment attempt" * 5

        response = self.client.post(
            f"/imported/{conv_a_id}/messages/{msg_id_from_b}/attachments",
            data={"attachment_file": (io.BytesIO(data), "cross.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 404)


    def test_db_constraint_prevents_duplicate_message_asset_rows(self):
        """DB-level uniqueness: direct double-insert raises IntegrityError, leaving one row."""
        from sqlalchemy.exc import IntegrityError as _IntegrityError

        conv_id, msg_ids = self._create_conversation_with_messages("conv-constraint-001")
        msg_id = msg_ids[0]
        data = b"constraint test content" * 6

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "constraint_test.txt",
                "text/plain",
                instance_root=Path(self.app.instance_path),
            )
            attach_asset_to_message(msg_id, asset.id)
            with self.assertRaises(_IntegrityError):
                attach_asset_to_message(msg_id, asset.id)

        with self.app.app_context():
            self.assertEqual(
                MessageAsset.query.filter_by(message_id=msg_id).count(), 1
            )

    def test_same_asset_different_messages_not_constrained(self):
        """Constraint is per (message_id, asset_id) — different messages are allowed."""
        conv_id, msg_ids = self._create_conversation_with_messages("conv-multi-msg-001", n_messages=2)
        msg_id_0 = msg_ids[0]
        msg_id_1 = msg_ids[1]
        data = b"shared asset different messages" * 6

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "shared_asset.txt",
                "text/plain",
                instance_root=Path(self.app.instance_path),
            )
            attach_asset_to_message(msg_id_0, asset.id)
            attach_asset_to_message(msg_id_1, asset.id)
            self.assertEqual(Asset.query.count(), 1)
            self.assertEqual(MessageAsset.query.count(), 2)


if __name__ == "__main__":
    unittest.main()
