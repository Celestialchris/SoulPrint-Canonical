from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import Config
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


def _make_session_jsonl(session_id: str) -> bytes:
    u = json.dumps({
        "type": "user",
        "sessionId": session_id,
        "uuid": f"u-{session_id[:8]}",
        "timestamp": "2026-01-01T10:00:00.000Z",
        "message": {"role": "user", "content": "hi"},
    })
    a = json.dumps({
        "type": "assistant",
        "sessionId": session_id,
        "uuid": f"a-{session_id[:8]}",
        "timestamp": "2026-01-01T10:00:05.000Z",
        "message": {"role": "assistant", "content": "hello"},
    })
    return (u + "\n" + a + "\n").encode()


def _build_fake_projects(base: Path, projects: dict[str, list[str]]) -> dict:
    projects_dir = base / "projects"
    projects_dir.mkdir()
    for proj_name, session_ids in projects.items():
        proj = projects_dir / proj_name
        proj.mkdir()
        for sid in session_ids:
            (proj / f"{sid}.jsonl").write_bytes(_make_session_jsonl(sid))
    return {"projects_dir": projects_dir}


class ScanClaudeCodeGetTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "scan-get")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        from src.app import create_app
        self.app = create_app()
        self.app.config["SECRET_KEY"] = "test-secret"
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_empty_state_when_no_projects_dir(self):
        nonexistent = self.tmpdir / "no-projects"
        with patch(
            "src.importers.claude_code_discovery.default_claude_projects_dir",
            return_value=nonexistent,
        ):
            response = self.client.get("/imported/scan-claude-code")
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("No Claude Code sessions found", body)

    def test_renders_project_tree(self):
        info = _build_fake_projects(self.tmpdir, {
            "C--proj-alpha": [
                "11111111-0000-0000-0000-000000000001",
                "22222222-0000-0000-0000-000000000002",
                "33333333-0000-0000-0000-000000000003",
            ],
            "C--proj-beta": [
                "44444444-0000-0000-0000-000000000004",
                "55555555-0000-0000-0000-000000000005",
                "66666666-0000-0000-0000-000000000006",
            ],
        })
        projects_dir = info["projects_dir"]
        with patch(
            "src.importers.claude_code_discovery.default_claude_projects_dir",
            return_value=projects_dir,
        ):
            response = self.client.get("/imported/scan-claude-code")
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("C--proj-alpha", body)
        self.assertIn("C--proj-beta", body)
        self.assertIn("11111111", body)
        self.assertIn("44444444", body)

    def test_rejects_path_outside_home(self):
        response = self.client.get(
            "/imported/scan-claude-code?path=/etc/passwd",
            follow_redirects=False,
        )
        self.assertIn(response.status_code, [302, 200])


class ScanClaudeCodePostTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "scan-post")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        from src.app import create_app
        self.app = create_app()
        self.app.config["SECRET_KEY"] = "test-secret"
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_imports_selected_sessions(self):
        from src.app.models import ImportedConversation
        sid1 = "aaaaaaaa-0000-0000-0000-000000000001"
        sid2 = "bbbbbbbb-0000-0000-0000-000000000002"
        info = _build_fake_projects(self.tmpdir, {
            "C--proj-test": [sid1, sid2],
        })
        projects_dir = info["projects_dir"]
        with patch(
            "src.importers.claude_code_discovery.default_claude_projects_dir",
            return_value=projects_dir,
        ):
            response = self.client.post(
                "/imported/scan-claude-code",
                data={"session_ids": [sid1, sid2]},
                follow_redirects=True,
            )
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn(sid1, body)
        self.assertIn(sid2, body)
        with self.app.app_context():
            count = ImportedConversation.query.filter_by(source="claude_code").count()
            self.assertEqual(count, 2)

    def test_empty_selection_redirects_with_error(self):
        response = self.client.post(
            "/imported/scan-claude-code",
            data={},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("No sessions selected", body)


class ScanClaudeCodeResultsGetTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "scan-results")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        from src.app import create_app
        self.app = create_app()
        self.app.config["SECRET_KEY"] = "test-secret"
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_redirects_when_no_session_data(self):
        response = self.client.get(
            "/imported/scan-claude-code/results",
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/imported/scan-claude-code", response.headers["Location"])
