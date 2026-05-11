"""Chatterbox-TTS wrapper for the Reader backend.

The proven generation pattern lives in `reader/test_nagato_reference.py`.
This wrapper reuses that exact API: ChatterboxTTS.from_pretrained, model.generate,
torchaudio.save.

Generation is serialized through a module-level threading.Lock so the background
worker thread cannot race itself on a single GPU.

The `speed` parameter is accepted for API forward compatibility. Chatterbox's
`generate` method does not expose a speed control in v1, so it is currently
unused in the underlying call.
"""
from __future__ import annotations

import threading

_LOCK = threading.Lock()
_MODEL = None


def load_model():
    """Lazy-load the Chatterbox model. Returns the singleton instance.

    Reads CUDA availability at call time so test environments without torch
    can still import this module (Chatterbox itself, of course, requires torch).
    """
    global _MODEL
    if _MODEL is None:
        from chatterbox.tts import ChatterboxTTS  # local import: needs .venv-chatter
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MODEL = ChatterboxTTS.from_pretrained(device=device)
    return _MODEL


def generate_chunk(
    text: str,
    ref_audio_path: str,
    output_path: str,
    speed: float = 1.0,
) -> str:
    """Generate a single chunk WAV. Returns the output path.

    Thread-safe via a module-level lock so only one generation runs on the GPU
    at a time.
    """
    import torchaudio as ta

    with _LOCK:
        model = load_model()
        wav = model.generate(text, audio_prompt_path=ref_audio_path)
        ta.save(output_path, wav, model.sr)
    return output_path
