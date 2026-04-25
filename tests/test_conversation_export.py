"""Tests for single-conversation markdown export."""

from __future__ import annotations

import io
import unittest
import zipfile
from pathlib import Path

from src.app import create_app
from src.app.models import (
    Asset,
    ConversationAsset,
    ImportedConversation,
    ImportedMessage,
    MessageAsset,
)
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


class ConversationExportAttachmentsTest(unittest.TestCase):
    """Attachment markdown markers in single-conversation export."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-export-attach")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_export_dir = Config.SOULPRINT_EXPORT_DIR
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/attach_export.db"
        Config.SOULPRINT_EXPORT_DIR = ""
        self.addCleanup(self._restore_config)

        self.app = create_app()
        self.instance_root = Path(self.app.instance_path)
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        self._physical_files: list[Path] = []
        self.addCleanup(self._remove_physical_files)

        with self.app.app_context():
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="attach-export-1",
                title="Test Attach Conversation",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            msg1 = ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m1",
                role="user",
                content="Message with attachment",
                sequence_index=0,
                created_at_unix=1700000000,
            )
            msg2 = ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m2",
                role="assistant",
                content="Response without attachment",
                sequence_index=1,
                created_at_unix=1700000100,
            )
            db.session.add_all([msg1, msg2])
            db.session.flush()
            self.conv_id = conv.id
            self.msg1_id = msg1.id
            self.msg2_id = msg2.id
            db.session.commit()

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_export_dir

    def _remove_physical_files(self):
        for p in self._physical_files:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass

    def _make_asset(self, sha_prefix: str, original_filename: str, mime_type: str) -> int:
        """Insert an Asset row and create the physical file on disk."""
        sha = (sha_prefix + "0" * 64)[:64]
        storage_path = f"assets/sha256/{sha[:2]}/{sha}-{original_filename}"
        asset = Asset(
            stable_id=f"asset:sha256:{sha}",
            sha256=sha,
            original_filename=original_filename,
            stored_filename=f"{sha}-{original_filename}",
            mime_type=mime_type,
            extension=Path(original_filename).suffix.lstrip(".") or None,
            size_bytes=1024,
            storage_path=storage_path,
            uploaded_at_unix=1700000001.0,
            source="manual",
            parse_status="unparsed",
            parse_error=None,
        )
        db.session.add(asset)
        db.session.flush()
        physical = self.instance_root / storage_path
        physical.parent.mkdir(parents=True, exist_ok=True)
        physical.write_bytes(b"dummy")
        self._physical_files.append(physical)
        return asset.id

    def _get_markdown(self, response) -> str:
        """Return the markdown text from a text/markdown or zip response."""
        if "application/zip" in response.content_type:
            with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
                md_name = next(n for n in zf.namelist() if n.endswith(".md"))
                return zf.read(md_name).decode("utf-8")
        return response.data.decode("utf-8")

    def test_no_attachments_preserves_previous_behavior(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = response.data.decode("utf-8")
        self.assertIn("# Test Attach Conversation", text)
        self.assertIn("Message with attachment", text)
        self.assertNotIn("## Attachments", text)
        self.assertNotIn("#### Attachments", text)

    def test_conversation_level_attachment_section_near_top(self):
        with self.app.app_context():
            asset_id = self._make_asset("abcdef1234", "source.pdf", "application/pdf")
            db.session.add(ConversationAsset(
                conversation_id=self.conv_id,
                asset_id=asset_id,
                role="context",
                note="",
                attached_at_unix=1700000002.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        self.assertIn("## Attachments", text)
        attach_idx = text.index("## Attachments")
        first_msg_idx = text.index("### User")
        self.assertLess(attach_idx, first_msg_idx)
        self.assertIn("source.pdf", text)
        self.assertIn("application/pdf", text)
        self.assertIn("conversation", text)

    def test_conversation_attachment_link_uses_assets_stem(self):
        with self.app.app_context():
            asset_id = self._make_asset("abcdef5678", "source.pdf", "application/pdf")
            db.session.add(ConversationAsset(
                conversation_id=self.conv_id,
                asset_id=asset_id,
                role="context",
                note="",
                attached_at_unix=1700000002.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        # sha_prefix "abcdef5678" → sha[:12] = "abcdef567800"
        self.assertIn("[[Test Attach Conversation.assets/abcdef567800-source.pdf]]", text)

    def test_message_level_attachment_appears_under_correct_message(self):
        with self.app.app_context():
            asset_id = self._make_asset("deadbeef12", "screenshot.png", "image/png")
            db.session.add(MessageAsset(
                message_id=self.msg1_id,
                asset_id=asset_id,
                placement="after_message_content",
                caption="",
                attached_at_unix=1700000003.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        self.assertIn("#### Attachments", text)
        # sha_prefix "deadbeef12" → sha[:12] = "deadbeef1200"
        self.assertIn("msg-000-deadbeef1200-screenshot.png", text)

    def test_message_level_attachment_not_under_neighboring_message(self):
        with self.app.app_context():
            asset_id = self._make_asset("cafebabe12", "screenshot.png", "image/png")
            db.session.add(MessageAsset(
                message_id=self.msg1_id,
                asset_id=asset_id,
                placement="after_message_content",
                caption="",
                attached_at_unix=1700000003.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        # "#### Attachments" block appears exactly once — under msg1 only
        self.assertEqual(text.count("#### Attachments"), 1)
        # sha_prefix "cafebabe12" → sha[:12] = "cafebabe1200"
        attach_pos = text.index("msg-000-cafebabe1200-screenshot.png")
        msg2_pos = text.index("Response without attachment")
        self.assertLess(attach_pos, msg2_pos)

    def test_no_absolute_path_in_export_output(self):
        with self.app.app_context():
            asset_id = self._make_asset("aabbcc1234", "report.pdf", "application/pdf")
            db.session.add(MessageAsset(
                message_id=self.msg1_id,
                asset_id=asset_id,
                placement="after_message_content",
                caption="",
                attached_at_unix=1700000003.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        self.assertNotIn(str(self.workdir), text)

    def test_two_conversation_assets_same_filename_produce_distinct_links(self):
        with self.app.app_context():
            asset_id_1 = self._make_asset("aaaa111111", "report.pdf", "application/pdf")
            asset_id_2 = self._make_asset("bbbb222222", "report.pdf", "application/pdf")
            db.session.add(ConversationAsset(
                conversation_id=self.conv_id,
                asset_id=asset_id_1,
                role="context",
                note="",
                attached_at_unix=1700000010.0,
            ))
            db.session.add(ConversationAsset(
                conversation_id=self.conv_id,
                asset_id=asset_id_2,
                role="context",
                note="",
                attached_at_unix=1700000020.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        # sha_prefix "aaaa111111" → sha[:12] = "aaaa11111100"
        # sha_prefix "bbbb222222" → sha[:12] = "bbbb22222200"
        link_1 = "[[Test Attach Conversation.assets/aaaa11111100-report.pdf]]"
        link_2 = "[[Test Attach Conversation.assets/bbbb22222200-report.pdf]]"
        self.assertIn(link_1, text)
        self.assertIn(link_2, text)

    def test_two_message_assets_same_filename_produce_distinct_links(self):
        with self.app.app_context():
            asset_id_1 = self._make_asset("cccc333333", "notes.txt", "text/plain")
            asset_id_2 = self._make_asset("dddd444444", "notes.txt", "text/plain")
            db.session.add(MessageAsset(
                message_id=self.msg1_id,
                asset_id=asset_id_1,
                placement="after_message_content",
                caption="",
                attached_at_unix=1700000010.0,
            ))
            db.session.add(MessageAsset(
                message_id=self.msg1_id,
                asset_id=asset_id_2,
                placement="after_message_content",
                caption="",
                attached_at_unix=1700000020.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        # sha_prefix "cccc333333" → sha[:12] = "cccc33333300"
        # sha_prefix "dddd444444" → sha[:12] = "dddd44444400"
        link_1 = "[[Test Attach Conversation.assets/msg-000-cccc33333300-notes.txt]]"
        link_2 = "[[Test Attach Conversation.assets/msg-000-dddd44444400-notes.txt]]"
        self.assertIn(link_1, text)
        self.assertIn(link_2, text)

    def test_attachment_marker_ordering_is_deterministic(self):
        with self.app.app_context():
            # Insert the late attachment first to confirm sort ignores insertion order
            asset_id_late = self._make_asset("ffff666666", "late.pdf", "application/pdf")
            asset_id_early = self._make_asset("eeee555555", "early.pdf", "application/pdf")
            db.session.add(ConversationAsset(
                conversation_id=self.conv_id,
                asset_id=asset_id_late,
                role="context",
                note="",
                attached_at_unix=1700000020.0,
            ))
            db.session.add(ConversationAsset(
                conversation_id=self.conv_id,
                asset_id=asset_id_early,
                role="context",
                note="",
                attached_at_unix=1700000010.0,
            ))
            db.session.commit()

        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 200)
        text = self._get_markdown(response)
        # sha_prefix "eeee555555" → sha[:12] = "eeee55555500"
        # sha_prefix "ffff666666" → sha[:12] = "ffff66666600"
        early_pos = text.index("eeee55555500-early.pdf")
        late_pos = text.index("ffff66666600-late.pdf")
        self.assertLess(early_pos, late_pos)


class ConversationExportDirectoryBundleTest(unittest.TestCase):
    """Directory export writes .assets/ folder with copied files and manifest.json."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-dir-bundle")
        self.export_dir = self.workdir / "vault"
        self.export_dir.mkdir()

        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_export_dir = Config.SOULPRINT_EXPORT_DIR
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/bundle.db"
        Config.SOULPRINT_EXPORT_DIR = str(self.export_dir)
        self.addCleanup(self._restore_config)

        self.app = create_app()
        self.instance_root = Path(self.app.instance_path)
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        self._physical_files: list[Path] = []
        self.addCleanup(self._remove_physical_files)

        # sha designed so sha[:2] == "aa"
        self._sha = ("aa" + "bb" * 31)[:64]
        self._storage_path = f"assets/sha256/aa/{self._sha}-report.pdf"

        with self.app.app_context():
            db.create_all()
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="bundle-conv-1",
                title="Bundle Test",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            msg = ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m1",
                role="user",
                content="Message content",
                sequence_index=0,
                created_at_unix=1700000000,
            )
            db.session.add(msg)
            db.session.flush()
            asset = Asset(
                stable_id=f"asset:sha256:{self._sha}",
                sha256=self._sha,
                original_filename="report.pdf",
                stored_filename=f"{self._sha}-report.pdf",
                mime_type="application/pdf",
                extension="pdf",
                size_bytes=9,
                storage_path=self._storage_path,
                uploaded_at_unix=1700000001.0,
                source="manual",
                parse_status="unparsed",
                parse_error=None,
            )
            db.session.add(asset)
            db.session.flush()
            db.session.add(ConversationAsset(
                conversation_id=conv.id,
                asset_id=asset.id,
                role="context",
                note="",
                attached_at_unix=1700000002.0,
            ))
            db.session.commit()
            self.conv_id = conv.id

        # Create the physical asset file under app.instance_path
        physical = self.instance_root / self._storage_path
        physical.parent.mkdir(parents=True, exist_ok=True)
        physical.write_bytes(b"pdf bytes")
        self._physical_files.append(physical)

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_export_dir

    def _remove_physical_files(self):
        for p in self._physical_files:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass

    def test_directory_export_creates_assets_folder(self):
        response = self.client.get(f"/imported/{self.conv_id}/export")
        self.assertEqual(response.status_code, 302)
        assets_dir = self.export_dir / "Bundle Test.assets"
        self.assertTrue(assets_dir.is_dir())

    def test_copied_filename_matches_markdown_marker(self):
        self.client.get(f"/imported/{self.conv_id}/export")
        assets_dir = self.export_dir / "Bundle Test.assets"
        expected_name = f"{self._sha[:12]}-report.pdf"
        self.assertTrue((assets_dir / expected_name).exists())

    def test_manifest_json_exists_with_expected_fields(self):
        import json as _json
        self.client.get(f"/imported/{self.conv_id}/export")
        manifest_path = self.export_dir / "Bundle Test.assets" / "manifest.json"
        self.assertTrue(manifest_path.exists())
        manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "soulprint.attachments.v1")
        self.assertEqual(manifest["source"], "chatgpt")
        self.assertEqual(manifest["title"], "Bundle Test")
        self.assertEqual(manifest["exported_from"], "SoulPrint")
        self.assertEqual(len(manifest["assets"]), 1)
        row = manifest["assets"][0]
        self.assertEqual(row["relationship"], "conversation")
        self.assertEqual(row["original_filename"], "report.pdf")
        self.assertIn("sha256", row)
        self.assertIn("asset_id", row)

    def test_manifest_contains_no_absolute_paths(self):
        self.client.get(f"/imported/{self.conv_id}/export")
        manifest_path = self.export_dir / "Bundle Test.assets" / "manifest.json"
        text = manifest_path.read_text(encoding="utf-8")
        self.assertNotIn(str(self.instance_root), text)
        self.assertNotIn(str(self.export_dir), text)

    def test_no_assets_folder_for_conversation_without_attachments(self):
        with self.app.app_context():
            conv2 = ImportedConversation(
                source="chatgpt",
                source_conversation_id="no-attach",
                title="No Attachments",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv2)
            db.session.flush()
            db.session.add(ImportedMessage(
                conversation_id=conv2.id,
                source_message_id="m1",
                role="user",
                content="hi",
                sequence_index=0,
                created_at_unix=1700000000,
            ))
            db.session.commit()
            conv2_id = conv2.id

        self.client.get(f"/imported/{conv2_id}/export")
        self.assertFalse((self.export_dir / "No Attachments.assets").exists())

    def test_missing_physical_asset_reports_error_not_silent(self):
        for p in self._physical_files:
            p.unlink(missing_ok=True)

        response = self.client.get(
            f"/imported/{self.conv_id}/export",
            follow_redirects=False,
        )
        # Must redirect with error, not 500
        self.assertEqual(response.status_code, 302)
        followed = self.client.get("/imported")
        body = followed.get_data(as_text=True)
        # The export_error flash message should describe the failure
        self.assertIn("report.pdf", body)

    def test_message_level_asset_bundle_uses_msg_prefix(self):
        """Message-level attachment: copied name uses msg-NNN- prefix."""
        import json as _json
        sha2 = ("cc" + "dd" * 31)[:64]
        storage2 = f"assets/sha256/cc/{sha2}-screenshot.png"
        with self.app.app_context():
            conv3 = ImportedConversation(
                source="claude",
                source_conversation_id="msg-bundle-conv",
                title="Msg Bundle",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv3)
            db.session.flush()
            msg3 = ImportedMessage(
                conversation_id=conv3.id,
                source_message_id="m1",
                role="user",
                content="content",
                sequence_index=0,
                created_at_unix=1700000000,
            )
            db.session.add(msg3)
            db.session.flush()
            asset3 = Asset(
                stable_id=f"asset:sha256:{sha2}",
                sha256=sha2,
                original_filename="screenshot.png",
                stored_filename=f"{sha2}-screenshot.png",
                mime_type="image/png",
                extension="png",
                size_bytes=5,
                storage_path=storage2,
                uploaded_at_unix=1700000010.0,
                source="manual",
                parse_status="unparsed",
                parse_error=None,
            )
            db.session.add(asset3)
            db.session.flush()
            db.session.add(MessageAsset(
                message_id=msg3.id,
                asset_id=asset3.id,
                placement="after_message_content",
                caption="",
                attached_at_unix=1700000011.0,
            ))
            db.session.commit()
            conv3_id = conv3.id

        physical3 = self.instance_root / storage2
        physical3.parent.mkdir(parents=True, exist_ok=True)
        physical3.write_bytes(b"png bytes")
        self._physical_files.append(physical3)

        self.client.get(f"/imported/{conv3_id}/export")
        assets_dir = self.export_dir / "Msg Bundle.assets"
        expected_name = f"msg-000-{sha2[:12]}-screenshot.png"
        self.assertTrue((assets_dir / expected_name).exists())

        manifest = _json.loads((assets_dir / "manifest.json").read_text())
        row = manifest["assets"][0]
        self.assertEqual(row["relationship"], "message")
        self.assertIn("message_sequence_index", row)
        self.assertEqual(row["message_sequence_index"], 0)


