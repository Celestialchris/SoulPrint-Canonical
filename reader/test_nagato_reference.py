"""Manual smoke check for Chatterbox-TTS generation.

This is NOT a pytest test, despite the filename. It is the proven generation
pattern used by the Reader's TTS engine. Imports and the CUDA model load are
guarded under ``if __name__ == "__main__":`` so that pytest can collect this
file (it lives under ``reader/`` and the filename starts with ``test_``)
without pulling in torchaudio/chatterbox or loading a model on a GPU box.

Run directly to verify your Chatterbox install works:

    python reader/test_nagato_reference.py
"""

if __name__ == "__main__":
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    print("Loading model...")
    model = ChatterboxTTS.from_pretrained(device="cuda")

    text = """I understand. Let's slow this down.

The important thing is not to panic.

We rebuild from the nearest stable point."""

    print("Generating with Nagato reference...")
    wav = model.generate(text, audio_prompt_path="refs/chris_terminal_v01.wav")
    ta.save("outputs/nagato_test.wav", wav, model.sr)
    print("Done. Saved to outputs/nagato_test.wav")
