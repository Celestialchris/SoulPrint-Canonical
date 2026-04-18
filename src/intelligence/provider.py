"""LLM provider protocol and implementations for derived intelligence."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for any LLM backend that can summarize messages."""

    def summarize(self, messages: list[dict]) -> str: ...

    def complete(self, system_prompt: str, user_message: str) -> str: ...

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

    def complete(self, system_prompt: str, user_message: str) -> str:
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

    def summarize(self, messages: list[dict]) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        transcript = "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')}" for m in messages
        )
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=(
                "You are summarizing one AI chat conversation for a personal archive. "
                "The user will re-read this summary months or years later to remember what happened. "
                "Shallow summaries fail that job.\n\n"
                "Your output must include, in prose or labeled sections:\n"
                "1. Starting point. What did the user bring to this conversation? "
                "What problem, question, or context?\n"
                "2. Specific questions asked. Quote or closely paraphrase the actual questions, "
                "not categories of questions. 'User asked about X' is too vague; "
                "'User asked whether X should use Y or Z given constraint W' is specific.\n"
                "3. Decisions reached. What was decided, and why? Include reasoning, not just outcome.\n"
                "4. Concrete artifacts. Name specific files, commands, URLs, library names, "
                "code snippets, people, or places that came up. Preserve them.\n"
                "5. Unresolved threads. What questions were raised but not answered? "
                "What was deferred or explicitly left open?\n"
                "6. Notable moments. One or two places where the conversation surprised, "
                "pivoted, or crystallized. A disagreement, a 'wait, actually,' a moment of insight.\n\n"
                "Write at minimum 400 words. For long or complex conversations, write more. "
                "Do not pad for length. Fill the space with specificity. "
                "Short conversations (fewer than 20 messages) may need less. Trust the material.\n\n"
                "Start directly with the substance. No preamble like 'in this conversation' "
                "or 'the user and assistant discussed.'"
            ),
            messages=[{"role": "user", "content": transcript}],
        )
        return response.content[0].text

    def complete(self, system_prompt: str, user_message: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
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

    def summarize(self, messages: list[dict]) -> str:
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
            max_tokens=4096,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are summarizing one AI chat conversation for a personal archive. "
                        "The user will re-read this summary months or years later to remember what happened. "
                        "Shallow summaries fail that job.\n\n"
                        "Your output must include, in prose or labeled sections:\n"
                        "1. Starting point. What did the user bring to this conversation? "
                        "What problem, question, or context?\n"
                        "2. Specific questions asked. Quote or closely paraphrase the actual questions, "
                        "not categories of questions. 'User asked about X' is too vague; "
                        "'User asked whether X should use Y or Z given constraint W' is specific.\n"
                        "3. Decisions reached. What was decided, and why? Include reasoning, not just outcome.\n"
                        "4. Concrete artifacts. Name specific files, commands, URLs, library names, "
                        "code snippets, people, or places that came up. Preserve them.\n"
                        "5. Unresolved threads. What questions were raised but not answered? "
                        "What was deferred or explicitly left open?\n"
                        "6. Notable moments. One or two places where the conversation surprised, "
                        "pivoted, or crystallized. A disagreement, a 'wait, actually,' a moment of insight.\n\n"
                        "Write at minimum 400 words. For long or complex conversations, write more. "
                        "Do not pad for length. Fill the space with specificity. "
                        "Short conversations (fewer than 20 messages) may need less. Trust the material.\n\n"
                        "Start directly with the substance. No preamble like 'in this conversation' "
                        "or 'the user and assistant discussed.'"
                    ),
                },
                {"role": "user", "content": transcript},
            ],
        )
        return response.choices[0].message.content

    def complete(self, system_prompt: str, user_message: str) -> str:
        import openai

        client = openai.OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
        response = client.chat.completions.create(
            model=self._model,
            max_tokens=4096,
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
