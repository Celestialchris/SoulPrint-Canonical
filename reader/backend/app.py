"""FastAPI app for the Reader backend.

Endpoints:
    GET  /health
    GET  /voices
    POST /generate
    GET  /jobs/{job_id}
    GET  /audio/{job_id}/{filename}

Job generation runs in a background thread launched by `_launch_worker`. Tests
patch `_launch_worker` to run `_run_job` synchronously for deterministic state.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import config, job_store
from .chunker import chunk_text
from .tts_engine import generate_chunk


def _detect_device() -> str:
    try:
        import torch  # type: ignore

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu_unknown"


app = FastAPI(title="SoulPrint Reader", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.CORS_ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    text: str
    voice: str
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "engine": "chatterbox",
        "device": _detect_device(),
        "refs_dir": config.READER_REFS_DIR,
        "output_dir": config.READER_OUTPUT_DIR,
    }


@app.get("/voices")
def list_voices() -> list[dict[str, str]]:
    refs_dir = config.READER_REFS_DIR
    if not os.path.isdir(refs_dir):
        return []
    voices: list[dict[str, str]] = []
    for filename in sorted(os.listdir(refs_dir)):
        if not filename.lower().endswith(".wav"):
            continue
        stem = os.path.splitext(filename)[0]
        display = stem.replace("_", " ").replace("-", " ").title()
        voices.append({"id": filename, "name": display, "filename": filename})
    return voices


def _run_job(
    job_id: str,
    voice_path: str,
    speed: float,
    chunks: list[dict[str, Any]],
    output_dir: str,
) -> None:
    """Generate every chunk's WAV sequentially, updating the job store as we go."""
    job_store.set_job_status(job_id, "running")
    try:
        os.makedirs(output_dir, exist_ok=True)
        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            job_store.update_chunk_status(job_id, chunk_id, "generating")
            wav_filename = f"{chunk_id}.wav"
            wav_path = os.path.join(output_dir, wav_filename)
            generate_chunk(chunk["text"], voice_path, wav_path, speed=speed)
            audio_url = f"/audio/{job_id}/{wav_filename}"
            job_store.update_chunk_status(job_id, chunk_id, "ready", audio_url=audio_url)
        job_store.set_job_status(job_id, "complete")
    except Exception as exc:  # noqa: BLE001 - we want to capture any failure
        job_store.set_job_status(job_id, "error", error=str(exc))


def _launch_worker(
    job_id: str,
    voice_path: str,
    speed: float,
    chunks: list[dict[str, Any]],
    output_dir: str,
) -> None:
    """Spawn the background generation thread. Tests patch this to run synchronously."""
    t = threading.Thread(
        target=_run_job,
        args=(job_id, voice_path, speed, chunks, output_dir),
        daemon=True,
    )
    t.start()


@app.post("/generate")
def generate(req: GenerateRequest) -> dict[str, Any]:
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    voice_filename = os.path.basename(req.voice)  # defense against path traversal in voice arg
    voice_path = os.path.join(config.READER_REFS_DIR, voice_filename)
    if not os.path.isfile(voice_path):
        raise HTTPException(status_code=400, detail=f"voice not found: {req.voice}")

    chunks = chunk_text(req.text)
    if not chunks:
        raise HTTPException(status_code=400, detail="no chunks produced from text")

    job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    output_dir = os.path.join(config.READER_OUTPUT_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)

    job_store.create_job(job_id, chunks=chunks, voice=voice_filename, speed=req.speed)
    _launch_worker(job_id, voice_path, req.speed, chunks, output_dir)

    return {
        "job_id": job_id,
        "status": "queued",
        "total_chunks": len(chunks),
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/audio/{job_id}/{filename}")
def serve_audio(job_id: str, filename: str):
    output_root = Path(config.READER_OUTPUT_DIR).resolve()
    try:
        job_dir = (output_root / job_id).resolve()
        requested = (job_dir / filename).resolve()
    except (OSError, ValueError):
        raise HTTPException(status_code=404, detail="audio not found")

    # Reject path traversal: requested must live under job_dir, which must live under output_root.
    try:
        requested.relative_to(job_dir)
        job_dir.relative_to(output_root)
    except ValueError:
        raise HTTPException(status_code=404, detail="audio not found")

    if not requested.is_file():
        raise HTTPException(status_code=404, detail="audio not found")
    return FileResponse(str(requested), media_type="audio/wav")
