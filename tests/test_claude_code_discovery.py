from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class SourceMetadataPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "meta-persist")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        from src.app import create_app
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_source_metadata_round_trips(self):
        from src.importers.contracts import NormalizedConversation, NormalizedMessage
        from src.importers.persistence import persist_normalized_conversations
        from src.app.models import ImportedConversation

        msg = NormalizedMessage(
            source_message_id="m1",
            role="user",
            content="hello",
            sequence_index=0,
            created_at=1700000000.0,
        )
        conv = NormalizedConversation(
            source_provider="claude",
            source_conversation_id="test-meta-001",
            title="Meta test",
            created_at=1700000000.0,
            updated_at=1700000001.0,
            messages=[msg],
            source_metadata={"key": "value", "num": 42},
        )

        with self.app.app_context():
            persist_normalized_conversations([conv])
            row = ImportedConversation.query.filter_by(
                source_conversation_id="test-meta-001"
            ).first()
            self.assertIsNotNone(row)
            self.assertIsNotNone(row.source_metadata_json)
            parsed = json.loads(row.source_metadata_json)
            self.assertEqual(parsed["key"], "value")
            self.assertEqual(parsed["num"], 42)


MINIMAL_JSONL = (
    b'{"type":"user","sessionId":"aaaaaaaa-0000-0000-0000-000000000001","uuid":"msg-u1",'
    b'"timestamp":"2026-01-01T10:00:00.000Z","message":{"role":"user","content":"hello"}}\n'
    b'{"type":"assistant","sessionId":"aaaaaaaa-0000-0000-0000-000000000001","uuid":"msg-a1",'
    b'"timestamp":"2026-01-01T10:00:05.000Z","message":{"role":"assistant","content":"world"}}\n'
)


def _write_session(project_dir: Path, session_id: str, content: bytes = MINIMAL_JSONL) -> Path:
    f = project_dir / f"{session_id}.jsonl"
    f.write_bytes(content)
    return f


class DiscoverSessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "discover")

    def test_returns_empty_when_projects_dir_missing(self):
        from src.importers.claude_code_discovery import discover_sessions
        result = discover_sessions(self.tmpdir / "nonexistent")
        self.assertEqual(result, [])

    def test_reads_sessions_index_when_present(self):
        from src.importers.claude_code_discovery import discover_sessions
        proj = self.tmpdir / "C--Users-foo-myproject"
        proj.mkdir()
        sid1 = "aaaaaaaa-0000-0000-0000-000000000001"
        sid2 = "bbbbbbbb-0000-0000-0000-000000000002"
        _write_session(proj, sid1)
        _write_session(proj, sid2)
        index = {
            "entries": [
                {
                    "sessionId": sid1,
                    "projectPath": "/Users/foo/myproject",
                    "summary": "First session",
                    "created": "2026-01-01T10:00:00Z",
                    "modified": "2026-01-01T11:00:00Z",
                },
                {
                    "sessionId": sid2,
                    "projectPath": "/Users/foo/myproject",
                    "summary": "Second session",
                    "created": "2026-01-02T10:00:00Z",
                    "modified": "2026-01-02T11:00:00Z",
                },
            ]
        }
        (proj / "sessions-index.json").write_text(json.dumps(index), encoding="utf-8")
        results = discover_sessions(self.tmpdir)
        self.assertEqual(len(results), 2)
        s1 = next(r for r in results if r.session_id == sid1)
        self.assertEqual(s1.summary, "First session")
        self.assertEqual(s1.project_path, "/Users/foo/myproject")
        self.assertEqual(s1.created, "2026-01-01T10:00:00Z")
        self.assertEqual(s1.modified, "2026-01-01T11:00:00Z")

    def test_falls_back_when_sessions_index_missing(self):
        from src.importers.claude_code_discovery import discover_sessions
        proj = self.tmpdir / "C--Users-foo-other"
        proj.mkdir()
        sid = "cccccccc-0000-0000-0000-000000000003"
        _write_session(proj, sid)
        results = discover_sessions(self.tmpdir)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].session_id, sid)
        self.assertIsNone(results[0].summary)
        self.assertIsNone(results[0].project_path)

    def test_message_count_estimate_bounded(self):
        from src.importers.claude_code_discovery import discover_sessions
        proj = self.tmpdir / "C--Users-foo-large"
        proj.mkdir()
        sid = "dddddddd-0000-0000-0000-000000000004"
        lines = []
        for i in range(100):
            lines.append(json.dumps({
                "type": "user",
                "sessionId": sid,
                "uuid": f"u{i}",
                "timestamp": "2026-01-01T10:00:00Z",
                "message": {"role": "user", "content": "x"},
            }))
            lines.append(json.dumps({
                "type": "assistant",
                "sessionId": sid,
                "uuid": f"a{i}",
                "timestamp": "2026-01-01T10:00:01Z",
                "message": {"role": "assistant", "content": "y"},
            }))
        (proj / f"{sid}.jsonl").write_bytes("\n".join(lines).encode())
        results = discover_sessions(self.tmpdir)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].message_count_estimate, 200)

    def test_sort_order(self):
        from src.importers.claude_code_discovery import discover_sessions
        for proj_name in ["C--proj-b", "C--proj-a"]:
            proj = self.tmpdir / proj_name
            proj.mkdir()
        sid_b1 = "11111111-0000-0000-0000-000000000001"
        sid_b2 = "22222222-0000-0000-0000-000000000002"
        sid_a1 = "33333333-0000-0000-0000-000000000003"
        _write_session(self.tmpdir / "C--proj-b", sid_b1)
        _write_session(self.tmpdir / "C--proj-b", sid_b2)
        _write_session(self.tmpdir / "C--proj-a", sid_a1)
        idx_b = {
            "entries": [
                {"sessionId": sid_b1, "created": "2026-01-02T00:00:00Z"},
                {"sessionId": sid_b2, "created": "2026-01-01T00:00:00Z"},
            ]
        }
        (self.tmpdir / "C--proj-b" / "sessions-index.json").write_text(json.dumps(idx_b))
        results = discover_sessions(self.tmpdir)
        names = [r.project_dir_name for r in results]
        self.assertEqual(names[0], "C--proj-a")
        self.assertEqual(names[1], "C--proj-b")
        self.assertEqual(names[2], "C--proj-b")
        proj_b = [r for r in results if r.project_dir_name == "C--proj-b"]
        self.assertEqual(proj_b[0].session_id, sid_b2)
        self.assertEqual(proj_b[1].session_id, sid_b1)


