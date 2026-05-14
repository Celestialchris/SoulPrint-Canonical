"""SOULPRINT_HOME canonical local directory layout.

The stable root under which runtime artifacts (ports.json, logs, config files)
live. Independent of `default_app_home()` in `src/runtime.py`, which continues
to govern the legacy `instance/` and `uploads/` paths for backward compatibility.

Default root: ``~/SoulPrint/Home``. Override via ``SOULPRINT_HOME`` env var.
"""

from __future__ import annotations

import os
from pathlib import Path

_ENV_VAR = "SOULPRINT_HOME"
_DEFAULT_HOME = Path.home() / "SoulPrint" / "Home"


def resolve() -> Path:
    """Return the absolute SOULPRINT_HOME path. Does not create the directory.

    Reads ``SOULPRINT_HOME`` env var when set and non-empty; otherwise returns
    the default ``~/SoulPrint/Home``. The env var is read on each call so tests
    can toggle the value freely.
    """

    override = os.environ.get(_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_HOME.expanduser().resolve()


def run_dir() -> Path:
    """Path for runtime artifacts such as ``ports.json``."""

    return resolve() / "run"


def logs_dir() -> Path:
    """Path for per-service log files. File-based in v1; no rotation."""

    return resolve() / "logs"


def config_dir() -> Path:
    """Path for user-editable config (ui.json and similar, added by later campaigns)."""

    return resolve() / "config"


def ensure_layout() -> Path:
    """Create SOULPRINT_HOME and its canonical subdirectories. Idempotent.

    Returns the home root path so callers can compose further paths inline.
    """

    home = resolve()
    home.mkdir(parents=True, exist_ok=True)
    run_dir().mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)
    config_dir().mkdir(parents=True, exist_ok=True)
    return home
