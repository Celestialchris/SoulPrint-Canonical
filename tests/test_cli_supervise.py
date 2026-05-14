"""Tests for the internal ``_supervise`` CLI subcommand (Campaign 02 B2)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src import cli


class CliSuperviseDispatchTest(unittest.TestCase):
    def _run_cli(self, argv: list[str]) -> int:
        with self.assertRaises(SystemExit) as ctx:
            cli.main(argv)
        code = ctx.exception.code
        return int(code) if code is not None else 0

    def test_default_procfile_is_cwd_procfile_dev(self):
        mock_supervisor = MagicMock()
        mock_supervisor.return_value.run.return_value = 0

        with patch("src.runtime.supervisor.Supervisor", mock_supervisor):
            code = self._run_cli(["_supervise"])

        self.assertEqual(code, 0)
        mock_supervisor.return_value.run.assert_called_once()
        called_path = mock_supervisor.return_value.run.call_args.args[0]
        self.assertEqual(called_path, Path.cwd() / "Procfile.dev")

    def test_procfile_flag_overrides_default(self):
        mock_supervisor = MagicMock()
        mock_supervisor.return_value.run.return_value = 0
        override = "C:\\tmp\\custom\\Procfile.dev"

        with patch("src.runtime.supervisor.Supervisor", mock_supervisor):
            code = self._run_cli(["_supervise", "--procfile", override])

        self.assertEqual(code, 0)
        called_path = mock_supervisor.return_value.run.call_args.args[0]
        self.assertEqual(called_path, Path(override))

    def test_exit_code_from_supervisor_propagates(self):
        mock_supervisor = MagicMock()
        mock_supervisor.return_value.run.return_value = 2

        with patch("src.runtime.supervisor.Supervisor", mock_supervisor):
            code = self._run_cli(["_supervise"])

        self.assertEqual(code, 2)


class CliServeUnchangedTest(unittest.TestCase):
    def test_serve_command_path_does_not_invoke_supervisor(self):
        # Patch both the existing serve dispatch and the Supervisor entrypoint.
        # ``serve`` must run its own server, never the supervisor.
        with patch("src.main.main") as run_server_mock, patch(
            "src.runtime.supervisor.Supervisor"
        ) as supervisor_mock:
            cli.main(["serve", "--no-browser"])

        run_server_mock.assert_called_once()
        supervisor_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
