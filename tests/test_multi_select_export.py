"""Tests for the multi-select export route on /imported.

Covers both output modes:
- zip mode: default when SOULPRINT_EXPORT_DIR is unset or points at a
  non-existent path. Returns a .zip download.
- directory mode: SOULPRINT_EXPORT_DIR set to a real directory. Writes
  .md files directly to that path and redirects to /imported.
"""

from __future__ import annotations

import io
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

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


def _seed_conversations(app) -> dict[str, int]:
    """Seed three conversations (two share a title for collision tests)."""

    with app.app_context():
        a = ImportedConversation(
            source="chatgpt",
            source_conversation_id="conv-a",
            title="Shared title",
            created_at_unix=1710000000.0,
            updated_at_unix=1710000500.0,
        )
        b = ImportedConversation(
            source="claude",
            source_conversation_id="conv-b",
            title="Shared title",  # intentional collision with A
            created_at_unix=1710001000.0,
            updated_at_unix=1710001500.0,
        )
        c = ImportedConversation(
            source="gemini",
            source_conversation_id="conv-c",
            title="Unique title",
            created_at_unix=1710002000.0,
            updated_at_unix=1710002500.0,
        )
        db.session.add_all([a, b, c])
        db.session.flush()

        db.session.add_all([
            ImportedMessage(
                conversation_id=a.id,
                source_message_id="a-0",
                role="user",
                content="A message from conversation A.",
                sequence_index=0,
                created_at_unix=1710000001.0,
            ),
            ImportedMessage(
                conversation_id=b.id,
                source_message_id="b-0",
                role="assistant",
                content="B message.",
                sequence_index=0,
                created_at_unix=1710001001.0,
            ),
            ImportedMessage(
                conversation_id=c.id,
                source_message_id="c-0",
                role="user",
                content="C message.",
                sequence_index=0,
                created_at_unix=1710002001.0,
            ),
        ])
        db.session.commit()
        return {"a": a.id, "b": b.id, "c": c.id}


