"""Filesystem layout for the durable capture inbox.

Capture payloads are durable, not ephemeral: they live under the application
instance directory (``default_instance_dir() / "inbox"``), not under the
process run directory. The inbox follows a Maildir-style ``tmp``/``new``/``cur``
layout so a future worker can move triaged payloads without races.
"""

from __future__ import annotations

from pathlib import Path

from src.runtime import default_instance_dir


def inbox_root() -> Path:
    return default_instance_dir() / "inbox"


def tmp_dir() -> Path:
    return inbox_root() / "tmp"


def new_dir() -> Path:
    return inbox_root() / "new"


def cur_dir() -> Path:
    return inbox_root() / "cur"


def ensure_inbox_layout() -> None:
    for d in (tmp_dir(), new_dir(), cur_dir()):
        d.mkdir(parents=True, exist_ok=True)
