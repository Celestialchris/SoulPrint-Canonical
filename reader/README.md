# SoulPrint Reader Backend

A FastAPI service that accepts text, chunks it for TTS, and generates per-chunk audio via Chatterbox-TTS. Chunks are served progressively so the first chunk becomes playable before the full job finishes.

This is a separate service from the SoulPrint Flask app and runs in its own Python environment.

## Prerequisites

- An existing Chatterbox virtualenv (e.g. `D:\VoiceForge\.venv-chatter`) with Python 3.11, `chatterbox-tts`, `torch`, and `torchaudio` installed.
- An NVIDIA GPU with CUDA for realistic generation speeds (CPU mode is supported but slow).
- A directory of reference voice clips (`.wav`) for Chatterbox to clone from.

## Install

Install the API-layer dependencies into the Chatterbox venv:

```powershell
D:\VoiceForge\.venv-chatter\Scripts\pip.exe install -r reader\requirements.txt
```

`torch`, `torchaudio`, and `chatterbox-tts` are NOT in `requirements.txt`; they are already present in the Chatterbox venv.

## Run

```powershell
$env:READER_HOME = "D:\VoiceForge"
D:\VoiceForge\.venv-chatter\Scripts\python.exe -m uvicorn reader.backend.app:app --host 127.0.0.1 --port 5001
```

The service listens on `http://127.0.0.1:5001`.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `READER_HOME` | `D:\VoiceForge` | Root for refs and output. |
| `READER_REFS_DIR` | `$READER_HOME\refs` | Directory of reference voice `.wav` files. |
| `READER_OUTPUT_DIR` | `$READER_HOME\output` | Directory where generated chunk WAVs are written, one subdirectory per job. |
| `READER_CORS_ORIGIN` | `http://127.0.0.1:5173` | Allowed CORS origin (Reader UI dev server). |

Setting `READER_HOME` alone moves both refs and output together. The other two variables override individually when set.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Engine status, device, configured paths. |
| GET | `/voices` | List `.wav` files in the refs directory. |
| POST | `/generate` | Start a generation job. Body: `{ text, voice, speed }`. |
| GET | `/jobs/{job_id}` | Job state with per-chunk status and audio URLs for ready chunks. |
| GET | `/audio/{job_id}/{filename}` | Serve a generated chunk WAV. |

Generation is progressive: chunks generate sequentially and each chunk's audio URL appears in `/jobs/{job_id}` as soon as that chunk finishes. The client can begin playback after chunk 1 without waiting for the full job.

## Test

```powershell
D:\VoiceForge\.venv-chatter\Scripts\python.exe -m pytest reader\tests\ -v
```

All tests run without a GPU: the TTS engine is mocked and the background worker runs synchronously under test.
