from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tests.temp_helpers import make_test_temp_dir


_CREATE_TABLES = """
CREATE TABLE imported_conversation (
    id INTEGER PRIMARY KEY,
    source TEXT,
    created_at_unix REAL
);
CREATE TABLE imported_message (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER
);
CREATE TABLE memory_entry (
    id INTEGER PRIMARY KEY
);
"""

_CREATE_TABLES_WITH_FTS = _CREATE_TABLES + """
CREATE VIRTUAL TABLE fts_messages USING fts5(content);
CREATE VIRTUAL TABLE fts_notes USING fts5(content);
"""


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_CREATE_TABLES)
        conn.commit()
    finally:
        conn.close()


def _seed_db(path: Path, conversations: list[dict], messages: int = 0, notes: int = 0) -> None:
    _make_db(path)
    conn = sqlite3.connect(str(path))
    try:
        for c in conversations:
            conn.execute(
                "INSERT INTO imported_conversation (source, created_at_unix) VALUES (?, ?)",
                (c["source"], c.get("ts")),
            )
        for i in range(messages):
            conn.execute("INSERT INTO imported_message (conversation_id) VALUES (?)", (i + 1,))
        for _ in range(notes):
            conn.execute("INSERT INTO memory_entry DEFAULT VALUES")
        conn.commit()
    finally:
        conn.close()


class CLIInfoTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = make_test_temp_dir(self, "cli-info")
        self.db_path = str(self.tmpdir / "test.db")

    def _run_info(self, extra_args: list[str] | None = None) -> str:
        from src.cli import main
        args = ["info", "--db", self.db_path] + (extra_args or [])
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            main(args)
        return buf.getvalue()

    def test_info_fresh_db_prints_zeros(self) -> None:
        _make_db(Path(self.db_path))
        out = self._run_info()
        self.assertIn("Conversations:", out)
        self.assertIn("0", out)
        self.assertIn("Date range: none", out)

    def test_info_with_data(self) -> None:
        _seed_db(
            Path(self.db_path),
            conversations=[
                {"source": "chatgpt", "ts": 1_700_000_000.0},
                {"source": "claude", "ts": 1_710_000_000.0},
            ],
            messages=3,
            notes=1,
        )
        out = self._run_info()
        self.assertIn("2", out)   # conversation count
        self.assertIn("3", out)   # message count
        self.assertIn("1", out)   # note count
        self.assertIn("chatgpt", out)
        self.assertIn("claude", out)

    def test_info_json_output(self) -> None:
        _seed_db(
            Path(self.db_path),
            conversations=[{"source": "chatgpt", "ts": 1_700_000_000.0}],
            messages=2,
            notes=0,
        )
        out = self._run_info(["--json"])
        obj = json.loads(out)
        self.assertIn("conversations", obj)
        self.assertIn("messages", obj)
        self.assertIn("notes", obj)
        self.assertIn("providers", obj)
        self.assertIn("date_range", obj)
        self.assertIn("db_size_bytes", obj)
        self.assertIn("intelligence", obj)
        self.assertEqual(obj["conversations"], 1)
        self.assertEqual(obj["messages"], 2)
        self.assertIn("min", obj["date_range"])
        self.assertIn("max", obj["date_range"])

    def test_info_missing_db_exits_nonzero(self) -> None:
        from src.cli import main
        missing = str(self.tmpdir / "nonexistent.db")
        err_buf = io.StringIO()
        with patch("sys.stderr", err_buf):
            with self.assertRaises(SystemExit) as cm:
                main(["info", "--db", missing])
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Database not found", err_buf.getvalue())

    def test_info_omits_zero_providers(self) -> None:
        _seed_db(
            Path(self.db_path),
            conversations=[{"source": "chatgpt", "ts": 1_700_000_000.0}],
        )
        out = self._run_info()
        self.assertIn("chatgpt", out)
        self.assertNotIn("claude", out)
        self.assertNotIn("gemini", out)
        self.assertNotIn("grok", out)
        self.assertNotIn("claude_code", out)


class CLIMcpConfigTest(unittest.TestCase):
    def test_mcp_config_prints_json(self) -> None:
        from src.cli import main
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            main(["mcp-config"])
        obj = json.loads(buf.getvalue())
        db_val = obj["mcpServers"]["soulprint"]["env"]["SOULPRINT_DB"]
        self.assertTrue(Path(db_val).is_absolute(), f"SOULPRINT_DB is not absolute: {db_val}")
        self.assertIn("soulprint.db", db_val)
        command = obj["mcpServers"]["soulprint"]["command"]
        self.assertTrue(os.path.isabs(command), f"command is not absolute: {command!r}")
        self.assertNotEqual(command, "python")

    def test_mcp_config_honors_soulprint_db_env(self) -> None:
        from src.cli import main
        custom_path = str(Path.cwd() / "custom_test_soulprint.db")
        expected = str(Path(custom_path).resolve())
        buf = io.StringIO()
        with patch.dict(os.environ, {"SOULPRINT_DB": custom_path}):
            with patch("sys.stdout", buf):
                main(["mcp-config"])
        obj = json.loads(buf.getvalue())
        db_val = obj["mcpServers"]["soulprint"]["env"]["SOULPRINT_DB"]
        self.assertEqual(db_val, expected)


