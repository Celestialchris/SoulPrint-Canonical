"""Derived Answer Trace helpers for local answering audit residue."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

from .local import GroundedAnswer


@dataclass(frozen=True)
class AnswerTrace:
    """Derived, append-only audit residue for one answer generation."""

    trace_id: str
    created_at: str
    question: str
    retrieval_terms: str
    status: str
    answer_text: str
    citations: list[dict[str, object]]
    source_lanes: list[str]
    notes: list[str]
    fallback_reason: str | None
    derived_from: str
    trace_kind: str


def default_trace_store_path(sqlite_path: str) -> Path:
    """Store traces beside SQLite as an explicit derived JSONL surface."""

    db_path = Path(sqlite_path)
    return db_path.parent / "answer_traces.jsonl"


def create_answer_trace(
    *,
    question: str,
    retrieval_terms: str,
    answer: GroundedAnswer,
) -> AnswerTrace:
    """Create a minimal derived trace record from one grounded answer result."""

    source_lanes = sorted({citation.source_lane for citation in answer.citations})
    fallback_reason = answer.notes[0] if answer.status == "insufficient_evidence" and answer.notes else None

    return AnswerTrace(
        trace_id=f"answer_trace:{uuid.uuid4()}",
        created_at=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        question=question.strip(),
        retrieval_terms=retrieval_terms.strip(),
        status=answer.status,
        answer_text=answer.answer_text,
        citations=[asdict(citation) for citation in answer.citations],
        source_lanes=source_lanes,
        notes=list(answer.notes),
        fallback_reason=fallback_reason,
        derived_from="canonical_records",
        trace_kind="answer_trace_derived_v1",
    )


def append_answer_trace(trace_store_path: str | Path, trace: AnswerTrace) -> None:
    """Append one derived trace to an on-disk JSONL log."""

    path = Path(trace_store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(trace), ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def list_answer_traces(trace_store_path: str | Path, limit: int = 20) -> list[dict[str, object]]:
    """Return newest-first derived traces from JSONL store."""

    path = Path(trace_store_path)
    if not path.exists():
        return []

    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if not cleaned:
                continue
            rows.append(json.loads(cleaned))

    return list(reversed(rows[-limit:]))


def get_answer_trace(trace_store_path: str | Path, trace_id: str) -> dict[str, object] | None:
    """Lookup one trace by id by scanning the full JSONL store."""

    path = Path(trace_store_path)
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = line.strip()
            if not cleaned:
                continue

            trace = json.loads(cleaned)
            if trace.get("trace_id") == trace_id:
                return trace

    return None
