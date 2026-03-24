"""JSONL append-only store for derived intelligence artifacts."""

from __future__ import annotations

from dataclasses import asdict
import json
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
