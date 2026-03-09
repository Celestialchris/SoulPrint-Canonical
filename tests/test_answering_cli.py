"""Tests for answering CLI output."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

from src.answering import cli
from src.retrieval import FederatedReadResult


class AnsweringCliTest(unittest.TestCase):
    def test_cli_uses_compact_terms_for_natural_language_question(self):
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
        with patch("src.answering.cli.federated_search", return_value=fake_hits) as mocked_search:
            with patch(
                "sys.argv",
                ["answer-cli", "What did I note about Lisbon food and restaurants?", "--limit-per-lane", "5"],
            ):
                with redirect_stdout(output):
                    exit_code = cli.main()

        self.assertEqual(exit_code, 0)
        _, kwargs = mocked_search.call_args
        self.assertEqual(kwargs["keyword"], "lisbon food restaurants")
        self.assertEqual(kwargs["limit_per_lane"], 5)

        text = output.getvalue()
        self.assertIn("status: grounded", text)
        self.assertIn('"stable_id": "memory:1"', text)


if __name__ == "__main__":
    unittest.main()
