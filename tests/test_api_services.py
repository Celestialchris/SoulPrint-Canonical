"""Tests for the GET /api/services route."""

from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from src import soulprint_home
from src.app import create_app
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


class ApiServicesRouteTest(unittest.TestCase):
    def setUp(self):
        # Override SOULPRINT_HOME so ensure_layout (called inside create_app)
        # and ports.read_entries() both resolve under the temp tree.
        self.home = temp_soulprint_home(self, "api-services-home")
        soulprint_home.ensure_layout()

        self.tmpdir = make_test_temp_dir(self, "api-services-db")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    # Missing ports.json ----------------------------------------------------

    def test_missing_ports_json_returns_empty_degraded_response(self):
        resp = self.client.get("/api/services")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        self.assertEqual(data["schema_version"], 1)
        self.assertFalse(data["ports_json_present"])
        self.assertFalse(data["supervisor_running"])
        self.assertEqual(data["services"], [])

    # Live Flask entry ------------------------------------------------------

    def test_live_flask_entry_reports_expected_fields(self):
        server = _start_healthz_server()
        host, port = server.server_address
        self.addCleanup(_stop_server, server)

        ports.write_entry(
            "flask", host, port, os.getpid(), started_at=1_700_000_000.0
        )

        resp = self.client.get("/api/services")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        self.assertEqual(data["schema_version"], 1)
        self.assertTrue(data["ports_json_present"])
        self.assertTrue(data["supervisor_running"])
        self.assertEqual(len(data["services"]), 1)

        svc = data["services"][0]
        self.assertEqual(svc["name"], "flask")
        self.assertTrue(svc["ok"])
        self.assertEqual(svc["host"], host)
        self.assertEqual(svc["port"], port)
        self.assertEqual(svc["pid"], os.getpid())
        self.assertEqual(svc["started_at"], 1_700_000_000.0)
        self.assertIsNotNone(svc["latency_ms"])
        self.assertIn("200", svc["detail"])

    # Dead PID --------------------------------------------------------------

    def test_dead_pid_returns_not_ok_with_process_not_running_detail(self):
        ports.write_entry(
            "flask", "127.0.0.1", 5678, _DEAD_PID, started_at=1_700_000_000.0
        )

        resp = self.client.get("/api/services")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        self.assertFalse(data["supervisor_running"])
        self.assertEqual(len(data["services"]), 1)
        svc = data["services"][0]
        self.assertEqual(svc["name"], "flask")
        self.assertFalse(svc["ok"])
        self.assertIsNone(svc["latency_ms"])
        self.assertIn("process not running", svc["detail"])

    def test_dead_pid_does_not_invoke_http_probe(self):
        ports.write_entry(
            "flask", "127.0.0.1", 5678, _DEAD_PID, started_at=1_700_000_000.0
        )

        with patch("src.app.HTTPProbe") as mock_probe:
            resp = self.client.get("/api/services")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_probe.call_count, 0)

    # Unknown live service --------------------------------------------------

    def test_unknown_live_service_returns_no_probe_configured(self):
        ports.write_entry(
            "reader", "127.0.0.1", 5173, os.getpid(), started_at=1_700_000_000.0
        )

        resp = self.client.get("/api/services")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        self.assertTrue(data["supervisor_running"])
        self.assertEqual(len(data["services"]), 1)
        svc = data["services"][0]
        self.assertEqual(svc["name"], "reader")
        self.assertTrue(svc["ok"])
        self.assertIsNone(svc["latency_ms"])
        self.assertIn("no probe configured", svc["detail"])

    # Non-GET methods -------------------------------------------------------

    def test_post_method_returns_405(self):
        resp = self.client.post("/api/services")
        self.assertEqual(resp.status_code, 405)

    def test_delete_method_returns_405(self):
        resp = self.client.delete("/api/services")
        self.assertEqual(resp.status_code, 405)

    # Response shape stability ---------------------------------------------

    def test_response_shape_has_stable_top_level_and_service_keys(self):
        ports.write_entry(
            "reader", "127.0.0.1", 5173, os.getpid(), started_at=1_700_000_000.0
        )

        resp = self.client.get("/api/services")
        data = json.loads(resp.data)

        self.assertEqual(
            set(data.keys()),
            {"schema_version", "supervisor_running", "ports_json_present", "services"},
        )
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


if __name__ == "__main__":
    unittest.main()
