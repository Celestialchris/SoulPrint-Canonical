"""Service probe primitives.

A ``ServiceProbe`` answers one question: is this named local service currently
healthy? Probes are dependency-free (stdlib only) so they can run inside the
supervisor, inside the Flask process, or inside the CLI without dragging an
HTTP client library into the runtime path.

Probes do not own service discovery. Callers read ``ports.json`` (Layer B
runtime state owned by ``src.runtime.ports``) and decide which probes to run.
"""

from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """Outcome of a single ``ServiceProbe.probe()`` call."""

    name: str
    ok: bool
    latency_ms: float | None
    detail: str


class ServiceProbe(Protocol):
    """One named, local health probe.

    Implementations return a ``ProbeResult`` carrying their own ``name`` and a
    short human-readable ``detail`` line. Probes must not raise on failure;
    failures are reported as ``ok=False``.
    """

    name: str

    def probe(self) -> ProbeResult: ...


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Block ``urlopen`` from following redirects so 3xx stays observable."""

    def http_error_301(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    http_error_302 = http_error_301
    http_error_303 = http_error_301
    http_error_307 = http_error_301
    http_error_308 = http_error_301


class HTTPProbe:
    """Probe a local HTTP service with one GET request.

    HTTP 2xx and 3xx are treated as healthy. HTTP 4xx/5xx, connection refused,
    DNS failures, and timeouts are treated as unhealthy. Latency is measured
    in milliseconds for any completed exchange (success or HTTP-level failure)
    and is ``None`` only when no exchange occurred.
    """

    def __init__(self, name: str, url: str, timeout_seconds: float = 0.5) -> None:
        self.name = name
        self.url = url
        self.timeout_seconds = timeout_seconds

    def probe(self) -> ProbeResult:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        start = time.perf_counter()
        try:
            response = opener.open(self.url, timeout=self.timeout_seconds)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            try:
                code = response.getcode()
                reason = getattr(response, "reason", "") or ""
            finally:
                response.close()
            detail = f"{code} {reason}".strip() or f"HTTP {code}"
            return ProbeResult(
                name=self.name,
                ok=True,
                latency_ms=elapsed_ms,
                detail=detail,
            )
        except urllib.error.HTTPError as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            reason = getattr(exc, "reason", "") or ""
            reason_text = reason if isinstance(reason, str) else str(reason)
            if 300 <= exc.code < 400:
                detail = f"{exc.code} {reason_text}".strip() or f"HTTP {exc.code}"
                return ProbeResult(
                    name=self.name,
                    ok=True,
                    latency_ms=elapsed_ms,
                    detail=detail,
                )
            return ProbeResult(
                name=self.name,
                ok=False,
                latency_ms=elapsed_ms,
                detail=f"HTTP {exc.code}",
            )
        except urllib.error.URLError as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            inner = exc.reason
            if isinstance(inner, (socket.timeout, TimeoutError)):
                detail = "timeout"
            else:
                detail = f"connection error: {inner}" if inner else "connection error"
            return ProbeResult(
                name=self.name,
                ok=False,
                latency_ms=elapsed_ms,
                detail=detail,
            )
        except (socket.timeout, TimeoutError):
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return ProbeResult(
                name=self.name,
                ok=False,
                latency_ms=elapsed_ms,
                detail="timeout",
            )