def _make_db_with_fts(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_CREATE_TABLES_WITH_FTS)
        conn.commit()
    finally:
        conn.close()


class CLIVerifyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = make_test_temp_dir(self, "cli-verify")
        self.db_path = str(self.tmpdir / "test.db")

    def _run_verify(self, extra_args: list[str] | None = None) -> tuple[str, int | None]:
        from src.cli import main
        args = ["verify", "--db", self.db_path] + (extra_args or [])
        buf = io.StringIO()
        exit_code = None
        try:
            with patch("sys.stdout", buf):
                main(args)
        except SystemExit as exc:
            exit_code = exc.code
        return buf.getvalue(), exit_code

    def test_verify_happy_path_exit_zero(self) -> None:
        _make_db_with_fts(Path(self.db_path))
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO imported_conversation (source, created_at_unix) VALUES (?, ?)",
                ("chatgpt", 1_700_000_000.0),
            )
            conn.commit()
        finally:
            conn.close()

        out, exit_code = self._run_verify()

        self.assertIn("Status: healthy", out)
        self.assertIsNone(exit_code)

    def test_verify_missing_db_exits_two(self) -> None:
        from src.cli import main
        missing = str(self.tmpdir / "nonexistent.db")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            with self.assertRaises(SystemExit) as cm:
                main(["verify", "--db", missing])
        self.assertEqual(cm.exception.code, 2)

    def test_verify_unhealthy_archive_exits_one(self) -> None:
        # core tables only — FTS tables missing → unhealthy
        _make_db(Path(self.db_path))

        _out, exit_code = self._run_verify()

        self.assertEqual(exit_code, 1)

    def test_verify_json_flag_outputs_parseable_json(self) -> None:
        _make_db_with_fts(Path(self.db_path))
        out, _exit_code = self._run_verify(["--json"])
        obj = json.loads(out)
        for key in ("ok", "db_path", "checks", "counts"):
            self.assertIn(key, obj)


class CLIHelpTest(unittest.TestCase):
    def test_help_lists_subcommands(self) -> None:
        from src.cli import main
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            with self.assertRaises(SystemExit):
                main(["--help"])
        out = buf.getvalue()
        self.assertIn("info", out)
        self.assertIn("mcp-config", out)
        self.assertIn("verify", out)
        self.assertNotIn("serve", out)


class CLIBareInvocationDispatchTest(unittest.TestCase):
    """Cover bare ``soulprint`` dispatch after Campaign 02 B5c."""

    def _chdir(self, target: Path) -> None:
        original_cwd = os.getcwd()
        self.addCleanup(os.chdir, original_cwd)
        os.chdir(target)

    def test_bare_soulprint_invokes_supervisor_and_not_legacy_serve(self) -> None:
        from src.cli import main
        supervisor_mock = MagicMock()
        supervisor_mock.return_value.run.return_value = 0
        with patch("src.main.main") as run_server_mock, patch(
            "src.runtime.supervisor.Supervisor", supervisor_mock
        ):
            with self.assertRaises(SystemExit) as ctx:
                main([])
        self.assertEqual(int(ctx.exception.code or 0), 0)
        supervisor_mock.return_value.run.assert_called_once()
        run_server_mock.assert_not_called()

    def test_bare_soulprint_uses_cwd_procfile_dev_when_present(self) -> None:
        from src.cli import main
        tmpdir = make_test_temp_dir(self, "bare-cwd-procfile")
        (tmpdir / "Procfile.dev").write_text(
            "flask: python -m src.main\n", encoding="utf-8"
        )
        self._chdir(tmpdir)

        supervisor_mock = MagicMock()
        supervisor_mock.return_value.run.return_value = 0
        with patch("src.runtime.supervisor.Supervisor", supervisor_mock):
            with self.assertRaises(SystemExit):
                main([])

        called_path = supervisor_mock.return_value.run.call_args.args[0]
        self.assertEqual(called_path, tmpdir / "Procfile.dev")

    def test_bare_soulprint_uses_packaged_procfile_when_cwd_has_none(self) -> None:
        from src.cli import main
        tmpdir = make_test_temp_dir(self, "bare-no-cwd-procfile")
        self._chdir(tmpdir)

        supervisor_mock = MagicMock()
        supervisor_mock.return_value.run.return_value = 0
        with patch("src.runtime.supervisor.Supervisor", supervisor_mock):
            with self.assertRaises(SystemExit):
                main([])

        called_path = supervisor_mock.return_value.run.call_args.args[0]
        self.assertNotEqual(called_path, tmpdir / "Procfile.dev")
        self.assertEqual(called_path.name, "Procfile.dev")
        self.assertEqual(called_path.parent.name, "runtime")
        self.assertTrue(called_path.exists())

    def test_bare_soulprint_propagates_supervisor_exit_code(self) -> None:
        from src.cli import main
        supervisor_mock = MagicMock()
        supervisor_mock.return_value.run.return_value = 3
        with patch("src.runtime.supervisor.Supervisor", supervisor_mock):
            with self.assertRaises(SystemExit) as ctx:
                main([])
        self.assertEqual(int(ctx.exception.code or 0), 3)
