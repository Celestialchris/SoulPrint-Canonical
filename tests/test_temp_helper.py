"""Regression tests for shared repo-local test temp helpers."""

from __future__ import annotations

import unittest

from tests.temp_helpers import create_test_temp_dir, test_temp_root


class TestTempHelperTest(unittest.TestCase):
    def test_create_test_temp_dir_uses_repo_local_tmp_tests_root_and_cleans_up(self):
        temp_dir = create_test_temp_dir("temp-helper")
        self.addCleanup(lambda: temp_dir.cleanup() if temp_dir.path.exists() else None)

        self.assertTrue(temp_dir.path.is_relative_to(test_temp_root()))
        self.assertTrue(temp_dir.path.exists())

        temp_dir.cleanup()

        self.assertFalse(temp_dir.path.exists())


if __name__ == "__main__":
    unittest.main()
