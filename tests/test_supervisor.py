"""Tests for ``Supervisor`` in ``src/runtime/supervisor.py`` (Campaign 02 B2)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src import soulprint_home
from src.runtime import ports as ports_module
from src.runtime.supervisor import (
    EXIT_MALFORMED_PROCFILE,
    EXIT_OK,
    EXIT_START_FAILED,
    Supervisor,
)
from tests.temp_helpers import make_test_temp_dir, temp_soulprint_home


class FakeService:
    """Stand-in for ``LocalService`` used by supervisor tests.

    Tracks start/stop calls and exposes the same attribute surface
    (``name``, ``pid``, ``is_alive()``, ``start()``, ``stop()``).
    """

    instances: list[FakeService] = []

    def __init__(
        self,
        name: str,
        command_tokens: list[str],
        host: str,
        port: int,
        log_path: Path,
        *,
        start_raises: type[BaseException] | None = None,
    ) -> None:
        self.name = name
        self.command_tokens = command_tokens
        self.host = host
        self.port = port
        self.log_path = log_path
        self.pid = 10_000 + len(FakeService.instances)
        self.start_calls = 0
        self.stop_calls = 0
        self._alive = False
        self._start_raises = start_raises
        FakeService.instances.append(self)

    def start(self) -> None:
        self.start_calls += 1
        if self._start_raises is not None:
            raise self._start_raises("simulated start failure")
        self._alive = True

    def stop(self, timeout: float = 5.0) -> None:
        self.stop_calls += 1
        self._alive = False

    def is_alive(self) -> bool:
        return self._alive


def _factory(*, fail_for: str | None = None):
    """Return a service_factory callable suitable for ``Supervisor``."""

    def _make(name, command_tokens, host, port, log_path):
        start_raises = OSError if name == fail_for else None
        return FakeService(
            name,
            command_tokens,
            host,
            port,
            log_path,
            start_raises=start_raises,
        )

    return _make


def _write_procfile(tmpdir: Path, body: str) -> Path:
    path = tmpdir / "Procfile.dev"
    path.write_text(body, encoding="utf-8")
    return path


class SupervisorRunTest(unittest.TestCase):
    def setUp(self):
        FakeService.instances = []
        self.home = temp_soulprint_home(self, "supervisor-run")
        self.tmpdir = make_test_temp_dir(self, "supervisor-procfile")

    def test_parses_procfile_and_starts_services_in_declared_order(self):
        procfile = _write_procfile(
            self.tmpdir,
            "flask: python -m src.main\nworker: python -m src.worker\n",
        )
        supervisor = Supervisor(service_factory=_factory(), poll_interval=0.01)

        with patch("src.runtime.supervisor.time.sleep", side_effect=KeyboardInterrupt):
            code = supervisor.run(procfile)

        self.assertEqual(code, EXIT_OK)
        self.assertEqual(len(FakeService.instances), 2)
        self.assertEqual(FakeService.instances[0].name, "flask")
        self.assertEqual(FakeService.instances[1].name, "worker")
        self.assertEqual(FakeService.instances[0].start_calls, 1)
        self.assertEqual(FakeService.instances[1].start_calls, 1)

    def test_writes_ports_json_entries_for_started_services(self):
        procfile = _write_procfile(self.tmpdir, "flask: python -m src.main\n")
        supervisor = Supervisor(service_factory=_factory(), poll_interval=0.01)

        observed_entries: list[dict[str, object]] = []

        def _capture_then_interrupt(*_args, **_kwargs):
            observed_entries.append(dict(ports_module.read_entries()))
            raise KeyboardInterrupt

        with patch(
            "src.runtime.supervisor.time.sleep",
            side_effect=_capture_then_interrupt,
        ):
            code = supervisor.run(procfile)

        self.assertEqual(code, EXIT_OK)
        self.assertEqual(len(observed_entries), 1)
        first_snapshot = observed_entries[0]
        self.assertIn("flask", first_snapshot)
        self.assertEqual(first_snapshot["flask"]["host"], "127.0.0.1")
        self.assertIsInstance(first_snapshot["flask"]["port"], int)

    def test_keyboard_interrupt_triggers_graceful_shutdown_and_clears_entries(self):
        procfile = _write_procfile(self.tmpdir, "flask: python -m src.main\n")
        supervisor = Supervisor(service_factory=_factory(), poll_interval=0.01)

        with patch("src.runtime.supervisor.time.sleep", side_effect=KeyboardInterrupt):
            code = supervisor.run(procfile)

        self.assertEqual(code, EXIT_OK)
        self.assertEqual(len(FakeService.instances), 1)
        self.assertEqual(FakeService.instances[0].stop_calls, 1)
        self.assertEqual(ports_module.read_entries(), {})

    def test_startup_failure_cleans_up_already_started_services(self):
        procfile = _write_procfile(
            self.tmpdir,
            "flask: python -m src.main\nworker: python -m src.worker\n",
        )
        supervisor = Supervisor(
            service_factory=_factory(fail_for="worker"),
            poll_interval=0.01,
        )

        code = supervisor.run(procfile)

        self.assertEqual(code, EXIT_START_FAILED)
        # The first service was started, then the second failed to start.
        # The first service must have been stopped, and ports.json cleared.
        self.assertEqual(len(FakeService.instances), 2)
        self.assertEqual(FakeService.instances[0].stop_calls, 1)
        self.assertEqual(ports_module.read_entries(), {})

    def test_malformed_procfile_returns_nonzero_and_leaves_no_ports_entries(self):
        procfile = _write_procfile(self.tmpdir, "not a valid procfile line\n")
        supervisor = Supervisor(service_factory=_factory(), poll_interval=0.01)

        code = supervisor.run(procfile)

        self.assertEqual(code, EXIT_MALFORMED_PROCFILE)
        self.assertEqual(len(FakeService.instances), 0)
        self.assertEqual(ports_module.read_entries(), {})

    def test_two_services_receive_distinct_ports(self):
        # FakeService.start() is a no-op that never binds, so without the
        # supervisor's reservation set both allocations would probe and
        # hand back the same preferred port. The fix prevents that.
        procfile = _write_procfile(
            self.tmpdir,
            "flask: python -m src.main\nworker: python -m src.worker\n",
        )
        supervisor = Supervisor(service_factory=_factory(), poll_interval=0.01)

        with patch("src.runtime.supervisor.time.sleep", side_effect=KeyboardInterrupt):
            code = supervisor.run(procfile)

        self.assertEqual(code, EXIT_OK)
        self.assertEqual(len(FakeService.instances), 2)
        port_a = FakeService.instances[0].port
        port_b = FakeService.instances[1].port
        self.assertNotEqual(port_a, port_b)

    def test_service_exit_during_wait_loop_clears_ports_entry(self):
        procfile = _write_procfile(self.tmpdir, "flask: python -m src.main\n")
        supervisor = Supervisor(service_factory=_factory(), poll_interval=0.01)

        state = {"sleep_count": 0}

        def _sleep_side_effect(*_args, **_kwargs):
            state["sleep_count"] += 1
            if state["sleep_count"] == 1:
                # Simulate the child crashing between poll ticks. The next
                # iteration of the wait loop should observe the exit and
                # clear the ports.json entry.
                FakeService.instances[0]._alive = False
                return
            raise KeyboardInterrupt

        with patch.object(ports_module, "clear_entry") as clear_mock, patch(
            "src.runtime.supervisor.time.sleep", side_effect=_sleep_side_effect
        ):
            code = supervisor.run(procfile)

        self.assertEqual(code, EXIT_OK)
        flask_calls = [c for c in clear_mock.call_args_list if c.args == ("flask",)]
        # Once when the wait loop first sees the exit, once at shutdown.
        self.assertEqual(len(flask_calls), 2)


if __name__ == "__main__":
    unittest.main()
