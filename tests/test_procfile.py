"""Tests for ``src/runtime/procfile.py`` covering B2 of Campaign 02."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

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

    def test_returns_packaged_procfile_when_cwd_has_none(self):
        tmpdir = make_test_temp_dir(self, "procfile-cwd-absent")
        self._chdir(tmpdir)

        result = default_procfile_path()

        self.assertNotEqual(result, tmpdir / "Procfile.dev")
        self.assertTrue(result.exists())
        self.assertEqual(result.name, "Procfile.dev")
        # Resolver should pick the package-data copy alongside src/runtime/.
        self.assertEqual(result.parent.name, "runtime")

    def test_returns_pathlib_path(self):
        tmpdir = make_test_temp_dir(self, "procfile-path-type")
        self._chdir(tmpdir)

        result = default_procfile_path()

        self.assertIsInstance(result, Path)

    def test_packaged_procfile_parses_as_flask_line(self):
        tmpdir = make_test_temp_dir(self, "procfile-packaged-content")
        self._chdir(tmpdir)

        result = default_procfile_path()
        text = result.read_text(encoding="utf-8")

        self.assertTrue(
            text.startswith("flask:"),
            f"packaged Procfile must start with 'flask:', got {text!r}",
        )
        self.assertEqual(parse(text), [("flask", ["python", "-m", "src.main"])])

    def test_packaged_procfile_matches_repo_root_when_present(self):
        repo_root_procfile = Path(__file__).resolve().parent.parent / "Procfile.dev"
        if not repo_root_procfile.exists():
            self.skipTest("repo-root Procfile.dev not present in this checkout")

        tmpdir = make_test_temp_dir(self, "procfile-packaged-vs-root")
        self._chdir(tmpdir)

        packaged = default_procfile_path()

        self.assertEqual(
            packaged.read_text(encoding="utf-8"),
            repo_root_procfile.read_text(encoding="utf-8"),
        )

    def test_packaged_procfile_round_trips_through_parse_file(self):
        tmpdir = make_test_temp_dir(self, "procfile-packaged-roundtrip")
        self._chdir(tmpdir)

        result = parse_file(default_procfile_path())

        self.assertEqual(result, [("flask", ["python", "-m", "src.main"])])


if __name__ == "__main__":
    unittest.main()
