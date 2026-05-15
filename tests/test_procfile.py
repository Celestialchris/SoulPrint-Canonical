"""Tests for ``src/runtime/procfile.py`` covering B2 of Campaign 02."""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from src.runtime.procfile import (
    MalformedProcfileError,
    default_procfile_path,
    parse,
    parse_file,
)
from tests.temp_helpers import make_test_temp_dir


class ProcfileParseTest(unittest.TestCase):
    def test_single_line_happy_path(self):
        result = parse("flask: python -m src.main")

        self.assertEqual(result, [("flask", ["python", "-m", "src.main"])])

    def test_blank_lines_and_comments_are_ignored(self):
        text = "\n# leading comment\n\nflask: python -m src.main\n# trailing comment\n\n"

        result = parse(text)

        self.assertEqual(result, [("flask", ["python", "-m", "src.main"])])

    def test_multiple_services_preserve_declared_order(self):
        text = "flask: python -m src.main\nworker: python -m src.worker --loop\n"

        result = parse(text)

        self.assertEqual(
            result,
            [
                ("flask", ["python", "-m", "src.main"]),
                ("worker", ["python", "-m", "src.worker", "--loop"]),
            ],
        )

    def test_missing_colon_raises(self):
        with self.assertRaises(MalformedProcfileError) as ctx:
            parse("flask python -m src.main")

        self.assertEqual(ctx.exception.line_number, 1)
        self.assertIn("missing", ctx.exception.reason)

    def test_empty_command_raises(self):
        with self.assertRaises(MalformedProcfileError) as ctx:
            parse("flask:   ")

        self.assertEqual(ctx.exception.line_number, 1)
        self.assertIn("empty command", ctx.exception.reason)

    def test_invalid_service_name_raises(self):
        with self.assertRaises(MalformedProcfileError) as ctx:
            parse("1flask: python -m src.main")

        self.assertEqual(ctx.exception.line_number, 1)
        self.assertIn("invalid service name", ctx.exception.reason)

    def test_line_number_reflects_offending_line(self):
        text = "flask: python -m src.main\n\n# comment\nbroken without colon\n"

        with self.assertRaises(MalformedProcfileError) as ctx:
            parse(text)

        self.assertEqual(ctx.exception.line_number, 4)

    def test_duplicate_service_names_raise(self):
        text = "flask: python -m src.main\nflask: python -m src.other\n"

        with self.assertRaises(MalformedProcfileError) as ctx:
            parse(text)

        self.assertEqual(ctx.exception.line_number, 2)
        self.assertIn("duplicate service name", ctx.exception.reason)

    def test_double_quoted_token_preserves_internal_whitespace(self):
        result = parse('flask: "/path with space/python" -m src.main')

        self.assertEqual(
            result,
            [("flask", ["/path with space/python", "-m", "src.main"])],
        )

    def test_single_quoted_token_preserves_whitespace_and_backslashes(self):
        result = parse("flask: 'C:\\Program Files\\Python\\python.exe' -m src.main")

        self.assertEqual(
            result,
            [("flask", ["C:\\Program Files\\Python\\python.exe", "-m", "src.main"])],
        )

    def test_unquoted_backslashes_are_literal(self):
        # Windows interpreter paths without surrounding quotes must survive
        # tokenization with backslashes intact; the parser disables shell
        # escape semantics for exactly this reason.
        result = parse("flask: C:\\Python312\\python.exe -m src.main")

        self.assertEqual(
            result,
            [("flask", ["C:\\Python312\\python.exe", "-m", "src.main"])],
        )

    def test_unbalanced_quote_raises_malformed_procfile_error(self):
        with self.assertRaises(MalformedProcfileError) as ctx:
            parse("flask: 'unterminated")

        self.assertEqual(ctx.exception.line_number, 1)
        self.assertIn("tokenization", ctx.exception.reason)


class ProcfileParseFileTest(unittest.TestCase):
    def test_parse_file_reads_disk(self):
        tmpdir = make_test_temp_dir(self, "procfile-parse-file")
        path = tmpdir / "Procfile.dev"
        path.write_text("flask: python -m src.main\n", encoding="utf-8")

        result = parse_file(path)

        self.assertEqual(result, [("flask", ["python", "-m", "src.main"])])