class MultiSelectExportTest(unittest.TestCase):
    def setUp(self):
        self.workdir = make_test_temp_dir(self, "multi-export")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_dir = Config.SOULPRINT_EXPORT_DIR
        self.addCleanup(self._restore_config)

        Config.SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{(self.workdir / 'export_test.db').as_posix()}"
        )
        Config.SOULPRINT_EXPORT_DIR = ""

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        self.ids = _seed_conversations(self.app)

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_dir

    # 1 — zip mode returns a valid zip with the expected .md files inside
    def test_export_selected_zip_mode(self):
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["c"])]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")
        self.assertIn(
            'filename="soulprint-export-2.zip"',
            response.headers.get("Content-Disposition", ""),
        )

        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 2)
            for name in names:
                self.assertTrue(name.endswith(".md"))
                body = zf.read(name).decode("utf-8")
                self.assertIn("**Provider:**", body)
                self.assertIn("**Exported from:** SoulPrint", body)

    # 2 — directory mode writes files to disk and redirects with a notice
    def test_export_selected_directory_mode(self):
        # Swap the app out for one whose config already points at the export dir
        release_app_db_handles(self.app, drop_all=True)
        export_dir = make_test_temp_dir(self, "export-dest")
        Config.SOULPRINT_EXPORT_DIR = str(export_dir)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.ids = _seed_conversations(self.app)

        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["c"])]},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/imported", response.headers["Location"])

        md_files = sorted(export_dir.glob("*.md"))
        self.assertEqual(len(md_files), 2)

        body = md_files[0].read_text(encoding="utf-8")
        self.assertIn("**Provider:**", body)
        self.assertIn("**Created:**", body)
        self.assertIn("**Exported from:** SoulPrint", body)

        # Notice should appear after following the redirect back to /imported
        followed = self.client.get("/imported")
        self.assertEqual(followed.status_code, 200)
        self.assertIn("Exported 2 conversations to", followed.get_data(as_text=True))

    # 3 — empty selection produces a redirect + visible error on /imported
    def test_export_selected_empty_selection(self):
        response = self.client.post(
            "/imported/export-selected",
            data={},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/imported", response.headers["Location"])

        followed = self.client.get("/imported")
        self.assertIn("No conversations selected", followed.get_data(as_text=True))

    # 4 — invalid / non-existent ids are silently skipped
    def test_export_selected_invalid_ids_skipped(self):
        payload = [str(self.ids["a"]), "not-a-number", "99999"]
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": payload},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            self.assertEqual(len(zf.namelist()), 1)

    # 5 — two conversations with the same title get disambiguated filenames
    def test_export_selected_filename_collision(self):
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["b"])]},
        )

        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 2)
            self.assertEqual(len(set(names)), 2)  # names are distinct
            # The second conversation's filename should carry its id suffix
            suffixed = [n for n in names if f"-{self.ids['b']}.md" in n]
            self.assertEqual(len(suffixed), 1)

    # 6 — nonexistent export dir falls back to zip mode rather than crashing
    def test_export_selected_nonexistent_dir(self):
        bogus = str(self.workdir / "does-not-exist")
        release_app_db_handles(self.app, drop_all=True)
        Config.SOULPRINT_EXPORT_DIR = bogus
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.ids = _seed_conversations(self.app)

        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["c"])]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")

    # 7 — OSError during dir-mode write degrades gracefully (no 500)
    def test_export_selected_dir_write_failure(self):
        release_app_db_handles(self.app, drop_all=True)
        export_dir = make_test_temp_dir(self, "export-dest-fail")
        Config.SOULPRINT_EXPORT_DIR = str(export_dir)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.ids = _seed_conversations(self.app)

        with patch(
            "pathlib.Path.write_text",
            side_effect=OSError("permission denied"),
        ):
            response = self.client.post(
                "/imported/export-selected",
                data={"conversation_ids": [str(self.ids["a"])]},
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/imported", response.headers["Location"])

        followed = self.client.get("/imported")
        body = followed.get_data(as_text=True)
        self.assertIn("Failed to write", body)
        self.assertIn("permission denied", body)


def _seed_triple_collision(app) -> list[int]:
    """Seed three conversations designed to trigger nested filename collisions.

    Title sequence: 'Foo', 'Foo-3', 'Foo'. On a fresh DB these get ids 1, 2, 3.
    The second pre-occupies 'Foo-3.md', which is exactly the name the naive
    single-shot disambiguator would hand the third (Foo with id 3).
    """

    with app.app_context():
        conversations = []
        for idx, title in enumerate(["Foo", "Foo-3", "Foo"]):
            c = ImportedConversation(
                source="chatgpt",
                source_conversation_id=f"triple-{idx}",
                title=title,
                created_at_unix=1710000000.0 + idx,
                updated_at_unix=1710000000.0 + idx,
            )
            db.session.add(c)
            conversations.append(c)
        db.session.flush()

        for c in conversations:
            db.session.add(
                ImportedMessage(
                    conversation_id=c.id,
                    source_message_id=f"m-{c.id}",
                    role="user",
                    content=f"message for {c.title}",
                    sequence_index=0,
                    created_at_unix=1710000001.0 + c.id,
                )
            )
        db.session.commit()
        return [c.id for c in conversations]


class MultiSelectExportCollisionTest(unittest.TestCase):
    """Isolated test class with its own DB so auto-increment IDs start at 1,
    which is required to construct the 'Foo-3 preoccupies the disambiguation
    target of Foo at id=3' scenario reliably."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "multi-export-coll")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_dir = Config.SOULPRINT_EXPORT_DIR
        self.addCleanup(self._restore_config)

        Config.SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{(self.workdir / 'coll_test.db').as_posix()}"
        )
        Config.SOULPRINT_EXPORT_DIR = ""

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        self.ids = _seed_triple_collision(self.app)
        # IDs must be 1, 2, 3 for the scenario to hold
        self.assertEqual(self.ids, [1, 2, 3])

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_dir

    # 8 — triple collision: Foo / Foo-3 / Foo with ids 1,2,3 all get unique names
    def test_triple_collision_produces_unique_names_zip(self):
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(i) for i in self.ids]},
        )

        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 3)
            self.assertEqual(len(set(names)), 3, f"duplicate names: {names}")
            # The third 'Foo' cannot simply become 'Foo-3.md' — that's taken
            # by the second conversation. It should fall through to a suffixed
            # variant ('Foo-3-2.md' with the current helper).
            self.assertIn("Foo.md", names)
            self.assertIn("Foo-3.md", names)

    # 9 — same scenario in directory mode: three distinct files on disk
    def test_triple_collision_produces_unique_names_dir(self):
        release_app_db_handles(self.app, drop_all=True)
        export_dir = make_test_temp_dir(self, "triple-dest")
        Config.SOULPRINT_EXPORT_DIR = str(export_dir)
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.ids = _seed_triple_collision(self.app)
        self.assertEqual(self.ids, [1, 2, 3])

        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(i) for i in self.ids]},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        md_files = sorted(export_dir.glob("*.md"))
        self.assertEqual(len(md_files), 3)
        self.assertEqual(len({f.name for f in md_files}), 3)


def _seed_conversations_with_assets(app) -> dict[str, int]:
    """Seed two conversations each with a distinct attachment.

    Conv A: conversation-level attachment alpha_report.pdf
    Conv B: message-level attachment beta_screenshot.png on its first message
    """
    with app.app_context():
        a = ImportedConversation(
            source="chatgpt",
            source_conversation_id="attach-alpha",
            title="Conversation Alpha",
            created_at_unix=1710000000.0,
            updated_at_unix=1710000500.0,
        )
        b = ImportedConversation(
            source="claude",
            source_conversation_id="attach-beta",
            title="Conversation Beta",
            created_at_unix=1710001000.0,
            updated_at_unix=1710001500.0,
        )
        db.session.add_all([a, b])
        db.session.flush()

        msg_a = ImportedMessage(
            conversation_id=a.id,
            source_message_id="a-0",
            role="user",
            content="Alpha message content.",
            sequence_index=0,
            created_at_unix=1710000001.0,
        )
        msg_b = ImportedMessage(
            conversation_id=b.id,
            source_message_id="b-0",
            role="user",
            content="Beta message content.",
            sequence_index=0,
            created_at_unix=1710001001.0,
        )
        db.session.add_all([msg_a, msg_b])
        db.session.flush()

        sha_a = ("aaa111" + "0" * 64)[:64]
        asset_a = Asset(
            stable_id=f"asset:sha256:{sha_a}",
            sha256=sha_a,
            original_filename="alpha_report.pdf",
            stored_filename=f"{sha_a}-alpha_report.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=1024,
            storage_path=f"assets/sha256/aa/{sha_a}-alpha_report.pdf",
            uploaded_at_unix=1710000010.0,
            source="manual",
            parse_status="unparsed",
            parse_error=None,
        )
        sha_b = ("bbb222" + "0" * 64)[:64]
        asset_b = Asset(
            stable_id=f"asset:sha256:{sha_b}",
            sha256=sha_b,
            original_filename="beta_screenshot.png",
            stored_filename=f"{sha_b}-beta_screenshot.png",
            mime_type="image/png",
            extension="png",
            size_bytes=512,
            storage_path=f"assets/sha256/bb/{sha_b}-beta_screenshot.png",
            uploaded_at_unix=1710001010.0,
            source="manual",
            parse_status="unparsed",
            parse_error=None,
        )
        db.session.add_all([asset_a, asset_b])
        db.session.flush()

        db.session.add(ConversationAsset(
            conversation_id=a.id,
            asset_id=asset_a.id,
            role="context",
            note="",
            attached_at_unix=1710000020.0,
        ))
        db.session.add(MessageAsset(
            message_id=msg_b.id,
            asset_id=asset_b.id,
            placement="after_message_content",
            caption="",
            attached_at_unix=1710001020.0,
        ))
        db.session.commit()
        return {"a": a.id, "b": b.id}


class MultiSelectExportAttachmentsTest(unittest.TestCase):
    """Attachment markers in multi-select export stay scoped to each conversation."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "multi-export-attach")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_dir = Config.SOULPRINT_EXPORT_DIR
        self.addCleanup(self._restore_config)

        Config.SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{(self.workdir / 'attach_export.db').as_posix()}"
        )
        Config.SOULPRINT_EXPORT_DIR = ""

        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        self.ids = _seed_conversations_with_assets(self.app)

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_dir

    def test_each_conversation_includes_only_its_own_attachments(self):
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["b"])]},
        )
        self.assertEqual(response.status_code, 200)

        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            bodies = {name: zf.read(name).decode("utf-8") for name in zf.namelist()}

        alpha_body = next(v for k, v in bodies.items() if "Alpha" in k)
        beta_body = next(v for k, v in bodies.items() if "Beta" in k)

        self.assertIn("alpha_report.pdf", alpha_body)
        self.assertNotIn("beta_screenshot.png", alpha_body)

        self.assertIn("beta_screenshot.png", beta_body)
        self.assertNotIn("alpha_report.pdf", beta_body)

    def test_zip_contains_only_markdown_files_when_attachments_exist(self):
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["b"])]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")

        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 2)
            for name in names:
                self.assertTrue(
                    name.endswith(".md"),
                    f"Expected only .md entries in zip, found: {name!r}",
                )

    def test_no_shared_global_assets_folder_in_zip(self):
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["b"])]},
        )
        self.assertEqual(response.status_code, 200)

        with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
            for name in zf.namelist():
                self.assertFalse(
                    name.startswith("assets/"),
                    f"Unexpected shared assets folder in zip: {name!r}",
                )
                self.assertFalse(
                    name.endswith("/"),
                    f"Unexpected directory entry in zip: {name!r}",
                )


