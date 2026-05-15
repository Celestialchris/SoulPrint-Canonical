"""Procfile parser for the local supervisor.

Supports the minimum subset SoulPrint needs:

- one service per line as ``<name>: <command>``;
- blank lines and full-line ``#`` comments are ignored;
- service names match ``[a-zA-Z][a-zA-Z0-9_-]*``;
- commands are tokenized with simple whitespace splitting (no shell);
- no pipes, redirection, ``&&``, or inline comments.
"""

from __future__ import annotations

import re
import sys
import tempfile
from importlib import resources
from pathlib import Path

_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
# Bare ``python`` token bordered by start-of-line / whitespace / colon on the
# left and whitespace / end-of-line on the right. Does not match ``python3``,
# ``pythonista``, or absolute paths like ``/usr/bin/python``.
_BARE_PYTHON_RE = re.compile(r"(?m)(^|[\s:])python(?=\s|$)")


def default_procfile_path() -> Path:
    """Resolve the Procfile path used by bare ``soulprint``.

    Returns the cwd ``Procfile.dev`` when present (the dev-mode override),
    otherwise materializes the packaged ``src/runtime/Procfile.dev`` with the
    bare ``python`` token pinned to ``sys.executable``. The pin prevents
    pip-installed users (pipx shims, desktop launchers, or invoking
    ``/path/to/venv/bin/soulprint`` without activating that venv) from falling
    through to a PATH-resolved ``python`` that may not have ``src`` importable.
    """

    cwd_path = Path.cwd() / "Procfile.dev"
    if cwd_path.exists():
        return cwd_path
    return _materialize_packaged_procfile()


def _materialize_packaged_procfile() -> Path:
    """Write the packaged Procfile to a temp file with ``python`` pinned."""

    if any(ch.isspace() for ch in sys.executable):
        raise RuntimeError(
            f"Cannot materialize packaged Procfile: sys.executable "
            f"{sys.executable!r} contains whitespace, which the Procfile "
            "parser tokenizes with simple whitespace splitting. Run soulprint "
            "from a venv whose interpreter path has no spaces, or place a "
            "Procfile.dev in your working directory."
        )

    packaged_text = (
        resources.files("src.runtime")
        .joinpath("Procfile.dev")
        .read_text(encoding="utf-8")
    )
    pinned_text = _pin_python_to_sys_executable(packaged_text)

    handle = tempfile.NamedTemporaryFile(
        prefix="soulprint-procfile-",
        suffix=".dev",
        delete=False,
        mode="w",
        encoding="utf-8",
    )
    try:
        handle.write(pinned_text)
    finally:
        handle.close()
    return Path(handle.name)


def _pin_python_to_sys_executable(text: str) -> str:
    """Replace bare ``python`` command tokens with ``sys.executable``.

    Uses a callable replacement so backslashes in Windows interpreter paths
    are not re-interpreted as regex backreferences.
    """

    return _BARE_PYTHON_RE.sub(lambda m: m.group(1) + sys.executable, text)


class MalformedProcfileError(ValueError):
    """Raised when a Procfile cannot be parsed.

    Attributes:
        line_number: 1-based line number where parsing failed.
        line: The offending line, with trailing whitespace stripped.
        reason: Short reason string.
    """

    def __init__(self, line_number: int, line: str, reason: str) -> None:
        self.line_number = line_number
        self.line = line
        self.reason = reason
        super().__init__(f"Procfile line {line_number}: {reason}: {line!r}")


def parse(text: str) -> list[tuple[str, list[str]]]:
    """Parse Procfile text into ``(name, command_tokens)`` pairs in declared order.

    Duplicate service names are rejected: ``ports.json`` is keyed by service
    name, so a repeat would silently overwrite the first entry and make the
    first process unreachable to discovery and shutdown bookkeeping.
    """

    services: list[tuple[str, list[str]]] = []
    seen_names: set[str] = set()
    for index, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise MalformedProcfileError(index, raw_line, "missing ':' separator")
        name_part, _, command_part = stripped.partition(":")
        name = name_part.strip()
        command = command_part.strip()
        if not _NAME_RE.match(name):
            raise MalformedProcfileError(index, raw_line, f"invalid service name {name!r}")
        if not command:
            raise MalformedProcfileError(index, raw_line, "empty command")
        if name in seen_names:
            raise MalformedProcfileError(
                index, raw_line, f"duplicate service name {name!r}"
            )
        seen_names.add(name)
        tokens = command.split()
        services.append((name, tokens))
    return services


def parse_file(path: str | Path) -> list[tuple[str, list[str]]]:
    """Read ``path`` and parse it as a Procfile."""

    text = Path(path).read_text(encoding="utf-8")
    return parse(text)
