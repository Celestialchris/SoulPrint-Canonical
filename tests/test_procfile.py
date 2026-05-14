"""Tests for ``src/runtime/procfile.py`` covering B2 of Campaign 02."""

from __future__ import annotations

import unittest

from src.runtime.procfile import MalformedProcfileError, parse, parse_file
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


class ProcfileParseFileTest(unittest.TestCase):
    def test_parse_file_reads_disk(self):
        tmpdir = make_test_temp_dir(self, "procfile-parse-file")
        path = tmpdir / "Procfile.dev"
        path.write_text("flask: python -m src.main\n", encoding="utf-8")

        result = parse_file(path)

        self.assertEqual(result, [("flask", ["python", "-m", "src.main"])])


if __name__ == "__main__":
    unittest.main()
