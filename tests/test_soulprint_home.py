"""Tests for ``src/soulprint_home.py`` covering B1 of Campaign 02."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from src import soulprint_home
from src.config import Config
from tests.temp_helpers import make_test_temp_dir, temp_soulprint_home


class SoulprintHomeTest(unittest.TestCase):
    def _override_env(self, value: str | None) -> None:
        """Set or unset SOULPRINT_HOME and register restore on cleanup."""

        prior = os.environ.get("SOULPRINT_HOME")
        if value is None:
            os.environ.pop("SOULPRINT_HOME", None)
        else:
            os.environ["SOULPRINT_HOME"] = value

        def _restore() -> None:
            if prior is None:
                os.environ.pop("SOULPRINT_HOME", None)
            else:
                os.environ["SOULPRINT_HOME"] = prior

        self.addCleanup(_restore)

    def test_env_var_override_returns_that_path(self):
        tmpdir = make_test_temp_dir(self, "sp-home-env")
        self._override_env(str(tmpdir))

        result = soulprint_home.resolve()

        self.assertEqual(result, Path(str(tmpdir)).resolve())

    def test_default_when_env_unset_returns_user_home_subpath(self):
        self._override_env(None)

        result = soulprint_home.resolve()

        expected = (Path.home() / "SoulPrint" / "Home").resolve()
        self.assertEqual(result, expected)

    def test_ensure_layout_creates_run_logs_config(self):
        home = temp_soulprint_home(self, "sp-ensure")

        returned = soulprint_home.ensure_layout()

        self.assertEqual(returned, home)
        self.assertTrue((home / "run").is_dir())
        self.assertTrue((home / "logs").is_dir())
        self.assertTrue((home / "config").is_dir())

    def test_ensure_layout_is_idempotent(self):
        home = temp_soulprint_home(self, "sp-idem")
        soulprint_home.ensure_layout()

        # Second call must succeed without raising.
        returned = soulprint_home.ensure_layout()

        self.assertEqual(returned, home)
        self.assertTrue((home / "run").is_dir())

    def test_ensure_layout_creates_missing_parents(self):
        tmpdir = make_test_temp_dir(self, "sp-parents")
        deep = tmpdir / "a" / "b" / "soulprint-home"
        self._override_env(str(deep))
        prior_config = Config.SOULPRINT_HOME
        Config.SOULPRINT_HOME = str(deep)
        self.addCleanup(lambda: setattr(Config, "SOULPRINT_HOME", prior_config))

        result = soulprint_home.ensure_layout()

        self.assertTrue(result.is_dir())
        self.assertTrue((result / "run").is_dir())
        self.assertTrue((result / "logs").is_dir())
        self.assertTrue((result / "config").is_dir())

    def test_path_resolvers_compose_under_home(self):
        home = temp_soulprint_home(self, "sp-paths")

        self.assertEqual(soulprint_home.run_dir(), home / "run")
        self.assertEqual(soulprint_home.logs_dir(), home / "logs")
        self.assertEqual(soulprint_home.config_dir(), home / "config")


if __name__ == "__main__":
    unittest.main()
