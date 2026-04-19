# LLM Configuration

Intelligence features (Ask, Distill, Recurring Themes) require an LLM.
Default local path: Ollama + Gemma 4 via the OpenAI-compatible endpoint.

## Environment Variables

```
SOULPRINT_LLM_PROVIDER=openai
SOULPRINT_LLM_BASE_URL=http://localhost:11434/v1
SOULPRINT_LLM_MODEL=gemma4
OLLAMA_CONTEXT_LENGTH=65536    # set in the shell running `ollama serve`, not SoulPrint's shell
```

## Gemma 4 Model Sizes

| Tag | Size | VRAM | Context | Notes |
|---|---|---|---|---|
| gemma4 (e4b) | 9.6 GB | 6+ GB | 128K | recommended default |
| gemma4:26b | 18 GB | 12+ GB | 256K | better summarization |
| gemma4:e2b | 7.2 GB | 4+ GB | 128K | low-end hardware |
| gemma4:31b | 20 GB | 16+ GB | 256K | marginal gain over 26b |

No API key needed for Ollama. For cloud providers, set `SOULPRINT_LLM_API_KEY`.

## Running with Local LLM

```bash
SOULPRINT_LLM_PROVIDER=openai SOULPRINT_LLM_BASE_URL=http://localhost:11434/v1 SOULPRINT_LLM_MODEL=gemma4 python -m src.main
```
