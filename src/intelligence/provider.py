"""LLM provider protocol and implementations for derived intelligence."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


DEFAULT_MAX_TOKENS = 4096
"""Backend-safe default output budget.

Works across OpenAI, Anthropic, and Ollama/Gemma4 with typical input sizes
without tripping the ``max_tokens + input_tokens <= context_window`` check
that non-OpenAI and local backends enforce server-side.

Distill and continuity-packet call sites override this explicitly with
16384 when they need headroom for long structured output.
"""


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for any LLM backend that can summarize messages."""

    def summarize(
        self,
        messages: list[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str: ...

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str: ...

    @property
    def provider_name(self) -> str: ...


class StubProvider:
    """Returns canned summary text — no API key needed."""

    @property
    def provider_name(self) -> str:
        return "stub"

    def summarize(
        self,
        messages: list[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        msg_count = len(messages)
        roles = {m.get("role", "unknown") for m in messages}
        return (
            f"[Stub summary] This conversation contains {msg_count} messages "
            f"across roles: {', '.join(sorted(roles))}. "
            "Key topics and decisions would be extracted by a real LLM provider."
        )

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        return (
            "[Stub complete] Received system prompt and user message. "
            "A real LLM would process these as separate roles."
        )


class AnthropicProvider:
    """Uses the anthropic SDK to call Claude for summarization."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def summarize(
        self,
        messages: list[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        transcript = "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')}" for m in messages
        )
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=(
                "You are a concise summarizer. Given a conversation transcript, "
                "produce a clear summary preserving key topics, decisions, and "
                "action items. Be factual and brief."
            ),
            messages=[{"role": "user", "content": transcript}],
        )
        return response.content[0].text

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text


class OpenAIProvider:
    """Uses the openai SDK to call any OpenAI-compatible API.

    Works with OpenAI directly, Ollama (local), OpenRouter, and any
    endpoint that implements the /v1/chat/completions contract.

    Env vars:
        SOULPRINT_LLM_BASE_URL — override the API endpoint (e.g. http://localhost:11434/v1)
        SOULPRINT_LLM_MODEL    — override the model (e.g. gemma4, gemma4:26b). Defaults to gpt-4o-mini.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._base_url = os.environ.get("SOULPRINT_LLM_BASE_URL", "").strip() or None
        self._model = os.environ.get("SOULPRINT_LLM_MODEL", "").strip() or "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        if self._base_url:
            return f"openai-compat/{self._model}"
        return f"openai/{self._model}"

    def summarize(
        self,
        messages: list[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        import openai

        client = openai.OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
        transcript = "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')}" for m in messages
        )
        response = client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise summarizer. Given a conversation transcript, "
                        "produce a clear summary preserving key topics, decisions, and "
                        "action items. Be factual and brief."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
        )
        return response.choices[0].message.content

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        import openai

        client = openai.OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
        response = client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content


def provider_from_config() -> LLMProvider | None:
    """Read SOULPRINT_LLM_PROVIDER and SOULPRINT_LLM_API_KEY env vars.

    Returns a provider instance or None when not configured.
    """
    provider_name = os.environ.get("SOULPRINT_LLM_PROVIDER", "").strip().lower()
    if not provider_name:
        return None

    if provider_name == "stub":
        return StubProvider()

    api_key = os.environ.get("SOULPRINT_LLM_API_KEY", "").strip()
    base_url = os.environ.get("SOULPRINT_LLM_BASE_URL", "").strip()
    if not api_key:
        # Ollama and some local servers don't need a real API key.
        # If a base_url is set, use "ollama" as a dummy key.
        if base_url and provider_name == "openai":
            api_key = "ollama"
        else:
            return None

    if base_url and not os.environ.get("SOULPRINT_LLM_MODEL", "").strip():
        import logging
        logging.getLogger(__name__).warning(
            "SOULPRINT_LLM_BASE_URL is set without SOULPRINT_LLM_MODEL — "
            "defaulting to gpt-4o-mini which may not exist on your endpoint. "
            "Set SOULPRINT_LLM_MODEL=gemma4 (or your model name)."
        )

    if provider_name == "anthropic":
        return AnthropicProvider(api_key)
    if provider_name == "openai":
        return OpenAIProvider(api_key)

    return None


def is_llm_configured() -> bool:
    """Convenience check: is any LLM provider available?"""
    return provider_from_config() is not None
