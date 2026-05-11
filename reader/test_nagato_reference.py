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