"""Tests for the cockpit at GET / — the new root surface.

B4 moves the workspace to /library and puts a local runtime cockpit at /.
These tests prove cockpit reflects supervisor state truthfully (running,
not running, dead-PID), surfaces the Reader as unmanaged in v1, and keeps
the brand link and Library nav behaving correctly across both routes.
"""

from __future__ import annotations

import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src import soulprint_home
from src.app import create_app
from src.app.models import ImportedConversation
from src.app.models.db import db
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


class CockpitRouteTest(unittest.TestCase):
    def setUp(self):
        self.home = temp_soulprint_home(self, "cockpit-route-home")
        soulprint_home.ensure_layout()

        self.tmpdir = make_test_temp_dir(self, "cockpit-route-db")
        self.db_path = str(self.tmpdir / "test.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.client = self.app.test_client()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    # ── Smoke and contract ─────────────────────────────────────────────

    def test_root_returns_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_root_rule_endpoint_is_cockpit(self):
        """The Flask url_map must register `/` as the cockpit endpoint."""
        root_rules = [r for r in self.app.url_map.iter_rules() if r.rule == "/"]
        self.assertEqual(len(root_rules), 1, "exactly one rule should match `/`")
        self.assertEqual(root_rules[0].endpoint, "cockpit")

    def test_no_catch_all_route_shadows_root(self):
        """Hitting `/` must reach the cockpit, not be shadowed by a wildcard."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        # The cockpit page title is the most specific marker; if a catch-all
        # rendered a different template, this string would be missing.
        self.assertIn("Cockpit", html)

    # ── Supervisor-not-running empty state ─────────────────────────────

    def test_no_ports_json_renders_supervisor_not_running(self):
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("Supervisor not running", html)

    def test_no_ports_json_renders_link_to_library(self):
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn('href="/library"', html)

    # ── Live Flask service ─────────────────────────────────────────────

    def test_live_flask_service_renders_name_hostport_and_detail(self):
        server = _start_healthz_server()
        host, port = server.server_address
        self.addCleanup(_stop_server, server)

        ports.write_entry(
            "flask", host, port, os.getpid(), started_at=1_700_000_000.0
        )

        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("flask", html)
        self.assertIn(f"{host}:{port}", html)
        # The HTTPProbe detail line contains the HTTP status code on success.
        self.assertIn("200", html)

    # ── Dead PID ───────────────────────────────────────────────────────

    def test_dead_pid_renders_process_not_running_and_no_supervisor_claim(self):
        ports.write_entry(
            "flask", "127.0.0.1", 5678, _DEAD_PID, started_at=1_700_000_000.0
        )

        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("process not running", html)
        # Dead PID means supervisor_running must be False, so the banner
        # should render the not-running line and not contradict itself.
        self.assertIn("Supervisor not running", html)

    # ── Reader unmanaged note ─────────────────────────────────────────

    def test_reader_unmanaged_note_renders(self):
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("Reader", html)
        self.assertIn("unmanaged", html)

    # ── Library nav active state ──────────────────────────────────────

    def test_library_nav_item_not_active_on_root(self):
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        # Locate the Library nav anchor and confirm it is NOT carrying the
        # active class on this page.
        idx = html.find(">Library<")
        self.assertGreater(idx, -1, "Library nav label must be present")
        prefix = html[max(0, idx - 240):idx]
        self.assertNotIn("sidebar-item--active", prefix)

    def test_library_nav_item_active_on_library(self):
        resp = self.client.get("/library")
        html = resp.get_data(as_text=True)
        idx = html.find(">Library<")
        self.assertGreater(idx, -1, "Library nav label must be present")
        prefix = html[max(0, idx - 240):idx]
        self.assertIn("sidebar-item--active", prefix)

    # ── Preferred-port-busy note ──────────────────────────────────────

    def test_preferred_port_busy_note_appears_for_port_5679(self):
        ports.write_entry(
            "flask", "127.0.0.1", 5679, _DEAD_PID, started_at=1_700_000_000.0
        )
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("5678", html)
        self.assertIn("5679", html)
        self.assertIn("busy", html)

    def test_preferred_port_busy_note_absent_for_port_5678(self):
        ports.write_entry(
            "flask", "127.0.0.1", 5678, _DEAD_PID, started_at=1_700_000_000.0
        )
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        # The exact note phrasing must not appear when Flask is on 5678.
        self.assertNotIn("Preferred port 5678 was busy", html)

    # ── Brand wordmark target ─────────────────────────────────────────

    def test_brand_wordmark_link_resolves_to_root(self):
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn('class="sidebar-header__brand" href="/"', html)

    # ── Existing deep links unaffected ────────────────────────────────

    def test_existing_deep_links_still_return_200(self):
        for path in ("/imported", "/archive/health"):
            with self.subTest(path=path):
                resp = self.client.get(path)
                self.assertEqual(
                    resp.status_code,
                    200,
                    f"{path} regressed to {resp.status_code}",
                )

    # ── Ledger pulse with seeded conversations ────────────────────────

    def test_ledger_pulse_renders_imported_titles(self):
        with self.app.app_context():
            conv = ImportedConversation(
                source="chatgpt",
                source_conversation_id="pulse-1",
                title="Pulse conversation",
            )
            db.session.add(conv)
            db.session.commit()

        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        self.assertIn("Pulse conversation", html)


if __name__ == "__main__":
    unittest.main()
