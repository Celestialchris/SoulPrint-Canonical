"""Tests for Phase 1 asset ledger: schema, content-addressed storage, and relationship helpers."""

from __future__ import annotations

import hashlib
import io
import sqlite3
import unittest

from src.app import create_app
from src.app.assets import (
    asset_absolute_path,
    attach_asset_to_conversation,
    attach_asset_to_message,
    store_asset,
)
from src.app.models import Asset, ConversationAsset, ImportedConversation, ImportedMessage, MessageAsset
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _make_app(test_case, prefix: str):
    tmpdir = make_test_temp_dir(test_case, prefix)
    db_path = str(tmpdir / "test.db")
    old_uri = Config.SQLALCHEMY_DATABASE_URI
    Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    app = create_app()
    test_case.addCleanup(release_app_db_handles, app, drop_all=True)
    test_case.addCleanup(lambda: setattr(Config, "SQLALCHEMY_DATABASE_URI", old_uri))
    return app, tmpdir, db_path


def _seed_conversation(app) -> int:
    with app.app_context():
        conv = ImportedConversation(
            source="chatgpt",
            source_conversation_id="test-conv-001",
            title="Test Conversation",
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
        )
        db.session.add(conv)
        db.session.commit()
        return conv.id


def _seed_conversation_with_message(app) -> tuple[int, int]:
    with app.app_context():
        conv = ImportedConversation(
            source="chatgpt",
            source_conversation_id="test-conv-002",
            title="Conv With Message",
            created_at_unix=1710000000.0,
            updated_at_unix=1710001000.0,
        )
        db.session.add(conv)
        db.session.flush()
        msg = ImportedMessage(
            conversation_id=conv.id,
            source_message_id="msg-001",
            role="user",
            content="Analyze this screenshot.",
            sequence_index=0,
            created_at_unix=1710000100.0,
        )
        db.session.add(msg)
        db.session.commit()
        return conv.id, msg.id


class AssetsSchemaTest(unittest.TestCase):
    def setUp(self):
        self.app, self.tmpdir, self.db_path = _make_app(self, "schema")

    def test_asset_tables_exist_after_create_all(self):
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        finally:
            conn.close()
        table_names = {r[0] for r in rows}
        self.assertIn("asset", table_names)
        self.assertIn("conversation_asset", table_names)
        self.assertIn("message_asset", table_names)


class AssetsStoreTest(unittest.TestCase):
    def setUp(self):
        self.app, self.tmpdir, self.db_path = _make_app(self, "store")

    def test_store_asset_computes_sha256_and_metadata(self):
        data = bytes(range(50))
        expected_sha256 = hashlib.sha256(data).hexdigest()

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "report.pdf",
                "application/pdf",
                instance_root=self.tmpdir,
            )
            asset_id = asset.id
            stable_id = asset.stable_id
            sha256 = asset.sha256
            size_bytes = asset.size_bytes
            original_filename = asset.original_filename
            stored_filename = asset.stored_filename
            mime_type = asset.mime_type
            extension = asset.extension
            storage_path = asset.storage_path

        self.assertEqual(sha256, expected_sha256)
        self.assertEqual(size_bytes, 50)
        self.assertTrue(stable_id.startswith("asset:sha256:"))
        self.assertEqual(original_filename, "report.pdf")
        self.assertIn("report", stored_filename)
        self.assertTrue(stored_filename.endswith(".pdf"))
        self.assertEqual(mime_type, "application/pdf")
        self.assertEqual(extension, "pdf")
        self.assertTrue(storage_path.startswith("assets/sha256/"))

        with self.app.app_context():
            fetched = Asset.query.get(asset_id)
            abs_path = asset_absolute_path(fetched, instance_root=self.tmpdir)
        self.assertTrue(abs_path.exists())


class AssetsDeduplicationTest(unittest.TestCase):
    def setUp(self):
        self.app, self.tmpdir, self.db_path = _make_app(self, "dedup")

    def test_duplicate_bytes_reuse_asset_row_and_physical_file(self):
        data = b"deduplicated content for test" * 10

        with self.app.app_context():
            asset1 = store_asset(io.BytesIO(data), "first.txt", instance_root=self.tmpdir)
            asset2 = store_asset(io.BytesIO(data), "second.txt", instance_root=self.tmpdir)
            count = Asset.query.count()
            id1 = asset1.id
            id2 = asset2.id

        self.assertEqual(count, 1)
        self.assertEqual(id1, id2)

        sha256 = hashlib.sha256(data).hexdigest()
        prefix = sha256[:2]
        physical_files = list((self.tmpdir / "assets" / "sha256" / prefix).iterdir())
        self.assertEqual(len(physical_files), 1)