class DefaultProcfileResolverTest(unittest.TestCase):
    """Cover ``default_procfile_path`` resolver behavior (Campaign 02 B5c)."""

    def _chdir(self, target: Path) -> None:
        original_cwd = os.getcwd()
        self.addCleanup(os.chdir, original_cwd)
        os.chdir(target)

    def test_returns_cwd_procfile_when_present(self):
        tmpdir = make_test_temp_dir(self, "procfile-cwd-present")
        cwd_procfile = tmpdir / "Procfile.dev"
        cwd_procfile.write_text("flask: python -m src.main\n", encoding="utf-8")
        self._chdir(tmpdir)

        result = default_procfile_path()

        self.assertEqual(result, tmpdir / "Procfile.dev")

    def test_returns_materialized_procfile_when_cwd_has_none(self):
        tmpdir = make_test_temp_dir(self, "procfile-cwd-absent")
        self._chdir(tmpdir)

        result = default_procfile_path()

        self.assertNotEqual(result, tmpdir / "Procfile.dev")
        self.assertTrue(result.exists())
        self.assertNotEqual(result.parent, tmpdir)

    def test_returns_pathlib_path(self):
        tmpdir = make_test_temp_dir(self, "procfile-path-type")
        self._chdir(tmpdir)

        result = default_procfile_path()

        self.assertIsInstance(result, Path)

    def test_packaged_procfile_parses_with_sys_executable(self):
        tmpdir = make_test_temp_dir(self, "procfile-packaged-content")
        self._chdir(tmpdir)

        result = default_procfile_path()
        text = result.read_text(encoding="utf-8")

        self.assertTrue(
            text.startswith("flask:"),
            f"packaged Procfile must start with 'flask:', got {text!r}",
        )
        self.assertEqual(
            parse(text),
            [("flask", [sys.executable, "-m", "src.main"])],
        )

    def test_packaged_procfile_pins_python_to_sys_executable(self):
        tmpdir = make_test_temp_dir(self, "procfile-python-pinned")
        self._chdir(tmpdir)

        result = default_procfile_path()
        text = result.read_text(encoding="utf-8")

        # Materialized text must contain sys.executable and must not contain
        # a bare ``python`` token (matching only the standalone form, not
        # paths like ``/usr/bin/python`` or names like ``python3``).
        self.assertIn(sys.executable, text)
        self.assertIsNone(
            re.search(r"(?m)(^|[\s:])python(?=\s|$)", text),
            f"materialized Procfile must not contain a bare 'python' token: {text!r}",
        )

    def test_packaged_procfile_matches_repo_root_after_substitution(self):
        repo_root_procfile = Path(__file__).resolve().parent.parent / "Procfile.dev"
        if not repo_root_procfile.exists():
            self.skipTest("repo-root Procfile.dev not present in this checkout")

        tmpdir = make_test_temp_dir(self, "procfile-packaged-vs-root")
        self._chdir(tmpdir)

        repo_services = parse(repo_root_procfile.read_text(encoding="utf-8"))
        materialized_services = parse_file(default_procfile_path())

        self.assertEqual(len(repo_services), len(materialized_services))
        for (rname, rcmd), (mname, mcmd) in zip(repo_services, materialized_services):
            self.assertEqual(rname, mname)
            self.assertEqual(len(rcmd), len(mcmd))
            # Only the leading interpreter token may differ; trailing args
            # must match the repo-root command verbatim.
            self.assertEqual(rcmd[1:], mcmd[1:])
            if rcmd and rcmd[0] == "python":
                self.assertEqual(mcmd[0], sys.executable)
            else:
                self.assertEqual(rcmd[0], mcmd[0])

    def test_packaged_procfile_round_trips_through_parse_file(self):
        tmpdir = make_test_temp_dir(self, "procfile-packaged-roundtrip")
        self._chdir(tmpdir)

        result = parse_file(default_procfile_path())

        self.assertEqual(
            result,
            [("flask", [sys.executable, "-m", "src.main"])],
        )

    def test_packaged_procfile_handles_sys_executable_with_whitespace(self):
        """Codex P2 follow-up: a venv inside ``Program Files`` must work."""

        tmpdir = make_test_temp_dir(self, "procfile-exec-with-space")
        self._chdir(tmpdir)

        fake_exec = "/path with space/python"
        with patch("src.runtime.procfile.sys.executable", fake_exec):
            result = default_procfile_path()
            tokens = parse_file(result)

        self.assertEqual(tokens, [("flask", [fake_exec, "-m", "src.main"])])

    def test_packaged_procfile_handles_windows_program_files_path(self):
        tmpdir = make_test_temp_dir(self, "procfile-exec-program-files")
        self._chdir(tmpdir)

        fake_exec = "C:\\Program Files\\Python312\\python.exe"
        with patch("src.runtime.procfile.sys.executable", fake_exec):
            result = default_procfile_path()
            tokens = parse_file(result)

        self.assertEqual(tokens, [("flask", [fake_exec, "-m", "src.main"])])


if __name__ == "__main__":
    unittest.main()
