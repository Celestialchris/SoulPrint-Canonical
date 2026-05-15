"""Tests for the shared gather_service_data() helper.

The helper backs both /api/services (JSON) and the cockpit (HTML).
These tests exercise the helper directly so the cockpit view can rely on
the same B3 service-status contract without going through the test client.
"""

from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src import soulprint_home
from src.app import create_app, gather_service_data
from src.config import Config
from src.runtime import ports
from tests.temp_helpers import (
    make_test_temp_dir,
    release_app_db_handles,
    temp_soulprint_home,
)


_DEAD_PID = 2_147_483_647


class _HealthzOKHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def _start_healthz_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _HealthzOKHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _stop_server(server: ThreadingHTTPServer) -> None:
    server.shutdown()
    server.server_close()


class GatherServiceDataTest(unittest.TestCase):
    """Direct tests of the helper without going through Flask."""

    def setUp(self):
        self.home = temp_soulprint_home(self, "gather-service-helper")
        soulprint_home.ensure_layout()

    def test_missing_ports_json_returns_degraded_snapshot(self):
        data = gather_service_data()

        self.assertEqual(data["schema_version"], 1)
        self.assertFalse(data["ports_json_present"])
        self.assertFalse(data["supervisor_running"])
        self.assertEqual(data["services"], [])

    def test_dead_pid_marks_service_as_not_running(self):
        ports.write_entry(
            "flask", "127.0.0.1", 5678, _DEAD_PID, started_at=1_700_000_000.0
        )

        data = gather_service_data()

        self.assertTrue(data["ports_json_present"])
        self.assertFalse(data["supervisor_running"])
        self.assertEqual(len(data["services"]), 1)

        svc = data["services"][0]
        self.assertEqual(svc["name"], "flask")
        self.assertFalse(svc["ok"])
        self.assertIsNone(svc["latency_ms"])
        self.assertIn("process not running", svc["detail"])

    def test_live_flask_entry_reports_supervisor_running(self):
        server = _start_healthz_server()
        host, port = server.server_address
        self.addCleanup(_stop_server, server)

        ports.write_entry(
            "flask", host, port, os.getpid(), started_at=1_700_000_000.0
        )

        data = gather_service_data()

        self.assertTrue(data["ports_json_present"])
        self.assertTrue(data["supervisor_running"])
        self.assertEqual(len(data["services"]), 1)

        svc = data["services"][0]
        self.assertEqual(
            set(svc.keys()),
            {
                "name",
                "ok",
                "latency_ms",
                "detail",
                "host",
                "port",
                "pid",
                "started_at",
            },
        )
        self.assertEqual(svc["name"], "flask")
        self.assertTrue(svc["ok"])
        self.assertEqual(svc["host"], host)
        self.assertEqual(svc["port"], port)
        self.assertEqual(svc["pid"], os.getpid())
        self.assertEqual(svc["started_at"], 1_700_000_000.0)
        self.assertIsNotNone(svc["latency_ms"])

    def test_top_level_keys_are_stable(self):
        data = gather_service_data()
        self.assertEqual(
            set(data.keys()),
            {"schema_version", "supervisor_running", "ports_json_present", "services"},
        )


class ApiServicesContractAfterRefactorTest(unittest.TestCase):
    """Smoke test: /api/services still returns the same shape after refactor."""

    def setUp(self):
        self.home = temp_soulprint_home(self, "gather-service-route")
        soulprint_home.ensure_layout()

        self.tmpdir = make_test_temp_dir(self, "gather-service-db")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def test_route_returns_same_shape_as_helper(self):
        ports.write_entry(
            "reader", "127.0.0.1", 5173, os.getpid(), started_at=1_700_000_000.0
        )

        helper_data = gather_service_data()
        resp = self.client.get("/api/services")
        self.assertEqual(resp.status_code, 200)
        route_data = json.loads(resp.data)

        self.assertEqual(set(route_data.keys()), set(helper_data.keys()))
        self.assertEqual(route_data["schema_version"], helper_data["schema_version"])
        self.assertEqual(
            route_data["ports_json_present"], helper_data["ports_json_present"]
        )
        self.assertEqual(
            route_data["supervisor_running"], helper_data["supervisor_running"]
        )
        self.assertEqual(len(route_data["services"]), len(helper_data["services"]))
        if helper_data["services"]:
            self.assertEqual(
                set(route_data["services"][0].keys()),
                set(helper_data["services"][0].keys()),
            )


if __name__ == "__main__":
    unittest.main()
