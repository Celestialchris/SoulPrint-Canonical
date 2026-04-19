"""JSONL append-only store for derived intelligence artifacts."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path

from .summarizer import DerivedSummary


# ---------------------------------------------------------------------------
# Generic JSONL helpers (shared across all artifact types)
# ---------------------------------------------------------------------------

def _append_jsonl(path: Path, data: dict) -> None:
    """Append one JSON object as a line to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _list_jsonl(path: Path, limit: int = 50) -> list[dict]:
    """Read JSONL, return newest-first up to *limit*."""
    if not path.exists():
        return []

    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if not cleaned:
                continue
            rows.append(json.loads(cleaned))

    return list(reversed(rows[-limit:]))


def _get_jsonl(path: Path, id_field: str, id_value: str) -> dict | None:
    """Scan JSONL for one record matching *id_field* == *id_value*."""
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if not cleaned:
                continue
            record = json.loads(cleaned)
            if record.get(id_field) == id_value:
                return record

    return None


def _rewrite_jsonl_atomically(path: Path, rows: list[dict]) -> None:
    """Atomic JSONL rewrite via temp file + os.replace."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Summaries (Phase 7.1 — unchanged public API)
# ---------------------------------------------------------------------------

def default_summary_store_path(sqlite_path: str) -> Path:
    """Store summaries beside SQLite as an explicit derived JSONL surface."""

    db_path = Path(sqlite_path)
    return db_path.parent / "derived_summaries.jsonl"


def append_summary(store_path: str | Path, summary: DerivedSummary) -> None:
    """Append one derived summary to the on-disk JSONL store."""

    _append_jsonl(Path(store_path), asdict(summary))


def list_summaries(store_path: str | Path, limit: int = 50) -> list[dict]:
    """Return newest-first derived summaries from JSONL store."""

    return _list_jsonl(Path(store_path), limit)


def get_summary(store_path: str | Path, summary_id: str) -> dict | None:
    """Lookup one summary by id by scanning the full JSONL store."""

    return _get_jsonl(Path(store_path), "summary_id", summary_id)


def delete_summaries_for_conversation(store_path: str | Path, stable_id: str) -> int:
    """Delete all summaries referencing *stable_id*. Returns count deleted."""
    path = Path(store_path)
    if not path.exists():
        return 0
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if cleaned:
                rows.append(json.loads(cleaned))
    kept = [r for r in rows if r.get("source_conversation_stable_id") != stable_id]
    deleted = len(rows) - len(kept)
    if deleted == 0:
        return 0
    _rewrite_jsonl_atomically(path, kept)
    return deleted


def list_summaries_for_conversation(store_path: str | Path, stable_id: str) -> list[dict]:
    """Return all summaries referencing *stable_id*."""
    all_rows = _list_jsonl(Path(store_path), limit=9999)
    return [r for r in all_rows if r.get("source_conversation_stable_id") == stable_id]


# ---------------------------------------------------------------------------
# Topic scans (Phase 7.2)
# ---------------------------------------------------------------------------

def default_topic_store_path(sqlite_path: str) -> Path:
    """Store topic scans beside SQLite."""

    db_path = Path(sqlite_path)
    return db_path.parent / "topic_scans.jsonl"


def append_topic_scan(store_path: str | Path, scan) -> None:
    """Append one topic scan to the on-disk JSONL store."""

    _append_jsonl(Path(store_path), asdict(scan))


def list_topic_scans(store_path: str | Path, limit: int = 50) -> list[dict]:
    """Return newest-first topic scans from JSONL store."""

    return _list_jsonl(Path(store_path), limit)


def get_topic_scan(store_path: str | Path, scan_id: str) -> dict | None:
    """Lookup one topic scan by id."""

    return _get_jsonl(Path(store_path), "scan_id", scan_id)


def delete_topic_scans_for_conversation(store_path: str | Path, stable_id: str) -> int:
    """Delete all topic scans where any cluster references *stable_id*. Returns count deleted."""
    path = Path(store_path)
    if not path.exists():
        return 0
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if cleaned:
                rows.append(json.loads(cleaned))
    kept = [
        r for r in rows
        if not any(
            stable_id in c.get("conversation_stable_ids", [])
            for c in r.get("clusters", [])
        )
    ]
    deleted = len(rows) - len(kept)
    if deleted == 0:
        return 0
    _rewrite_jsonl_atomically(path, kept)
    return deleted


def list_topic_scans_for_conversation(store_path: str | Path, stable_id: str) -> list[dict]:
    """Return all topic scans where any cluster references *stable_id*."""
    all_rows = _list_jsonl(Path(store_path), limit=9999)
    return [
        r for r in all_rows
        if any(stable_id in c.get("conversation_stable_ids", []) for c in r.get("clusters", []))
    ]


# ---------------------------------------------------------------------------
# Digests (Phase 7.2)
# ---------------------------------------------------------------------------

def default_digest_store_path(sqlite_path: str) -> Path:
    """Store digests beside SQLite."""

    db_path = Path(sqlite_path)
    return db_path.parent / "derived_digests.jsonl"


def append_digest(store_path: str | Path, digest) -> None:
    """Append one derived digest to the on-disk JSONL store."""

    _append_jsonl(Path(store_path), asdict(digest))


def list_digests(store_path: str | Path, limit: int = 50) -> list[dict]:
    """Return newest-first digests from JSONL store."""

    return _list_jsonl(Path(store_path), limit)


def get_digest(store_path: str | Path, digest_id: str) -> dict | None:
    """Lookup one digest by id."""

    return _get_jsonl(Path(store_path), "digest_id", digest_id)


def delete_digests_for_conversation(store_path: str | Path, stable_id: str) -> int:
    """Delete all digests referencing *stable_id*. Returns count deleted."""
    path = Path(store_path)
    if not path.exists():
        return 0
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if cleaned:
                rows.append(json.loads(cleaned))
    kept = [r for r in rows if stable_id not in r.get("source_conversation_stable_ids", [])]
    deleted = len(rows) - len(kept)
    if deleted == 0:
        return 0
    _rewrite_jsonl_atomically(path, kept)
    return deleted


def list_digests_for_conversation(store_path: str | Path, stable_id: str) -> list[dict]:
    """Return all digests referencing *stable_id*."""
    all_rows = _list_jsonl(Path(store_path), limit=9999)
    return [r for r in all_rows if stable_id in r.get("source_conversation_stable_ids", [])]


# ---------------------------------------------------------------------------
# Distillations (multi-conversation distillation)
# ---------------------------------------------------------------------------

def default_distillation_store_path(sqlite_path: str) -> Path:
    """Store distillations beside SQLite."""

    db_path = Path(sqlite_path)
    return db_path.parent / "derived_distillations.jsonl"


def append_distillation(store_path: str | Path, distillation) -> None:
    """Append one derived distillation to the on-disk JSONL store."""

    _append_jsonl(Path(store_path), asdict(distillation))


def list_distillations(store_path: str | Path, limit: int = 50) -> list[dict]:
    """Return newest-first distillations from JSONL store."""

    return _list_jsonl(Path(store_path), limit)


def get_distillation(store_path: str | Path, distillation_id: str) -> dict | None:
    """Lookup one distillation by id."""

    return _get_jsonl(Path(store_path), "distillation_id", distillation_id)


def delete_distillations_for_conversation(store_path: str | Path, stable_id: str) -> int:
    """Delete all distillations referencing *stable_id*. Returns count deleted."""
    path = Path(store_path)
    if not path.exists():
        return 0
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if cleaned:
                rows.append(json.loads(cleaned))
    kept = [r for r in rows if stable_id not in r.get("source_conversation_stable_ids", [])]
    deleted = len(rows) - len(kept)
    if deleted == 0:
        return 0
    _rewrite_jsonl_atomically(path, kept)
    return deleted


def list_distillations_for_conversation(store_path: str | Path, stable_id: str) -> list[dict]:
    """Return all distillations referencing *stable_id*."""
    all_rows = _list_jsonl(Path(store_path), limit=9999)
    return [r for r in all_rows if stable_id in r.get("source_conversation_stable_ids", [])]
