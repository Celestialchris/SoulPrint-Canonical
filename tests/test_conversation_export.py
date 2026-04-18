"""Tests for single-conversation markdown export."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.app import create_app
from src.app.models import ImportedConversation, ImportedMessage
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class TestConversationExport(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-export")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_export_dir = Config.SOULPRINT_EXPORT_DIR
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/export_test.db"
        Config.SOULPRINT_EXPORT_DIR = ""
        self.addCleanup(self._restore_config)

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        with self.app.app_context():
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="export-test-1",
                title="Test Export Conversation",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            msg1 = ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m1",
                role="user",
                content="Hello, how are you?",
                sequence_index=0,
                created_at_unix=1700000000,
            )
            msg2 = ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m2",
                role="assistant",
                content="I'm doing well, thanks for asking!",
                sequence_index=1,
                created_at_unix=1700000100,
            )
            db.session.add_all([msg1, msg2])
            db.session.commit()
            self.conv_id = conv.id

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_export_dir

    def test_export_returns_markdown(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)

    def test_export_contains_title(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("# Test Export Conversation", text)

    def test_export_contains_messages(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("Hello, how are you?", text)
        self.assertIn("I'm doing well, thanks for asking!", text)

    def test_export_contains_provider(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("**Provider:** chatgpt", text)

    def test_export_has_download_header(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))

    def test_export_404_for_nonexistent(self):
        response = self.client.get("/imported/99999/export")
        self.assertEqual(response.status_code, 404)


class TestConversationExportEdgeCases(unittest.TestCase):
    """Edge cases: missing title, null timestamps, filename sanitization."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-export-edge")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_export_dir = Config.SOULPRINT_EXPORT_DIR
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/edge.db"
        Config.SOULPRINT_EXPORT_DIR = ""
        self.addCleanup(self._restore_config)

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_export_dir

    def _create_conv(self, title: str, *, created=None, messages=None):
        with self.app.app_context():
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id=f"edge-{title or 'empty'}",
                title=title,
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            for i, (role, content, ts) in enumerate(messages or []):
                db.session.add(ImportedMessage(
                    conversation_id=conv.id,
                    source_message_id=f"m{i}",
                    role=role,
                    content=content,
                    sequence_index=i,
                    created_at_unix=ts,
                ))
            db.session.commit()
            return conv.id

    def test_empty_title_falls_back_to_untitled(self):
        conv_id = self._create_conv("", messages=[("user", "hi", 1700000000)])
        response = self.client.get(f"/imported/{conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = response.data.decode("utf-8")
        self.assertIn("# Untitled conversation", text)
        self.assertIn("Untitled conversation", response.headers["Content-Disposition"])

    def test_title_with_only_illegal_chars_uses_generic_filename(self):
        conv_id = self._create_conv("/<>", messages=[("user", "hi", 1700000000)])
        response = self.client.get(f"/imported/{conv_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn('filename="conversation.md"', response.headers["Content-Disposition"])

    def test_message_with_no_timestamp_has_no_italic_line(self):
        conv_id = self._create_conv("Plain", messages=[("user", "text", None)])
        response = self.client.get(f"/imported/{conv_id}/export")
        text = response.data.decode("utf-8")
        self.assertIn("### User", text)
        self.assertIn("text", text)
        lines = text.split("\n")
        user_idx = lines.index("### User")
        self.assertFalse(lines[user_idx + 1].startswith("*"))

    def test_epoch_zero_timestamp_still_emits_italic_line(self):
        conv_id = self._create_conv("Epoch", messages=[("user", "hi", 0)])
        response = self.client.get(f"/imported/{conv_id}/export")
        text = response.data.decode("utf-8")
        lines = text.split("\n")
        user_idx = lines.index("### User")
        self.assertTrue(
            lines[user_idx + 1].startswith("*"),
            f"Expected italic timestamp line for epoch=0, got: {lines[user_idx + 1]!r}",
        )

    def test_dots_in_title_are_preserved_in_filename(self):
        conv_id = self._create_conv(
            "My.notes.v2", messages=[("user", "hi", 1700000000)]
        )
        response = self.client.get(f"/imported/{conv_id}/export")
        dispo = response.headers["Content-Disposition"]
        self.assertIn("My.notes.v2.md", dispo)

    def test_special_chars_in_title_sanitized(self):
        conv_id = self._create_conv(
            "Project/Alpha: v2 <beta>",
            messages=[("user", "x", 1700000000)],
        )
        response = self.client.get(f"/imported/{conv_id}/export")
        dispo = response.headers["Content-Disposition"]
        self.assertNotIn("/", dispo.split("filename=")[1])
        self.assertNotIn("<", dispo)
        self.assertNotIn(">", dispo)
        self.assertIn(".md", dispo)

    def test_non_ascii_title_falls_back_to_generic_filename(self):
        conv_id = self._create_conv(
            "\u4f1a\u8a71\u30ed\u30b0", messages=[("user", "hi", 1700000000)]
        )
        response = self.client.get(f"/imported/{conv_id}/export")
        self.assertEqual(response.status_code, 200)
        dispo = response.headers["Content-Disposition"]
        self.assertIn('filename="conversation.md"', dispo)
        self.assertTrue(
            dispo.isascii(),
            f"Content-Disposition must be ASCII-only, got: {dispo!r}",
        )


class TestConversationExportFilesystemMode(unittest.TestCase):
    """Single-conv export when SOULPRINT_EXPORT_DIR points at a writable dir.

    Mirrors the multi-select directory-mode tests in test_multi_select_export.py.
    """

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-export-fs")
        self.export_dir = self.workdir / "vault_raw"
        self.export_dir.mkdir()

        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_export_dir = Config.SOULPRINT_EXPORT_DIR
        Config.SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{self.workdir}/fs_test.db"
        )
        Config.SOULPRINT_EXPORT_DIR = str(self.export_dir)
        self.addCleanup(self._restore_config)

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        with self.app.app_context():
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="fs-test-1",
                title="Vault Export",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            db.session.add(ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m1",
                role="user",
                content="filesystem mode check",
                sequence_index=0,
                created_at_unix=1700000000,
            ))
            db.session.commit()
            self.conv_id = conv.id

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_export_dir

    def test_filesystem_write_redirects_and_creates_file(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/imported"))

        written = list(self.export_dir.glob("*.md"))
        self.assertEqual(len(written), 1)
        body = written[0].read_text(encoding="utf-8")
        self.assertIn("# Vault Export", body)
        self.assertIn("filesystem mode check", body)

    def test_filesystem_write_sets_notice(self):
        with self.client.session_transaction() as sess:
            sess.clear()
        self.client.get(f"/imported/{self.conv_id}/export")
        with self.client.session_transaction() as sess:
            notice = sess.get("export_notice", "")
        self.assertIn("Vault Export", notice)
        self.assertIn(str(self.export_dir), notice)

    def test_filename_collision_uses_id_suffix(self):
        (self.export_dir / "Vault Export.md").write_text(
            "pre-existing", encoding="utf-8"
        )
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            (self.export_dir / "Vault Export.md").read_text(encoding="utf-8"),
            "pre-existing",
        )
        suffixed = self.export_dir / f"Vault Export-{self.conv_id}.md"
        self.assertTrue(suffixed.exists())
        self.assertIn("# Vault Export", suffixed.read_text(encoding="utf-8"))

    def test_nonexistent_export_dir_falls_back_to_download(self):
        bogus = str(self.workdir / "does_not_exist")
        Config.SOULPRINT_EXPORT_DIR = bogus
        self.app.config["SOULPRINT_EXPORT_DIR"] = bogus
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(
            "attachment",
            response.headers.get("Content-Disposition", ""),
        )

    def test_empty_export_dir_preserves_download_behavior(self):
        Config.SOULPRINT_EXPORT_DIR = ""
        self.app.config["SOULPRINT_EXPORT_DIR"] = ""
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(
            'filename="Vault Export.md"',
            response.headers["Content-Disposition"],
        )
        self.assertEqual(list(self.export_dir.glob("*.md")), [])

    def test_write_failure_falls_back_to_download(self):
        from unittest.mock import patch

        def _raise(*args, **kwargs):
            raise OSError("disk full")

        with patch.object(Path, "write_text", _raise):
            response = self.client.get(f"/imported/{self.conv_id}/export")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(
            "attachment",
            response.headers.get("Content-Disposition", ""),
        )
        body = response.data.decode("utf-8")
        self.assertIn("# Vault Export", body)
        self.assertEqual(list(self.export_dir.glob("*.md")), [])

    def test_write_failure_cleans_up_partial_tmp_file(self):
        """If write_text fails mid-write after creating a .tmp file on disk,
        atomic-rename logic must unlink the partial tmp so the vault never
        sees a corrupt artifact. The previous test uses a mock that raises
        BEFORE writing anything; this one writes partial bytes then fails,
        which is the realistic disk-full scenario the cleanup was built for.
        """
        from unittest.mock import patch

        def _partial_then_fail(self_path, content, encoding="utf-8"):
            # Write real partial bytes to disk, then simulate the disk
            # giving out before the write could finish.
            with open(self_path, "w", encoding=encoding) as fh:
                fh.write(content[: max(1, len(content) // 2)])
            raise OSError("simulated disk full mid-write")

        with patch.object(Path, "write_text", _partial_then_fail):
            response = self.client.get(f"/imported/{self.conv_id}/export")

        # Route falls back to the browser-download path on OSError.
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)

        # Neither the target file nor a leftover .tmp file should remain.
        leftovers = sorted(p.name for p in self.export_dir.iterdir())
        self.assertEqual(
            leftovers, [],
            f"expected empty export dir after OSError, found: {leftovers}",
        )
