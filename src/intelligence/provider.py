"""LLM provider protocol and implementations for derived intelligence."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for any LLM backend that can summarize messages."""

    def summarize(self, messages: list[dict]) -> str: ...

    @property
    def provider_name(self) -> str: ...


class StubProvider:
    """Returns canned summary text — no API key needed."""

    @property
    def provider_name(self) -> str:
        return "stub"

    def summarize(self, messages: list[dict]) -> str:
        msg_count = len(messages)
        roles = {m.get("role", "unknown") for m in messages}
        return (
            f"[Stub summary] This conversation contains {msg_count} messages "
            f"across roles: {', '.join(sorted(roles))}. "
            "Key topics and decisions would be extracted by a real LLM provider."
        )


class AnthropicProvider:
    """Uses the anthropic SDK to call Claude for summarization."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def summarize(self, messages: list[dict]) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        transcript = "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')}" for m in messages
        )
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=(
                "You are a concise summarizer. Given a conversation transcript, "
                "produce a clear summary preserving key topics, decisions, and "
                "action items. Be factual and brief."
            ),
            messages=[{"role": "user", "content": transcript}],
        )
        return response.content[0].text


class OpenAIProvider:
    """Uses the openai SDK to call GPT for summarization."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "openai"

    def summarize(self, messages: list[dict]) -> str:
        import openai

        client = openai.OpenAI(api_key=self._api_key)
        transcript = "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')}" for m in messages
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
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
    if not api_key:
        return None

    if provider_name == "anthropic":
        return AnthropicProvider(api_key)
    if provider_name == "openai":
        return OpenAIProvider(api_key)

    return None


def is_llm_configured() -> bool:
    """Convenience check: is any LLM provider available?"""
    return provider_from_config() is not None
