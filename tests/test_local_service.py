"""Tests for ``LocalService`` in ``src/runtime/supervisor.py`` (Campaign 02 B2)."""

from __future__ import annotations

import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.runtime.supervisor import LocalService
from tests.temp_helpers import make_test_temp_dir


def _make_popen_mock(poll_value=None, pid: int = 12345) -> MagicMock:
    """Build a MagicMock that walks like ``subprocess.Popen`` for drain threads."""

    proc = MagicMock()
    proc.poll.return_value = poll_value
    proc.pid = pid
    proc.stdout = MagicMock()
    proc.stdout.readline.return_value = b""
    proc.stderr = MagicMock()
    proc.stderr.readline.return_value = b""
    return proc


def _make_service(tmpdir: Path, name: str = "flask") -> LocalService:
    return LocalService(
        name=name,
        command_tokens=["python", "-c", "pass"],
        host="127.0.0.1",
        port=5678,
        log_path=tmpdir / f"{name}.log",
    )


class LocalServiceSpawnFlagsTest(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows-only spawn flag check")
    def test_windows_uses_new_process_group(self):
        tmpdir = make_test_temp_dir(self, "ls-win-spawn")
        service = _make_service(tmpdir)

        with patch(
            "src.runtime.supervisor.subprocess.Popen",
            return_value=_make_popen_mock(),
        ) as popen_mock:
            service.start()

        kwargs = popen_mock.call_args.kwargs
        self.assertEqual(
            kwargs["creationflags"], subprocess.CREATE_NEW_PROCESS_GROUP
        )

    @unittest.skipIf(sys.platform == "win32", "POSIX-only preexec_fn check")
    def test_posix_uses_setsid_as_preexec_fn(self):
        import os as os_module

        tmpdir = make_test_temp_dir(self, "ls-posix-spawn")
        service = _make_service(tmpdir)

        with patch(
            "src.runtime.supervisor.subprocess.Popen",
            return_value=_make_popen_mock(),
        ) as popen_mock:
            service.start()

        kwargs = popen_mock.call_args.kwargs
        self.assertIs(kwargs["preexec_fn"], os_module.setsid)


class LocalServiceStopTest(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows graceful-signal path")
    def test_stop_sends_ctrl_break_on_windows(self):
        tmpdir = make_test_temp_dir(self, "ls-win-stop")
        service = _make_service(tmpdir)
        proc = _make_popen_mock(poll_value=None)
        # poll() stays None so stop() enters the graceful-signal path;
        # wait() returning 0 simulates the child exiting after CTRL_BREAK.
        proc.wait.return_value = 0

        with patch("src.runtime.supervisor.subprocess.Popen", return_value=proc):
            service.start()
            service.stop(timeout=0.1)

        proc.send_signal.assert_called_with(signal.CTRL_BREAK_EVENT)

    @unittest.skipIf(sys.platform == "win32", "POSIX graceful-signal path")
    def test_stop_sends_sigterm_on_posix(self):
        tmpdir = make_test_temp_dir(self, "ls-posix-stop")
        service = _make_service(tmpdir)
        proc = _make_popen_mock(poll_value=None, pid=98765)
        proc.wait.return_value = 0

        with patch("src.runtime.supervisor.subprocess.Popen", return_value=proc), patch(
            "src.runtime.supervisor.os.killpg"
        ) as killpg_mock:
            service.start()
            service.stop(timeout=0.1)

        killpg_mock.assert_any_call(98765, signal.SIGTERM)

    def test_stop_hard_kills_after_timeout(self):
        tmpdir = make_test_temp_dir(self, "ls-hardkill")
        service = _make_service(tmpdir)
        proc = _make_popen_mock(poll_value=None, pid=98765)

        wait_call_state = {"count": 0}

        def _wait_side_effect(timeout=None):
            wait_call_state["count"] += 1
            if wait_call_state["count"] == 1:
                raise subprocess.TimeoutExpired(cmd="cmd", timeout=timeout)
            return 0

        proc.wait.side_effect = _wait_side_effect

        with patch("src.runtime.supervisor.subprocess.Popen", return_value=proc):
            if sys.platform == "win32":
                with patch.object(proc, "kill") as kill_mock:
                    service.start()
                    service.stop(timeout=0.01)
                kill_mock.assert_called()
            else:
                with patch("src.runtime.supervisor.os.killpg") as killpg_mock:
                    service.start()
                    service.stop(timeout=0.01)
                # Should see at least SIGTERM and SIGKILL calls.
                signals_sent = [call.args[1] for call in killpg_mock.call_args_list]
                self.assertIn(signal.SIGTERM, signals_sent)
                self.assertIn(signal.SIGKILL, signals_sent)

    def test_stop_is_safe_when_never_started(self):
        tmpdir = make_test_temp_dir(self, "ls-never-started")
        service = _make_service(tmpdir)

        # Should not raise.
        service.stop(timeout=0.1)

        self.assertFalse(service.is_alive())


class LocalServiceLifecycleTest(unittest.TestCase):
    def test_is_alive_false_before_start(self):
        tmpdir = make_test_temp_dir(self, "ls-prestart")
        service = _make_service(tmpdir)

        self.assertFalse(service.is_alive())
        self.assertIsNone(service.pid)

    def test_crash_detection_via_poll(self):
        tmpdir = make_test_temp_dir(self, "ls-crash")
        service = _make_service(tmpdir)
        proc = _make_popen_mock(poll_value=None)

        with patch("src.runtime.supervisor.subprocess.Popen", return_value=proc):
            service.start()
            self.assertTrue(service.is_alive())
            # Simulate child exit by flipping poll() to return non-None.
            proc.poll.return_value = 1
            self.assertFalse(service.is_alive())


class LocalServiceLogDrainTest(unittest.TestCase):
    """Spawn a real short-lived Python child to verify stdout reaches the log."""

    def test_log_file_receives_child_output(self):
        tmpdir = make_test_temp_dir(self, "ls-logdrain")
        log_path = tmpdir / "flask.log"
        service = LocalService(
            name="flask",
            command_tokens=[
                sys.executable,
                "-c",
                "print('hello-from-child', flush=True)",
            ],
            host="127.0.0.1",
            port=5678,
            log_path=log_path,
        )

        service.start()
        # Wait for the child to finish printing and exit on its own.
        for _ in range(50):
            if not service.is_alive():
                break
            time.sleep(0.05)
        # Give drain threads a moment to flush.
        time.sleep(0.1)
        service.stop(timeout=2.0)

        content = log_path.read_bytes()
        self.assertIn(b"hello-from-child", content)


class LocalServiceWindowsIntegrationTest(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows-only spawn-and-stop")
    def test_real_spawn_and_stop_terminates_child(self):
        tmpdir = make_test_temp_dir(self, "ls-win-real")
        script = (
            "import time, sys\n"
            "print('child-started', flush=True)\n"
            "try:\n"
            "    for _ in range(120):\n"
            "        time.sleep(0.5)\n"
            "except KeyboardInterrupt:\n"
            "    print('child-exiting', flush=True)\n"
            "    sys.exit(0)\n"
        )
        service = LocalService(
            name="long-running",
            command_tokens=[sys.executable, "-c", script],
            host="127.0.0.1",
            port=0,
            log_path=tmpdir / "long-running.log",
        )

        service.start()
        # Wait for the child to actually print "child-started" so the
        # interpreter has installed its CTRL_BREAK handler.
        deadline = time.time() + 3.0
        while time.time() < deadline:
            if (tmpdir / "long-running.log").exists() and b"child-started" in (
                tmpdir / "long-running.log"
            ).read_bytes():
                break
            time.sleep(0.05)

        self.assertTrue(service.is_alive())
        service.stop(timeout=5.0)
        self.assertFalse(service.is_alive())


if __name__ == "__main__":
    unittest.main()