class AssetsSameAssetTwoConversationsTest(unittest.TestCase):
    def setUp(self):
        self.app, self.tmpdir, self.db_path = _make_app(self, "two-convs")

    def test_same_asset_can_attach_to_two_conversations(self):
        data = b"shared context document" * 5

        with self.app.app_context():
            conv1 = ImportedConversation(
                source="chatgpt", source_conversation_id="conv-a",
                title="Conv A", created_at_unix=1710000000.0, updated_at_unix=1710001000.0,
            )
            conv2 = ImportedConversation(
                source="claude", source_conversation_id="conv-b",
                title="Conv B", created_at_unix=1710000000.0, updated_at_unix=1710001000.0,
            )
            db.session.add(conv1)
            db.session.add(conv2)
            db.session.commit()
            conv1_id = conv1.id
            conv2_id = conv2.id

        with self.app.app_context():
            asset = store_asset(io.BytesIO(data), "notes.pdf", instance_root=self.tmpdir)
            asset_id = asset.id
            attach_asset_to_conversation(conv1_id, asset_id)
            attach_asset_to_conversation(conv2_id, asset_id)
            ca_count = ConversationAsset.query.count()
            a_count = Asset.query.count()
            ca_rows = ConversationAsset.query.all()
            asset_ids = {r.asset_id for r in ca_rows}

        self.assertEqual(ca_count, 2)
        self.assertEqual(a_count, 1)
        self.assertEqual(asset_ids, {asset_id})


class AssetsMessageAttachTest(unittest.TestCase):
    def setUp(self):
        self.app, self.tmpdir, self.db_path = _make_app(self, "msg-attach")

    def test_asset_can_attach_to_message(self):
        conv_id, msg_id = _seed_conversation_with_message(self.app)
        data = b"screenshot bytes" * 20

        with self.app.app_context():
            asset = store_asset(io.BytesIO(data), "screenshot.png", "image/png", instance_root=self.tmpdir)
            attach_asset_to_message(
                msg_id, asset.id,
                placement="after_message_content",
                caption="Test caption",
            )
            count = MessageAsset.query.count()
            row = MessageAsset.query.first()
            placement = row.placement
            caption = row.caption

        self.assertEqual(count, 1)
        self.assertEqual(placement, "after_message_content")
        self.assertEqual(caption, "Test caption")


class AssetsMetadataOnlyTest(unittest.TestCase):
    def setUp(self):
        self.app, self.tmpdir, self.db_path = _make_app(self, "meta-only")

    def test_database_stores_metadata_not_file_bytes(self):
        distinctive = b"\xCA\xFE\xBA\xBE" * 200

        with self.app.app_context():
            store_asset(io.BytesIO(distinctive), "binary.bin", instance_root=self.tmpdir)

        conn = sqlite3.connect(self.db_path)
        try:
            columns = [
                row[1] for row in conn.execute("PRAGMA table_info(asset)").fetchall()
            ]
            row = conn.execute("SELECT * FROM asset LIMIT 1").fetchone()
        finally:
            conn.close()

        forbidden_col_names = {"data", "bytes", "content", "blob"}
        for col in columns:
            self.assertNotIn(col.lower(), forbidden_col_names, f"Forbidden column found: {col}")

        if row:
            for value in row:
                if isinstance(value, (bytes, bytearray)):
                    self.assertNotIn(b"\xCA\xFE", value)
                elif isinstance(value, str):
                    self.assertNotIn("\xca\xfe", value)


class AssetsSanitizationTest(unittest.TestCase):
    def setUp(self):
        self.app, self.tmpdir, self.db_path = _make_app(self, "sanitize")

    def test_filename_sanitization_blocks_path_traversal(self):
        data = b"safe content" * 10

        with self.app.app_context():
            asset = store_asset(
                io.BytesIO(data),
                "../evil/../../report?.pdf",
                instance_root=self.tmpdir,
            )
            stored_filename = asset.stored_filename
            storage_path = asset.storage_path
            abs_path = asset_absolute_path(asset, instance_root=self.tmpdir)

        root = self.tmpdir.resolve()
        self.assertTrue(
            str(abs_path).startswith(str(root)),
            f"Path escaped root: {abs_path}",
        )
        self.assertNotIn("/", stored_filename)
        self.assertNotIn("\\", stored_filename)
        self.assertNotIn("..", stored_filename)
        self.assertTrue(storage_path.startswith("assets/sha256/"))


if __name__ == "__main__":
    unittest.main()
