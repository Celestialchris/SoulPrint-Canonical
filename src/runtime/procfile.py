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
from pathlib import Path

_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")


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
    """Parse Procfile text into ``(name, command_tokens)`` pairs in declared order."""

    services: list[tuple[str, list[str]]] = []
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
        tokens = command.split()
        services.append((name, tokens))
    return services


def parse_file(path: str | Path) -> list[tuple[str, list[str]]]:
    """Read ``path`` and parse it as a Procfile."""

    text = Path(path).read_text(encoding="utf-8")
    return parse(text)
