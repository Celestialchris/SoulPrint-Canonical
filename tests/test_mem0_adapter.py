"""Tests for the optional mem0 adapter boundary."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.retrieval.federated import FederatedReadResult
from src.retrieval.mem0_adapter import _canonical_pointer_payload, ingest_federated_items, query_mem0


class Mem0AdapterTest(unittest.TestCase):
    def test_canonical_pointer_payload_preserves_boundary_contract_fields(self):
        item = FederatedReadResult(
            source_lane="imported_conversation",
            stable_id="imported_conversation:42",
            title="Trip planning",
            timestamp_unix=1710000300.0,
            source_metadata={
                "source": "chatgpt",
                "source_conversation_id": "conv-1",
            },
        )

        payload = _canonical_pointer_payload(item)

        self.assertEqual(payload["canonical"]["source_lane"], item.source_lane)
        self.assertEqual(payload["canonical"]["stable_id"], item.stable_id)
        self.assertEqual(payload["canonical"]["timestamp_unix"], item.timestamp_unix)
        self.assertEqual(payload["canonical"]["source_metadata"], item.source_metadata)

    def test_ingest_is_noop_when_mem0_disabled(self):
        item = FederatedReadResult(
            source_lane="native_memory",
            stable_id="memory:1",
            title="Lisbon food notes",
            timestamp_unix=1710000000.0,
            source_metadata={"role": "user", "tags": "travel"},
        )

        with patch.dict(os.environ, {"SOULPRINT_MEM0_ENABLED": "false"}, clear=False):
            report = ingest_federated_items([item])

        self.assertFalse(report.enabled)
        self.assertEqual(report.attempted, 0)
        self.assertEqual(report.accepted, 0)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.skipped, 1)
        self.assertEqual(query_mem0("anything"), [])


if __name__ == "__main__":
    unittest.main()