class ConversationExportBrowserBundleTest(unittest.TestCase):
    """Browser download returns .zip bundle when conversation has attachments."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "conv-browser-bundle")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_export_dir = Config.SOULPRINT_EXPORT_DIR
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.workdir}/browser_bundle.db"
        Config.SOULPRINT_EXPORT_DIR = ""
        self.addCleanup(self._restore_config)

        self.app = create_app()
        self.instance_root = Path(self.app.instance_path)
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        self._physical_files: list[Path] = []
        self.addCleanup(self._remove_physical_files)

        self._sha = ("aa" + "bb" * 31)[:64]
        self._storage_path = f"assets/sha256/aa/{self._sha}-report.pdf"

        with self.app.app_context():
            db.create_all()

            # Conversation with a conv-level asset
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="browser-bundle-1",
                title="Bundle Download Test",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv)
            db.session.flush()
            db.session.add(ImportedMessage(
                conversation_id=conv.id,
                source_message_id="m1",
                role="user",
                content="message content",
                sequence_index=0,
                created_at_unix=1700000000,
            ))
            db.session.flush()
            asset = Asset(
                stable_id=f"asset:sha256:{self._sha}",
                sha256=self._sha,
                original_filename="report.pdf",
                stored_filename=f"{self._sha}-report.pdf",
                mime_type="application/pdf",
                extension="pdf",
                size_bytes=9,
                storage_path=self._storage_path,
                uploaded_at_unix=1700000001.0,
                source="manual",
                parse_status="unparsed",
                parse_error=None,
            )
            db.session.add(asset)
            db.session.flush()
            db.session.add(ConversationAsset(
                conversation_id=conv.id,
                asset_id=asset.id,
                role="context",
                note="",
                attached_at_unix=1700000002.0,
            ))
            db.session.commit()
            self.conv_with_asset_id = conv.id

            # Conversation without attachments
            conv2 = ImportedConversation(
                source="chatgpt",
                source_conversation_id="browser-bundle-2",
                title="No Attachment Download",
                created_at_unix=1700000000,
                updated_at_unix=1700001000,
            )
            db.session.add(conv2)
            db.session.flush()
            db.session.add(ImportedMessage(
                conversation_id=conv2.id,
                source_message_id="m2",
                role="user",
                content="no files",
                sequence_index=0,
                created_at_unix=1700000000,
            ))
            db.session.commit()
            self.conv_no_asset_id = conv2.id

        physical = self.instance_root / self._storage_path
        physical.parent.mkdir(parents=True, exist_ok=True)
        physical.write_bytes(b"pdf bytes")
        self._physical_files.append(physical)

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_export_dir

    def _remove_physical_files(self):
        for p in self._physical_files:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass

    def test_no_attachment_returns_plain_markdown(self):
        response = self.client.get(f"/imported/{self.conv_no_asset_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.content_type)
        self.assertIn(".md", response.headers.get("Content-Disposition", ""))

    def test_with_attachment_returns_zip(self):
        response = self.client.get(f"/imported/{self.conv_with_asset_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")
        self.assertIn(".zip", response.headers.get("Content-Disposition", ""))

    def test_zip_contains_markdown_assets_and_manifest(self):
        response = self.client.get(f"/imported/{self.conv_with_asset_id}/export")
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            names = zf.namelist()
        self.assertTrue(any(n.endswith(".md") for n in names), f"No .md in zip: {names}")
        self.assertTrue(any("manifest.json" in n for n in names), f"No manifest in zip: {names}")
        self.assertTrue(any("report.pdf" in n for n in names), f"No report.pdf in zip: {names}")

    def test_zip_copied_filename_matches_markdown_marker(self):
        response = self.client.get(f"/imported/{self.conv_with_asset_id}/export")
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            names = zf.namelist()
            md_name = next(n for n in names if n.endswith(".md"))
            md_content = zf.read(md_name).decode("utf-8")
        expected_filename = f"{self._sha[:12]}-report.pdf"
        self.assertIn(expected_filename, md_content)
        self.assertTrue(
            any(expected_filename in n for n in names),
            f"Expected zip entry containing {expected_filename!r}, got: {names}",
        )

    def test_zip_manifest_contains_no_absolute_paths(self):
        import json as _json
        response = self.client.get(f"/imported/{self.conv_with_asset_id}/export")
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            manifest_entry = next(n for n in zf.namelist() if n.endswith("manifest.json"))
            manifest_text = zf.read(manifest_entry).decode("utf-8")
        self.assertNotIn(str(self.instance_root), manifest_text)
        self.assertNotIn(str(self.workdir), manifest_text)
        manifest = _json.loads(manifest_text)
        self.assertEqual(manifest["schema"], "soulprint.attachments.v1")
        self.assertEqual(len(manifest["assets"]), 1)

    def test_missing_physical_file_returns_error_redirect(self):
        for p in self._physical_files:
            p.unlink(missing_ok=True)
        response = self.client.get(
            f"/imported/{self.conv_with_asset_id}/export",
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        followed = self.client.get("/imported")
        self.assertIn("report.pdf", followed.get_data(as_text=True))
