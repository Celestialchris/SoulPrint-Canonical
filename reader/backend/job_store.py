"""In-memory job store for Reader generation sessions.

Jobs are ephemeral. v1 holds state in a process-local dict guarded by a
threading.Lock so the background generation thread and the FastAPI request
thread can safely interleave reads and writes.
"""
from __future__ import annotations

import threading
from typing import Any

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def create_job(
    job_id: str,
    chunks: list[dict[str, Any]],
    voice: str,
    speed: float,
) -> dict[str, Any]:
    job = {
        "job_id": job_id,
        "status": "queued",
        "voice": voice,
        "speed": speed,
        "total_chunks": len(chunks),
        "current_chunk": 0,
        "error": None,
        "chunks": [
            {
                "chunk_id": c["chunk_id"],
                "status": "pending",
                "audio_url": None,
            }
            for c in chunks
        ],
    }
    with _LOCK:
        _JOBS[job_id] = job
    # Return a shallow copy so callers cannot accidentally mutate store state.
    return dict(job)


def get_job(job_id: str) -> dict[str, Any] | None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return None
        # Deep-copy chunks list since callers commonly iterate it.
        return {
            **job,
            "chunks": [dict(c) for c in job["chunks"]],
        }


def update_chunk_status(
    job_id: str,
    chunk_id: str,
    status: str,
    audio_url: str | None = None,
) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return
        for chunk in job["chunks"]:
            if chunk["chunk_id"] == chunk_id:
                chunk["status"] = status
                if audio_url is not None:
                    chunk["audio_url"] = audio_url
                break
        # current_chunk = count of chunks that have reached "ready".
        job["current_chunk"] = sum(1 for c in job["chunks"] if c["status"] == "ready")


def set_job_status(
    job_id: str,
    status: str,
    error: str | None = None,
) -> None:
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return
        job["status"] = status
        if error is not None:
            job["error"] = error


def _reset_for_tests() -> None:
    """Test-only hook. Do not call from production code."""
    with _LOCK:
        _JOBS.clear()
