"""Tests for reader.backend.job_store.

In-memory job state, no I/O, no GPU.
"""
from __future__ import annotations

import pytest

from reader.backend import job_store


@pytest.fixture(autouse=True)
def _clear_store():
    """Reset the in-process job store between tests so they don't leak state."""
    job_store._reset_for_tests()
    yield
    job_store._reset_for_tests()


def _chunks(n: int = 2) -> list[dict]:
    return [
        {"chunk_id": f"c{i + 1:03d}", "index": i, "kind": "paragraph",
         "text": f"chunk {i}", "char_start": 0, "char_end": 7}
        for i in range(n)
    ]


def test_create_and_get_job():
    job = job_store.create_job(
        "job_test_1",
        chunks=_chunks(3),
        voice="nagato_ref.wav",
        speed=1.0,
    )
    assert job["job_id"] == "job_test_1"
    assert job["status"] == "queued"
    assert job["voice"] == "nagato_ref.wav"
    assert job["speed"] == 1.0
    assert job["total_chunks"] == 3
    assert job["current_chunk"] == 0
    assert job["error"] is None
    assert len(job["chunks"]) == 3
    assert all(c["status"] == "pending" for c in job["chunks"])
    assert all(c["audio_url"] is None for c in job["chunks"])

    fetched = job_store.get_job("job_test_1")
    assert fetched is not None
    assert fetched["job_id"] == "job_test_1"


def test_get_nonexistent_job():
    assert job_store.get_job("job_does_not_exist") is None


def test_update_chunk_status_marks_ready_with_url():
    job_store.create_job("job_a", chunks=_chunks(2), voice="v.wav", speed=1.0)
    job_store.update_chunk_status("job_a", "c001", "ready", audio_url="/audio/job_a/c001.wav")

    job = job_store.get_job("job_a")
    chunk = next(c for c in job["chunks"] if c["chunk_id"] == "c001")
    assert chunk["status"] == "ready"
    assert chunk["audio_url"] == "/audio/job_a/c001.wav"

    # Other chunk is still pending.
    other = next(c for c in job["chunks"] if c["chunk_id"] == "c002")
    assert other["status"] == "pending"
    assert other["audio_url"] is None


def test_update_chunk_status_intermediate_state_does_not_require_url():
    job_store.create_job("job_b", chunks=_chunks(2), voice="v.wav", speed=1.0)
    job_store.update_chunk_status("job_b", "c001", "generating")

    job = job_store.get_job("job_b")
    chunk = next(c for c in job["chunks"] if c["chunk_id"] == "c001")
    assert chunk["status"] == "generating"
    assert chunk["audio_url"] is None


def test_set_job_status_complete():
    job_store.create_job("job_c", chunks=_chunks(1), voice="v.wav", speed=1.0)
    job_store.set_job_status("job_c", "complete")

    job = job_store.get_job("job_c")
    assert job["status"] == "complete"


def test_set_job_status_error_carries_message():
    job_store.create_job("job_d", chunks=_chunks(1), voice="v.wav", speed=1.0)
    job_store.set_job_status("job_d", "error", error="CUDA out of memory")

    job = job_store.get_job("job_d")
    assert job["status"] == "error"
    assert job["error"] == "CUDA out of memory"


def test_update_chunk_advances_current_chunk_when_ready():
    job_store.create_job("job_e", chunks=_chunks(3), voice="v.wav", speed=1.0)
    job_store.update_chunk_status("job_e", "c001", "ready", audio_url="/x")
    job = job_store.get_job("job_e")
    assert job["current_chunk"] == 1

    job_store.update_chunk_status("job_e", "c002", "ready", audio_url="/y")
    job = job_store.get_job("job_e")
    assert job["current_chunk"] == 2
