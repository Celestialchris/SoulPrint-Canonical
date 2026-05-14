"""SoulPrint local home subdirectories.

Provides ``run/``, ``logs/``, and ``config/`` paths beneath the application
home and a one-shot ``ensure_layout()`` helper that creates them. The home
root itself is owned by ``src/runtime.py::default_app_home()``, which honors
the ``SOULPRINT_HOME`` environment variable for the entire application home
(including the legacy ``instance/`` and ``uploads/`` trees). This module
does not introduce a new ``SOULPRINT_HOME`` meaning; it composes additional
subdirectories under the same existing home.
"""

from __future__ import annotations

from pathlib import Path

from .runtime import default_app_home


def resolve() -> Path:
    """Return the SoulPrint home root by delegating to ``default_app_home()``."""

    return default_app_home()


def run_dir() -> Path:
    """Path for runtime artifacts such as ``ports.json``."""

    return resolve() / "run"


def logs_dir() -> Path:
    """Path for per-service log files. File-based in v1; no rotation."""

    return resolve() / "logs"


def config_dir() -> Path:
    """Path for user-editable config (added by later campaigns)."""

    return resolve() / "config"


def ensure_layout() -> Path:
    """Create the home subdirectories. Idempotent. Returns the home root."""

    home = resolve()
    home.mkdir(parents=True, exist_ok=True)
    run_dir().mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)
    config_dir().mkdir(parents=True, exist_ok=True)
    return home
