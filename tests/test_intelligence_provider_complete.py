"""Tests for LLMProvider.complete() — verifies system_prompt is passed through
without re-wrapping or flattening."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from src.intelligence.provider import AnthropicProvider, OpenAIProvider, StubProvider


SYSTEM = "You are a distillation engine."
USER = "Distill the following 3 conversations into a handoff document.\n\nConv 1..."


class StubProviderCompleteTest(unittest.TestCase):
    def test_returns_non_empty_string(self):
        provider = StubProvider()
        result = provider.complete(SYSTEM, USER)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_callable_without_error(self):
        provider = StubProvider()
        # Should not raise
        provider.complete(SYSTEM, USER)

    def test_does_not_flatten_messages(self):
        provider = StubProvider()
        result = provider.complete(SYSTEM, USER)
        # Result should NOT contain the "[user]:" prefix that summarize() produces
        self.assertNotIn("[user]:", result)


class OpenAIProviderCompleteTest(unittest.TestCase):
    def _make_mock_response(self, text: str = "distilled output") -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = text
        return mock_resp

    def _make_provider(self) -> OpenAIProvider:
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        with patch.dict(os.environ, env, clear=True):
            return OpenAIProvider(api_key="sk-test")

    def test_system_prompt_passed_as_system_role(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.complete(SYSTEM, USER)

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], SYSTEM)

    def test_user_message_passed_raw_as_user_role(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.complete(SYSTEM, USER)

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], USER)

    def test_exactly_two_messages_sent(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.complete(SYSTEM, USER)

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(len(messages), 2)

    def test_does_not_flatten_user_message(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.complete(SYSTEM, USER)

        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        # user content should be exactly USER, not "[user]: " + USER
        self.assertEqual(messages[1]["content"], USER)
        self.assertFalse(messages[1]["content"].startswith("[user]:"))

    def test_uses_max_tokens_4096(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.complete(SYSTEM, USER)

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 4096)

    def test_accepts_explicit_max_tokens(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.complete(SYSTEM, USER, max_tokens=16384)

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 16384)


class AnthropicProviderCompleteTest(unittest.TestCase):
    """Anthropic is a lazy import inside complete(); patch via sys.modules."""

    def _make_context(self, text: str = "distilled output"):
        """Return (fake_anthropic_module, mock_client, mock_response)."""
        import sys

        mock_resp = MagicMock()
        mock_resp.content[0].text = text
        fake_anthropic = MagicMock()
        mock_client = fake_anthropic.Anthropic.return_value
        mock_client.messages.create.return_value = mock_resp
        return fake_anthropic, mock_client, mock_resp

    def test_system_prompt_passed_via_system_kwarg(self):
        import sys

        fake_anthropic, mock_client, _ = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.complete(SYSTEM, USER)

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["system"], SYSTEM)

    def test_exactly_one_message_sent(self):
        import sys

        fake_anthropic, mock_client, _ = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.complete(SYSTEM, USER)

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(len(kwargs["messages"]), 1)

    def test_user_message_raw_content(self):
        import sys

        fake_anthropic, mock_client, _ = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.complete(SYSTEM, USER)

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertEqual(kwargs["messages"][0]["content"], USER)

    def test_does_not_flatten_user_message(self):
        import sys

        fake_anthropic, mock_client, _ = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.complete(SYSTEM, USER)

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertFalse(kwargs["messages"][0]["content"].startswith("[user]:"))

    def test_uses_max_tokens_4096(self):
        import sys

        fake_anthropic, mock_client, _ = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.complete(SYSTEM, USER)

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 4096)

    def test_accepts_explicit_max_tokens(self):
        import sys

        fake_anthropic, mock_client, _ = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.complete(SYSTEM, USER, max_tokens=16384)

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 16384)


if __name__ == "__main__":
    unittest.main()