class MultiSelectExportDirectoryBundleTest(unittest.TestCase):
    """Multi-select directory export creates per-conversation .assets/ folders."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "multi-dir-bundle")
        self.export_dir = self.workdir / "vault"
        self.export_dir.mkdir()

        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        self._old_dir = Config.SOULPRINT_EXPORT_DIR
        self.addCleanup(self._restore_config)

        Config.SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{(self.workdir / 'multi_bundle.db').as_posix()}"
        )
        Config.SOULPRINT_EXPORT_DIR = str(self.export_dir)

        self.app = create_app()
        self.instance_root = Path(self.app.instance_path)
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

        self._physical_files: list[Path] = []
        self.addCleanup(self._remove_physical_files)

        # sha_a: sha[:2] == "aa"
        self._sha_a = ("aa" + "11" * 31)[:64]
        self._sha_b = ("bb" + "22" * 31)[:64]
        self._storage_a = f"assets/sha256/aa/{self._sha_a}-alpha_report.pdf"
        self._storage_b = f"assets/sha256/bb/{self._sha_b}-beta_screenshot.png"

        self.ids = _seed_dir_bundle_conversations(self.app, self._sha_a, self._sha_b,
                                                  self._storage_a, self._storage_b)

        for storage in (self._storage_a, self._storage_b):
            physical = self.instance_root / storage
            physical.parent.mkdir(parents=True, exist_ok=True)
            physical.write_bytes(b"bytes")
            self._physical_files.append(physical)

    def _restore_config(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri
        Config.SOULPRINT_EXPORT_DIR = self._old_dir

    def _remove_physical_files(self):
        for p in self._physical_files:
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass

    def test_each_conversation_gets_its_own_assets_folder(self):
        response = self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["b"])]},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)

        self.assertTrue((self.export_dir / "Conversation Alpha.assets").is_dir())
        self.assertTrue((self.export_dir / "Conversation Beta.assets").is_dir())

    def test_assets_not_leaked_across_conversations(self):
        self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["b"])]},
        )
        alpha_files = {p.name for p in (self.export_dir / "Conversation Alpha.assets").iterdir()}
        beta_files = {p.name for p in (self.export_dir / "Conversation Beta.assets").iterdir()}

        self.assertTrue(any("alpha_report.pdf" in n for n in alpha_files))
        self.assertFalse(any("beta_screenshot.png" in n for n in alpha_files))

        self.assertTrue(any("beta_screenshot.png" in n for n in beta_files))
        self.assertFalse(any("alpha_report.pdf" in n for n in beta_files))

    def test_no_assets_folder_for_conversation_without_attachments(self):
        with self.app.app_context():
            conv_clean = ImportedConversation(
                source="gemini",
                source_conversation_id="clean-conv",
                title="Clean Conversation",
                created_at_unix=1710002000.0,
                updated_at_unix=1710002500.0,
            )
            db.session.add(conv_clean)
            db.session.flush()
            db.session.add(ImportedMessage(
                conversation_id=conv_clean.id,
                source_message_id="c-0",
                role="user",
                content="no attachments here",
                sequence_index=0,
                created_at_unix=1710002001.0,
            ))
            db.session.commit()
            clean_id = conv_clean.id

        self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(clean_id)]},
        )
        self.assertFalse((self.export_dir / "Clean Conversation.assets").exists())

    def test_each_manifest_scoped_to_its_own_conversation(self):
        import json as _json
        self.client.post(
            "/imported/export-selected",
            data={"conversation_ids": [str(self.ids["a"]), str(self.ids["b"])]},
        )
        alpha_manifest = _json.loads(
            (self.export_dir / "Conversation Alpha.assets" / "manifest.json").read_text()
        )
        beta_manifest = _json.loads(
            (self.export_dir / "Conversation Beta.assets" / "manifest.json").read_text()
        )
        self.assertEqual(alpha_manifest["title"], "Conversation Alpha")
        self.assertEqual(beta_manifest["title"], "Conversation Beta")
        self.assertEqual(len(alpha_manifest["assets"]), 1)
        self.assertEqual(len(beta_manifest["assets"]), 1)
        self.assertNotEqual(alpha_manifest["conversation_id"], beta_manifest["conversation_id"])


def _seed_dir_bundle_conversations(app, sha_a, sha_b, storage_a, storage_b) -> dict[str, int]:
    """Seed two conversations: Alpha (conv-level asset), Beta (message-level asset)."""
    with app.app_context():
        a = ImportedConversation(
            source="chatgpt",
            source_conversation_id="dir-alpha",
            title="Conversation Alpha",
            created_at_unix=1710000000.0,
            updated_at_unix=1710000500.0,
        )
        b = ImportedConversation(
            source="claude",
            source_conversation_id="dir-beta",
            title="Conversation Beta",
            created_at_unix=1710001000.0,
            updated_at_unix=1710001500.0,
        )
        db.session.add_all([a, b])
        db.session.flush()

        msg_a = ImportedMessage(
            conversation_id=a.id,
            source_message_id="a-0",
            role="user",
            content="Alpha message.",
            sequence_index=0,
            created_at_unix=1710000001.0,
        )
        msg_b = ImportedMessage(
            conversation_id=b.id,
            source_message_id="b-0",
            role="user",
            content="Beta message.",
            sequence_index=0,
            created_at_unix=1710001001.0,
        )
        db.session.add_all([msg_a, msg_b])
        db.session.flush()

        asset_a = Asset(
            stable_id=f"asset:sha256:{sha_a}",
            sha256=sha_a,
            original_filename="alpha_report.pdf",
            stored_filename=f"{sha_a}-alpha_report.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size_bytes=8,
            storage_path=storage_a,
            uploaded_at_unix=1710000010.0,
            source="manual",
            parse_status="unparsed",
            parse_error=None,
        )
        asset_b = Asset(
            stable_id=f"asset:sha256:{sha_b}",
            sha256=sha_b,
            original_filename="beta_screenshot.png",
            stored_filename=f"{sha_b}-beta_screenshot.png",
            mime_type="image/png",
            extension="png",
            size_bytes=5,
            storage_path=storage_b,
            uploaded_at_unix=1710001010.0,
            source="manual",
            parse_status="unparsed",
            parse_error=None,
        )
        db.session.add_all([asset_a, asset_b])
        db.session.flush()

        db.session.add(ConversationAsset(
            conversation_id=a.id,
            asset_id=asset_a.id,
            role="context",
            note="",
            attached_at_unix=1710000020.0,
        ))
        db.session.add(MessageAsset(
            message_id=msg_b.id,
            asset_id=asset_b.id,
            placement="after_message_content",
            caption="",
            attached_at_unix=1710001020.0,
        ))
        db.session.commit()
        return {"a": a.id, "b": b.id}


if __name__ == "__main__":
    unittest.main()
