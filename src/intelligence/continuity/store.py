"""JSONL append-only store for continuity artifacts — derived, non-canonical."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from ..store import _append_jsonl, _get_jsonl, _list_jsonl, _rewrite_jsonl_atomically
from .models import ContinuityArtifact


def default_continuity_store_path(sqlite_path: str) -> Path:
    """Store continuity artifacts beside SQLite as an explicit derived JSONL surface."""
    return Path(sqlite_path).parent / "continuity_artifacts.jsonl"


def append_artifact(store_path: str | Path, artifact: ContinuityArtifact) -> None:
    """Append one continuity artifact to the on-disk JSONL store."""
    _append_jsonl(Path(store_path), asdict(artifact))


def list_artifacts(store_path: str | Path, limit: int = 50) -> list[dict]:
    """Return newest-first continuity artifacts from the JSONL store."""
    return _list_jsonl(Path(store_path), limit)


def get_artifact(store_path: str | Path, artifact_id: str) -> dict | None:
    """Lookup one continuity artifact by ID."""
    return _get_jsonl(Path(store_path), "artifact_id", artifact_id)


def list_artifacts_by_type(
    store_path: str | Path,
    artifact_type: str,
    limit: int = 50,
) -> list[dict]:
    """Return newest-first continuity artifacts filtered by type."""
    all_rows = _list_jsonl(Path(store_path), limit=9999)
    filtered = [r for r in all_rows if r.get("artifact_type") == artifact_type]
    return filtered[:limit]


def list_artifacts_for_conversation(
    store_path: str | Path,
    conversation_stable_id: str,
    limit: int = 50,
) -> list[dict]:
    """Return newest-first artifacts that reference a given conversation."""
    path = Path(store_path)
    all_rows = _list_jsonl(path, limit=9999)
    filtered = [
        r for r in all_rows
        if conversation_stable_id in r.get("source_conversation_ids", [])
    ]
    return filtered[:limit]


def delete_artifacts_for_conversation(store_path: str | Path, stable_id: str) -> int:
    """Delete all continuity artifacts referencing *stable_id*. Returns count deleted."""
    path = Path(store_path)
    if not path.exists():
        return 0
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if cleaned:
                rows.append(json.loads(cleaned))
    kept = [r for r in rows if stable_id not in r.get("source_conversation_ids", [])]
    deleted = len(rows) - len(kept)
    if deleted == 0:
        return 0
    _rewrite_jsonl_atomically(path, kept)
    return deleted
