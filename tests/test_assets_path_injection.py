"""Regression tests for the CodeQL py/path-injection canonical-shape sanitizer in store_asset.

The fix inlines os.path.realpath + str.startswith at the asset write sinks (assets.py
mkdir + write_bytes). These tests verify the sanitizer accepts legitimate writes,
rejects symlink-based escapes, and does not regress on hostile filenames.
"""

from __future__ import annotations

import io
import os
import unittest
from pathlib import Path

from flask import Flask

from src.app.assets import store_asset
from src.app.models.db import db
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class AssetsPathInjectionTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = make_test_temp_dir(self, "assets-path-injection")
        self.instance_root = self.tmpdir / "inst"
        self.instance_root.mkdir(parents=True, exist_ok=True)

        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{self.tmpdir / 'test.db'}"
        )
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def test_normal_write_lands_under_instance_root(self):
        with self.app.app_context():
            stream = io.BytesIO(b"in-base payload")
            asset, _ = store_asset(
                stream,
                "hello.txt",
                instance_root=self.instance_root,
            )
            written = self.instance_root / asset.storage_path

        self.assertTrue(written.exists())
        self.assertEqual(written.read_bytes(), b"in-base payload")

        base_real = os.path.realpath(str(self.instance_root))
        target_real = os.path.realpath(str(written))
        self.assertTrue(
            target_real == base_real
            or target_real.startswith(base_real.rstrip(os.sep) + os.sep)
        )

    def test_symlink_escape_raises_value_error(self):
        outside = self.tmpdir / "outside"
        outside.mkdir()

        assets_link = self.instance_root / "assets"
        try:
            os.symlink(str(outside), str(assets_link), target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not supported in this environment")

        with self.app.app_context():
            stream = io.BytesIO(b"escape payload")
            with self.assertRaises(ValueError):
                store_asset(
                    stream,
                    "evil.txt",
                    instance_root=self.instance_root,
                )

        # Confirm the bytes never landed at the symlinked-out location.
        leaked = list(outside.rglob("*"))
        self.assertEqual(leaked, [])

    def test_traversal_filename_still_lands_in_base(self):
        with self.app.app_context():
            stream = io.BytesIO(b"hostile filename payload")
            asset, _ = store_asset(
                stream,
                "../../../etc/passwd",
                instance_root=self.instance_root,
            )
            written = self.instance_root / asset.storage_path

        self.assertTrue(written.exists())

        base_real = os.path.realpath(str(self.instance_root))
        target_real = os.path.realpath(str(written))
        self.assertTrue(
            target_real == base_real
            or target_real.startswith(base_real.rstrip(os.sep) + os.sep)
        )


if __name__ == "__main__":
    unittest.main()
