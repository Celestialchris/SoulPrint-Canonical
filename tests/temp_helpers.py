"""Shared helpers for repo-local test temp artifacts and DB teardown."""

from __future__ import annotations

import shutil
import unittest
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


_TEST_TEMP_ROOT = Path.cwd() / ".tmp-tests"


def test_temp_root() -> Path:
    """Return the shared repo-local root for test temp artifacts."""

    _TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    return _TEST_TEMP_ROOT


@dataclass(slots=True)
class TestTempDir:
    """Track a repo-local temp directory so tests can clean it explicitly."""

    path: Path

    def cleanup(self) -> None:
        """Remove the temp directory once app and SQLite handles are released."""

        if not self.path.exists():
            return

        shutil.rmtree(self.path)


def create_test_temp_dir(prefix: str) -> TestTempDir:
    """Create a temp directory scoped under the shared repo-local root."""

    # `tempfile.mkdtemp(dir=...)` produced locked-down directories on Windows here.
    path = test_temp_root() / f"{prefix}-{uuid4().hex}"
    path.mkdir()
    return TestTempDir(path=path)


def make_test_temp_dir(test_case: unittest.TestCase, prefix: str) -> Path:
    """Create a repo-local temp directory and register cleanup on the test case."""

    temp_dir = create_test_temp_dir(prefix)
    test_case.addCleanup(temp_dir.cleanup)
    return temp_dir.path


def release_app_db_handles(app, *, drop_all: bool = False) -> None:
    """Release Flask-SQLAlchemy session and engine handles before temp cleanup."""

    from src.app.models.db import db

    with app.app_context():
        db.session.remove()
        if drop_all:
            db.drop_all()
        db.session.remove()
        db.engine.dispose()
