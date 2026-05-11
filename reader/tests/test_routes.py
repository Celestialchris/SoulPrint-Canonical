"""Tests for the Reader FastAPI routes.

TTS is mocked: no GPU, no Chatterbox. Background generation is patched to
run synchronously so tests can assert on post-generation state deterministically.
"""
from __future__ import annotations

import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from reader.backend import config, job_store


def _write_silent_wav(path: Path, duration_s: float = 0.05, framerate: int = 22050) -> None:
    """Write a tiny silent WAV file (used both as fake voice ref and as fake generated audio)."""
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(framerate)
        n_frames = int(duration_s * framerate)
        w.writeframes(b"\x00\x00" * n_frames)


@pytest.fixture
def tmp_paths(tmp_path, monkeypatch):
    refs_dir = tmp_path / "refs"
    output_dir = tmp_path / "output"
    refs_dir.mkdir()
    output_dir.mkdir()
    monkeypatch.setattr(config, "READER_REFS_DIR", str(refs_dir))
    monkeypatch.setattr(config, "READER_OUTPUT_DIR", str(output_dir))
    return {"refs": refs_dir, "output": output_dir}


@pytest.fixture
def mocked_tts(monkeypatch):
    """Replace Chatterbox calls with a silent-WAV writer."""
    from reader.backend import tts_engine

    def fake_load_model():
        return object()

    def fake_generate(text, ref_audio_path, output_path, speed=1.0):
        _write_silent_wav(Path(output_path))
        return output_path

    monkeypatch.setattr(tts_engine, "load_model", fake_load_model)
    monkeypatch.setattr(tts_engine, "generate_chunk", fake_generate)


@pytest.fixture
def sync_worker(monkeypatch):
    """Run the background worker synchronously in the request thread."""
    from reader.backend import app as app_module

    monkeypatch.setattr(app_module, "_launch_worker", app_module._run_job)


@pytest.fixture
def client(tmp_paths, mocked_tts, sync_worker):
    job_store._reset_for_tests()
    from reader.backend.app import app
    return TestClient(app)


# --------------------------------------------------------------------------- #
# health
# --------------------------------------------------------------------------- #


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["engine"] == "chatterbox"
    assert "device" in body
    assert "refs_dir" in body
    assert "output_dir" in body


# --------------------------------------------------------------------------- #
# voices
# --------------------------------------------------------------------------- #


def test_voices_empty_dir(client, tmp_paths):
    r = client.get("/voices")
    assert r.status_code == 200
    assert r.json() == []


def test_voices_finds_wav(client, tmp_paths):
    voice_path = tmp_paths["refs"] / "nagato_ref.wav"
    _write_silent_wav(voice_path)
    r = client.get("/voices")
    assert r.status_code == 200
    voices = r.json()
    assert len(voices) == 1
    assert voices[0]["filename"] == "nagato_ref.wav"
    assert voices[0]["id"] == "nagato_ref.wav"
    # name derived from filename: underscores -> spaces, title-cased, no extension
    assert voices[0]["name"] == "Nagato Ref"


def test_voices_ignores_non_wav(client, tmp_paths):
    _write_silent_wav(tmp_paths["refs"] / "voice.wav")
    (tmp_paths["refs"] / "readme.txt").write_text("not a voice")
    r = client.get("/voices")
    voices = r.json()
    assert [v["filename"] for v in voices] == ["voice.wav"]


# --------------------------------------------------------------------------- #
# generate
# --------------------------------------------------------------------------- #


def test_generate_empty_text(client):
    r = client.post("/generate", json={"text": "", "voice": "v.wav", "speed": 1.0})
    assert r.status_code == 400


def test_generate_whitespace_text(client):
    r = client.post("/generate", json={"text": "   \n  ", "voice": "v.wav", "speed": 1.0})
    assert r.status_code == 400


def test_generate_missing_voice(client):
    r = client.post(
        "/generate",
        json={"text": "Hello world.", "voice": "does_not_exist.wav", "speed": 1.0},
    )
    assert r.status_code == 400


def test_generate_starts_job(client, tmp_paths):
    _write_silent_wav(tmp_paths["refs"] / "v.wav")
    r = client.post(
        "/generate",
        json={"text": "First paragraph.\n\nSecond paragraph.", "voice": "v.wav", "speed": 1.0},
    )
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    # With the synchronous worker patch, the job has fully run by the time the
    # response returns. The initial status is "queued" in the production code path;
    # we tolerate any reachable state to keep the test independent of patch timing.
    assert body["status"] in ("queued", "running", "complete")
    assert body["total_chunks"] >= 1


def test_generate_then_inspect_job(client, tmp_paths):
    _write_silent_wav(tmp_paths["refs"] / "v.wav")
    r = client.post(
        "/generate",
        json={"text": "One. Two. Three.", "voice": "v.wav", "speed": 1.0},
    )
    job_id = r.json()["job_id"]

    job = client.get(f"/jobs/{job_id}").json()
    assert job["job_id"] == job_id
    assert job["total_chunks"] >= 1
    # Sync worker means all chunks should be ready by now.
    assert job["status"] == "complete"
    assert all(c["status"] == "ready" for c in job["chunks"])
    assert all(c["audio_url"] is not None for c in job["chunks"])


# --------------------------------------------------------------------------- #
# jobs
# --------------------------------------------------------------------------- #


def test_job_not_found(client):
    r = client.get("/jobs/nonexistent_job_id")
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# audio
# --------------------------------------------------------------------------- #


def test_audio_not_found(client):
    r = client.get("/audio/fake_job/fake.wav")
    assert r.status_code == 404


def test_audio_serves_generated_chunk(client, tmp_paths):
    _write_silent_wav(tmp_paths["refs"] / "v.wav")
    r = client.post(
        "/generate",
        json={"text": "Hello there.", "voice": "v.wav", "speed": 1.0},
    )
    job_id = r.json()["job_id"]
    job = client.get(f"/jobs/{job_id}").json()
    audio_url = job["chunks"][0]["audio_url"]
    assert audio_url is not None

    audio_r = client.get(audio_url)
    assert audio_r.status_code == 200
    assert audio_r.headers["content-type"].startswith("audio/")


def test_audio_path_traversal_blocked(client, tmp_paths):
    # Even if the path traversal escapes the job dir, the route must not serve
    # files from outside the configured output directory.
    r = client.get("/audio/anyjob/..%2F..%2Fsecret.wav")
    # FastAPI may either reject (404) or normalize. The contract is "do not serve".
    assert r.status_code in (404, 400)


# --------------------------------------------------------------------------- #
# cors
# --------------------------------------------------------------------------- #


def test_cors_header_on_get(client):
    r = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
