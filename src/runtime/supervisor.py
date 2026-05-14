"""Local supervisor that runs Procfile services for development.

Two collaborating types:

- ``LocalService`` wraps one ``subprocess.Popen`` child with platform-aware
  process-group handling, log draining via stdlib threads, and a graceful
  ``stop()`` that escalates to a hard kill after a timeout.
- ``Supervisor`` parses a Procfile, allocates ports, starts each service in
  declared order, records entries in ``ports.json``, and shuts everything down
  cleanly on ``KeyboardInterrupt`` or startup failure.

This is a v1 foundation. Children are not auto-restarted on crash; crashes
are logged and remaining services keep running. Later campaigns layer service
probes, cockpit UI, and the staged CLI transition on top of this surface.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Callable

from src import soulprint_home
from src.runtime import ports as ports_module
from src.runtime.procfile import MalformedProcfileError, parse_file

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PREFERRED_PORT = 5678
STOP_TIMEOUT_DEFAULT = 5.0
WAIT_POLL_INTERVAL = 0.5

EXIT_OK = 0
EXIT_MALFORMED_PROCFILE = 2
EXIT_PORT_EXHAUSTED = 3
EXIT_START_FAILED = 4


@dataclass
class LocalService:
    """One supervised local process.

    The service is dormant until ``start()`` is called. ``stop()`` is idempotent
    and safe to call on a never-started or already-stopped service.
    """

    name: str
    command_tokens: list[str]
    host: str
    port: int
    log_path: Path
    _process: subprocess.Popen | None = field(default=None, init=False, repr=False)
    _log_handle: IO[bytes] | None = field(default=None, init=False, repr=False)
    _drain_threads: list[threading.Thread] = field(
        default_factory=list, init=False, repr=False
    )

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None else None

    def is_alive(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    def start(self) -> None:
        """Spawn the child process and begin draining its output."""

        if self._process is not None and self._process.poll() is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_handle = open(self.log_path, "ab", buffering=0)

        child_env = os.environ.copy()
        child_env["SOULPRINT_HOST"] = self.host
        child_env["SOULPRINT_PORT"] = str(self.port)

        popen_kwargs: dict = {
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "bufsize": 0,
            "env": child_env,
        }
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["preexec_fn"] = os.setsid  # noqa: PLW1509

        self._process = subprocess.Popen(self.command_tokens, **popen_kwargs)

        for stream in (self._process.stdout, self._process.stderr):
            if stream is None:
                continue
            thread = threading.Thread(
                target=self._drain_stream,
                args=(stream, self._log_handle),
                name=f"{self.name}-drain",
                daemon=True,
            )
            thread.start()
            self._drain_threads.append(thread)

    def stop(self, timeout: float = STOP_TIMEOUT_DEFAULT) -> None:
        """Stop the child, escalating from graceful signal to hard kill."""

        if self._process is None:
            self._release_log_handle()
            return

        if self._process.poll() is not None:
            self._drain_join_and_close()
            return

        self._send_graceful_signal()
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._send_hard_kill()
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                pass

        self._drain_join_and_close()

    def _drain_stream(self, stream: IO[bytes], log_handle: IO[bytes]) -> None:
        try:
            for chunk in iter(stream.readline, b""):
                try:
                    log_handle.write(chunk)
                except (OSError, ValueError):
                    break
        finally:
            try:
                stream.close()
            except OSError:
                pass

    def _drain_join_and_close(self) -> None:
        for thread in self._drain_threads:
            thread.join(timeout=1.0)
        self._drain_threads = []
        self._release_log_handle()

    def _release_log_handle(self) -> None:
        if self._log_handle is not None:
            try:
                self._log_handle.close()
            except OSError:
                pass
            self._log_handle = None

    def _send_graceful_signal(self) -> None:
        assert self._process is not None
        try:
            if sys.platform == "win32":
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(self._process.pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass

    def _send_hard_kill(self) -> None:
        assert self._process is not None
        try:
            if sys.platform == "win32":
                self._process.kill()
            else:
                os.killpg(self._process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass


ServiceFactory = Callable[[str, list[str], str, int, Path], LocalService]


def _default_service_factory(
    name: str,
    command_tokens: list[str],
    host: str,
    port: int,
    log_path: Path,
) -> LocalService:
    return LocalService(
        name=name,
        command_tokens=command_tokens,
        host=host,
        port=port,
        log_path=log_path,
    )


@dataclass
class Supervisor:
    """Parse a Procfile, start each service, and shut down cleanly."""

    host: str = DEFAULT_HOST
    preferred_port: int = DEFAULT_PREFERRED_PORT
    service_factory: ServiceFactory = field(default=_default_service_factory)
    stop_timeout: float = STOP_TIMEOUT_DEFAULT
    poll_interval: float = WAIT_POLL_INTERVAL

    def run(self, procfile_path: Path) -> int:
        """Run the supervisor synchronously. Returns a process-style exit code."""

        try:
            entries = parse_file(procfile_path)
        except MalformedProcfileError as exc:
            print(f"supervisor: {exc}", file=sys.stderr)
            return EXIT_MALFORMED_PROCFILE
        except OSError as exc:
            print(f"supervisor: cannot read {procfile_path}: {exc}", file=sys.stderr)
            return EXIT_MALFORMED_PROCFILE

        soulprint_home.ensure_layout()
        started: list[LocalService] = []
        assigned_ports: set[int] = set()

        try:
            for name, command_tokens in entries:
                try:
                    port = ports_module.allocate_port(
                        self.host, self.preferred_port, exclude=assigned_ports
                    )
                except ports_module.PortExhaustionError as exc:
                    print(f"supervisor: {exc}", file=sys.stderr)
                    self._stop_all(started)
                    return EXIT_PORT_EXHAUSTED

                log_path = soulprint_home.logs_dir() / f"{name}.log"
                service = self.service_factory(
                    name, command_tokens, self.host, port, log_path
                )

                try:
                    service.start()
                except OSError as exc:
                    print(
                        f"supervisor: failed to start service {name!r}: {exc}",
                        file=sys.stderr,
                    )
                    self._stop_all(started)
                    return EXIT_START_FAILED

                started.append(service)
                assigned_ports.add(port)
                pid_value = service.pid if service.pid is not None else -1
                ports_module.write_entry(name, self.host, port, pid_value)

            return self._wait_loop(started)
        except KeyboardInterrupt:
            self._stop_all(started)
            return EXIT_OK

    def _wait_loop(self, services: list[LocalService]) -> int:
        """Block until KeyboardInterrupt, logging child exits but not restarting.

        When a service is first observed as not alive, its ``ports.json`` entry
        is cleared so the file does not advertise a dead PID/port for the rest
        of the supervisor's lifetime.
        """

        already_logged_exit: set[str] = set()
        try:
            while True:
                time.sleep(self.poll_interval)
                for service in services:
                    if not service.is_alive() and service.name not in already_logged_exit:
                        print(
                            f"supervisor: service {service.name!r} exited",
                            file=sys.stderr,
                        )
                        already_logged_exit.add(service.name)
                        try:
                            ports_module.clear_entry(service.name)
                        except Exception as exc:
                            print(
                                f"supervisor: error clearing ports.json entry "
                                f"for {service.name!r}: {exc}",
                                file=sys.stderr,
                            )
        except KeyboardInterrupt:
            pass
        self._stop_all(services)
        return EXIT_OK

    def _stop_all(self, services: list[LocalService]) -> None:
        for service in services:
            try:
                service.stop(timeout=self.stop_timeout)
            except Exception as exc:
                print(
                    f"supervisor: error stopping {service.name!r}: {exc}",
                    file=sys.stderr,
                )
            try:
                ports_module.clear_entry(service.name)
            except Exception as exc:
                print(
                    f"supervisor: error clearing ports.json entry for {service.name!r}: {exc}",
                    file=sys.stderr,
                )
