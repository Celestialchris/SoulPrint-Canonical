"""Tests for answering CLI output."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

from src.answering import cli
from src.retrieval import FederatedReadResult


class AnsweringCliTest(unittest.TestCase):
    def test_cli_prints_answer_and_citations(self):
        fake_hits = [
            FederatedReadResult(
                source_lane="native_memory",
                stable_id="memory:1",
                title="Lisbon food notes",
                timestamp_unix=1710000000.0,
                source_metadata={"role": "user", "tags": "travel"},
            )
        ]

        output = StringIO()
        with patch("src.answering.cli.federated_search", return_value=fake_hits):
            with patch("sys.argv", ["answer-cli", "What about Lisbon food?"]):
                with redirect_stdout(output):
                    exit_code = cli.main()

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("status: grounded", text)
        self.assertIn('"stable_id": "memory:1"', text)


if __name__ == "__main__":
    unittest.main()
