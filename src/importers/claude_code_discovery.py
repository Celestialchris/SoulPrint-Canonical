"""Auto-discovery and batch import of Claude Code sessions from ~/.claude/projects/."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiscoveredSession:
    path: Path
    session_id: str
    project_dir_name: str
    project_path: str | None
    summary: str | None
    created: str | None
    modified: str | None
    size_bytes: int
    message_count_estimate: int


@dataclass(frozen=True)
class ImportScanResult:
    imported: list[str]
    skipped_duplicate: list[str]
    failed: list[tuple[str, str]]


def default_claude_projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def normalize_projects_path(raw: str) -> Path:
    """Resolve a user-supplied path, constrained to under Path.home().

    Validates the raw string before any filesystem operation. Rejects
    traversal segments and absolute paths outside home at the string
    level, then uses resolve() to finalize and re-checks via relative_to
    as a defense-in-depth measure.
    """
    # String-level validation (pre-filesystem) to satisfy taint analysis.
    expanded_str = os.path.expanduser(raw)
    # Reject explicit traversal segments before Path() touches the filesystem.
    if ".." in Path(expanded_str).parts:
        raise ValueError("Path traversal segments not allowed")

    home = Path.home().resolve()
    candidate = Path(expanded_str).resolve()
    # Defense-in-depth: validator still runs even if string check misses edge case.
    candidate.relative_to(home)
    return candidate


def discover_sessions(projects_dir: Path) -> list[DiscoveredSession]:
    if not projects_dir.exists() or not projects_dir.is_dir():
        return []

    sessions: list[DiscoveredSession] = []

    for subdir in sorted(projects_dir.iterdir()):
        if not subdir.is_dir():
            continue

        index: dict[str, Any] = {}
        index_path = subdir / "sessions-index.json"
        if index_path.exists():
            try:
                raw = json.loads(index_path.read_text(encoding="utf-8"))
                for entry in raw.get("entries", []):
                    sid = entry.get("sessionId")
                    if sid:
                        index[sid] = entry
            except Exception:
                pass  # treat malformed index as absent

        for jsonl_file in sorted(subdir.glob("*.jsonl")):
            session_id = jsonl_file.stem
            entry = index.get(session_id, {})
            sessions.append(
                DiscoveredSession(
                    path=jsonl_file,
                    session_id=session_id,
                    project_dir_name=subdir.name,
                    project_path=entry.get("projectPath"),
                    summary=entry.get("summary"),
                    created=entry.get("created"),
                    modified=entry.get("modified"),
                    size_bytes=jsonl_file.stat().st_size,
                    message_count_estimate=_count_messages(jsonl_file),
                )
            )

    sessions.sort(key=lambda s: (s.project_dir_name, s.created or ""))
    return sessions


def _count_messages(path: Path) -> int:
    count = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if ('"type":"user"' in line or '"type": "user"' in line or
                        '"type":"assistant"' in line or '"type": "assistant"' in line):
                    count += 1
                    if count >= 1000:
                        break
    except OSError:
        pass
    return count


def import_selected_sessions(
    sessions: list[DiscoveredSession],
    db_path: str,
) -> ImportScanResult:
    from flask import Flask
    from src.app.models.db import db
    from src.importers.registry import parse_import_file
    from src.importers.persistence import persist_normalized_conversations

    imported: list[str] = []
    skipped_duplicate: list[str] = []
    failed: list[tuple[str, str]] = []

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        for session in sessions:
            try:
                parsed = parse_import_file(session.path)
                for conv in parsed.conversations:
                    conv.source_metadata.update({
                        "project_path": session.project_path,
                        "project_dir_name": session.project_dir_name,
                        "session_id": session.session_id,
                    })
                result = persist_normalized_conversations(parsed.conversations)
                if result.imported_conversations > 0:
                    imported.append(session.session_id)
                elif result.skipped_conversations > 0:
                    skipped_duplicate.append(session.session_id)
            except Exception as exc:
                failed.append((session.session_id, str(exc)))
        db.session.remove()
        db.engine.dispose()

    return ImportScanResult(
        imported=imported,
        skipped_duplicate=skipped_duplicate,
        failed=failed,
    )