class NormalizeProjectsPathTest(unittest.TestCase):
    def test_rejects_traversal_segments(self):
        from src.importers.claude_code_discovery import normalize_projects_path
        home = Path.home()
        with self.assertRaises(ValueError):
            normalize_projects_path(str(home / "valid" / ".." / ".." / "etc"))


class ImportSelectedSessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "import-sel")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        from src.app import create_app
        self.app = create_app()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _make_discovered(
        self,
        session_id: str,
        project_dir_name: str = "C--proj-test",
        content: bytes = MINIMAL_JSONL,
    ):
        proj = self.tmpdir / project_dir_name
        proj.mkdir(exist_ok=True)
        path = proj / f"{session_id}.jsonl"
        path.write_bytes(content)
        from src.importers.claude_code_discovery import DiscoveredSession
        return DiscoveredSession(
            path=path,
            session_id=session_id,
            project_dir_name=project_dir_name,
            project_path="/Users/test/proj",
            summary="test",
            created="2026-01-01T10:00:00Z",
            modified="2026-01-01T11:00:00Z",
            size_bytes=len(content),
            message_count_estimate=2,
        )

    def test_imports_and_populates_metadata(self):
        from src.importers.claude_code_discovery import import_selected_sessions
        from src.app.models import ImportedConversation

        sid = "aaaaaaaa-0000-0000-0000-000000000001"
        discovered = self._make_discovered(sid)
        result = import_selected_sessions([discovered], self.db_path)
        self.assertIn(sid, result.imported)
        self.assertEqual(result.skipped_duplicate, [])
        self.assertEqual(result.failed, [])
        with self.app.app_context():
            row = ImportedConversation.query.filter_by(source="claude_code").first()
            self.assertIsNotNone(row)
            self.assertIsNotNone(row.source_metadata_json)
            meta = json.loads(row.source_metadata_json)
            self.assertEqual(meta["project_path"], "/Users/test/proj")
            self.assertEqual(meta["project_dir_name"], "C--proj-test")
            self.assertEqual(meta["session_id"], sid)

    def test_skip_duplicate_on_rerun(self):
        from src.importers.claude_code_discovery import import_selected_sessions

        sid = "aaaaaaaa-0000-0000-0000-000000000001"
        discovered = self._make_discovered(sid)
        result1 = import_selected_sessions([discovered], self.db_path)
        self.assertIn(sid, result1.imported)
        result2 = import_selected_sessions([discovered], self.db_path)
        self.assertEqual(result2.imported, [])
        self.assertIn(sid, result2.skipped_duplicate)

    def test_failed_session_captured_not_raised(self):
        from src.importers.claude_code_discovery import import_selected_sessions, DiscoveredSession

        bad_path = self.tmpdir / "C--proj-bad" / "bad-session.jsonl"
        bad_path.parent.mkdir(exist_ok=True)
        # Do NOT write the file -- reading it will raise OSError
        discovered = DiscoveredSession(
            path=bad_path,
            session_id="bad-session",
            project_dir_name="C--proj-bad",
            project_path=None,
            summary=None,
            created=None,
            modified=None,
            size_bytes=0,
            message_count_estimate=0,
        )
        result = import_selected_sessions([discovered], self.db_path)
        self.assertEqual(result.imported, [])
        self.assertEqual(len(result.failed), 1)
        self.assertEqual(result.failed[0][0], "bad-session")
        self.assertIsInstance(result.failed[0][1], str)
        self.assertTrue(len(result.failed[0][1]) > 0)
