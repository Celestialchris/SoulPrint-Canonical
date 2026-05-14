"""Port allocation and ``ports.json`` runtime state for the supervisor.

The supervisor needs two related primitives:

- pick a free TCP port, walking upward from a preferred port if it is busy;
- record per-service ``(host, port, pid, started_at)`` so other tools can
  discover the running services without re-allocating ports.

``ports.json`` lives under ``$SOULPRINT_HOME/run/`` and carries a
``schema_version`` so later campaigns can extend the format. Writes go through
``os.replace()`` for crash-safe atomic update.
"""

from __future__ import annotations

import errno
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any, Iterable

from src import soulprint_home

SCHEMA_VERSION = 1
_PORTS_FILENAME = "ports.json"


class PortExhaustionError(RuntimeError):
    """Raised when ``allocate_port`` cannot find a free port in its range."""


def _ports_path() -> Path:
    return soulprint_home.run_dir() / _PORTS_FILENAME


def _is_port_free(host: str, port: int) -> bool:
    """Return True if a TCP listen socket can bind ``(host, port)``."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def allocate_port(
    host: str,
    preferred: int,
    max_attempts: int = 10,
    exclude: Iterable[int] | None = None,
) -> int:
    """Return the preferred port if free, otherwise the next available port.

    Walks from ``preferred`` upward by 1 until a port binds, up to
    ``max_attempts`` candidates total. Each probe attempt is printed to stderr
    so cockpit-style observers can surface preferred-port-busy behavior.

    ``exclude`` is a set of ports the caller has already reserved this run.
    Excluded ports are skipped without a socket probe, so the supervisor can
    avoid handing the same port to two services when their actual child
    processes have not yet bound it.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    excluded = set(exclude) if exclude is not None else set()

    for offset in range(max_attempts):
        candidate = preferred + offset
        if candidate in excluded:
            print(
                f"port-allocate: {host}:{candidate} already reserved, trying next",
                file=sys.stderr,
            )
            continue
        if _is_port_free(host, candidate):
            if offset > 0:
                print(
                    f"port-allocate: {host}:{preferred} busy, using {host}:{candidate}",
                    file=sys.stderr,
                )
            return candidate
        print(
            f"port-allocate: {host}:{candidate} busy, trying next",
            file=sys.stderr,
        )

    last_attempt = preferred + max_attempts - 1
    raise PortExhaustionError(
        f"no free port in range {preferred}..{last_attempt} on {host} "
        f"after {max_attempts} attempts"
    )


def _read_raw() -> dict[str, Any]:
    path = _ports_path()
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "services": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "services": {}}
    if not isinstance(data, dict) or "services" not in data:
        return {"schema_version": SCHEMA_VERSION, "services": {}}
    data.setdefault("schema_version", SCHEMA_VERSION)
    if not isinstance(data["services"], dict):
        data["services"] = {}
    return data


def _atomic_write(payload: dict[str, Any]) -> None:
    path = _ports_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def read_entries() -> dict[str, dict[str, Any]]:
    """Return the ``services`` map from ``ports.json`` (empty if missing)."""

    return dict(_read_raw().get("services", {}))


def write_entry(
    name: str,
    host: str,
    port: int,
    pid: int,
    started_at: float | None = None,
) -> None:
    """Record one service entry in ``ports.json`` atomically."""

    data = _read_raw()
    data.setdefault("schema_version", SCHEMA_VERSION)
    services = data.setdefault("services", {})
    services[name] = {
        "host": host,
        "port": port,
        "pid": pid,
        "started_at": float(started_at) if started_at is not None else time.time(),
    }
    _atomic_write(data)


def clear_entry(name: str) -> None:
    """Remove one service entry; delete the file when no services remain."""

    path = _ports_path()
    if not path.exists():
        return
    data = _read_raw()
    services = data.get("services", {})
    if name not in services:
        return
    services.pop(name)
    if not services:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return
    data["services"] = services
    _atomic_write(data)


def is_pid_alive(pid: int) -> bool:
    """Return True if ``pid`` names a live process.

    POSIX uses ``os.kill(pid, 0)``. Windows uses ``OpenProcess`` with the
    ``PROCESS_QUERY_LIMITED_INFORMATION`` access right and closes the handle
    immediately. Neither path actually signals the process.
    """

    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            return True
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        return True
    return True
