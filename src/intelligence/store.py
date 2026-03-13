"""JSONL append-only store for derived summaries (mirrors answering/trace.py)."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .summarizer import DerivedSummary


def default_summary_store_path(sqlite_path: str) -> Path:
    """Store summaries beside SQLite as an explicit derived JSONL surface."""

    db_path = Path(sqlite_path)
    return db_path.parent / "derived_summaries.jsonl"


def append_summary(store_path: str | Path, summary: DerivedSummary) -> None:
    """Append one derived summary to the on-disk JSONL store."""

    path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(summary), ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def list_summaries(store_path: str | Path, limit: int = 50) -> list[dict]:
    """Return newest-first derived summaries from JSONL store."""

    path = Path(store_path)
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


def get_summary(store_path: str | Path, summary_id: str) -> dict | None:
    """Lookup one summary by id by scanning the full JSONL store."""

    path = Path(store_path)
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if not cleaned:
                continue

            summary = json.loads(cleaned)
            if summary.get("summary_id") == summary_id:
                return summary

    return None
