"""Tests for ``src/runtime/probes.py``."""

from __future__ import annotations

import socket
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.runtime.probes import HTTPProbe, ProbeResult


def _free_local_port() -> int:
    """Pick an ephemeral local port that is free at this instant."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class _OKHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        # Silence the test HTTP server so pytest output stays clean.
        pass


class _RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(301)
        self.send_header("Location", "/somewhere-else")
        self.end_headers()

    def log_message(self, format, *args):
        pass


class _SlowHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.6)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def _start_server(handler_cls) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _stop_server(server: ThreadingHTTPServer) -> None:
    server.shutdown()
    server.server_close()


class HTTPProbeTest(unittest.TestCase):
    def test_returns_ok_for_local_200(self):
        server = _start_server(_OKHandler)
        host, port = server.server_address
        self.addCleanup(_stop_server, server)

        probe = HTTPProbe(name="flask", url=f"http://{host}:{port}/healthz")
        result = probe.probe()

        self.assertIsInstance(result, ProbeResult)
        self.assertEqual(result.name, "flask")
        self.assertTrue(result.ok)
        self.assertIsNotNone(result.latency_ms)
        self.assertGreaterEqual(result.latency_ms, 0.0)
        self.assertIn("200", result.detail)

    def test_returns_ok_for_3xx_redirect_without_following(self):
        server = _start_server(_RedirectHandler)
        host, port = server.server_address
        self.addCleanup(_stop_server, server)

        probe = HTTPProbe(name="flask", url=f"http://{host}:{port}/")
        result = probe.probe()

        self.assertTrue(result.ok)
        self.assertIn("301", result.detail)

    def test_returns_not_ok_for_unreachable_local_port(self):
        port = _free_local_port()

        probe = HTTPProbe(
            name="flask",
            url=f"http://127.0.0.1:{port}/healthz",
            timeout_seconds=0.5,
        )
        result = probe.probe()

        self.assertFalse(result.ok)
        self.assertNotIn("200", result.detail)
        self.assertNotEqual(result.detail, "")

    def test_returns_not_ok_for_timeout(self):
        server = _start_server(_SlowHandler)
        host, port = server.server_address
        self.addCleanup(_stop_server, server)

        probe = HTTPProbe(
            name="flask",
            url=f"http://{host}:{port}/healthz",
            timeout_seconds=0.1,
        )
        result = probe.probe()

        self.assertFalse(result.ok)
        self.assertEqual(result.detail, "timeout")


if __name__ == "__main__":
    unittest.main()
