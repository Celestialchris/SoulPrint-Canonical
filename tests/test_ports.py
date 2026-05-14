"""Tests for ``src/runtime/ports.py`` covering B2 of Campaign 02."""

from __future__ import annotations

import json
import os
import socket
import unittest

from src import soulprint_home
from src.runtime import ports
from tests.temp_helpers import temp_soulprint_home


def _bind_listener(host: str = "127.0.0.1") -> tuple[socket.socket, int]:
    """Bind a listening socket to an OS-assigned ephemeral port."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, 0))
    sock.listen(1)
    return sock, sock.getsockname()[1]


class AllocatePortTest(unittest.TestCase):
    def test_preferred_port_free_returns_preferred(self):
        # An OS-assigned ephemeral port we then release is overwhelmingly
        # likely to remain free for the immediate next bind attempt in the
        # same process. This is the standard pattern for port-probe tests.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        preferred = sock.getsockname()[1]
        sock.close()

        result = ports.allocate_port("127.0.0.1", preferred)

        self.assertEqual(result, preferred)

    def test_occupied_preferred_walks_to_next_free_port(self):
        listener, busy_port = _bind_listener()
        self.addCleanup(listener.close)

        result = ports.allocate_port("127.0.0.1", busy_port, max_attempts=10)

        self.assertNotEqual(result, busy_port)
        self.assertGreater(result, busy_port)
        self.assertLess(result, busy_port + 10)

    def test_exhaustion_raises_port_exhaustion_error(self):
        listeners: list[socket.socket] = []
        # Bind consecutive ports so allocate_port has nothing free in its
        # window. We bind 5 contiguous ephemeral ports if we can find them.
        first_listener, first_port = _bind_listener()
        listeners.append(first_listener)
        for offset in range(1, 5):
            candidate_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                candidate_sock.bind(("127.0.0.1", first_port + offset))
                candidate_sock.listen(1)
                listeners.append(candidate_sock)
            except OSError:
                candidate_sock.close()
                self.skipTest(
                    "could not bind a contiguous run of ports for exhaustion test"
                )
        for sock in listeners:
            self.addCleanup(sock.close)

        with self.assertRaises(ports.PortExhaustionError) as ctx:
            ports.allocate_port("127.0.0.1", first_port, max_attempts=len(listeners))

        self.assertIn(str(first_port), str(ctx.exception))


class PortsJsonRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.home = temp_soulprint_home(self, "ports-json")
        soulprint_home.ensure_layout()

    def test_write_entry_then_read_entries_round_trip(self):
        ports.write_entry("flask", "127.0.0.1", 5678, 12345, started_at=1_700_000_000.0)

        entries = ports.read_entries()

        self.assertIn("flask", entries)
        self.assertEqual(entries["flask"]["host"], "127.0.0.1")
        self.assertEqual(entries["flask"]["port"], 5678)
        self.assertEqual(entries["flask"]["pid"], 12345)
        self.assertEqual(entries["flask"]["started_at"], 1_700_000_000.0)

    def test_ports_json_schema_version_is_one(self):
        ports.write_entry("flask", "127.0.0.1", 5678, 12345)

        path = soulprint_home.run_dir() / "ports.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["schema_version"], 1)
        self.assertIn("services", data)
        self.assertIn("flask", data["services"])

    def test_clear_entry_removes_one_service(self):
        ports.write_entry("flask", "127.0.0.1", 5678, 12345)
        ports.write_entry("worker", "127.0.0.1", 5679, 12346)

        ports.clear_entry("flask")

        entries = ports.read_entries()
        self.assertNotIn("flask", entries)
        self.assertIn("worker", entries)

    def test_clear_entry_removes_file_when_no_services_remain(self):
        ports.write_entry("flask", "127.0.0.1", 5678, 12345)
        path = soulprint_home.run_dir() / "ports.json"
        self.assertTrue(path.exists())

        ports.clear_entry("flask")

        self.assertFalse(path.exists())
        self.assertEqual(ports.read_entries(), {})

    def test_clear_entry_is_safe_when_file_missing(self):
        # Should not raise.
        ports.clear_entry("flask")

        self.assertEqual(ports.read_entries(), {})


class IsPidAliveTest(unittest.TestCase):
    def test_returns_true_for_current_process(self):
        self.assertTrue(ports.is_pid_alive(os.getpid()))

    def test_returns_false_for_implausible_pid(self):
        # 2**31 - 1 is well outside any realistic live pid range.
        self.assertFalse(ports.is_pid_alive(2_147_483_647))

    def test_returns_false_for_nonpositive_pid(self):
        self.assertFalse(ports.is_pid_alive(0))
        self.assertFalse(ports.is_pid_alive(-1))


if __name__ == "__main__":
    unittest.main()
