"""Tests for intelligence LLM provider protocol and factory."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from src.intelligence.provider import (
    AnthropicProvider,
    OpenAIProvider,
    StubProvider,
    is_llm_configured,
    provider_from_config,
)


class StubProviderTest(unittest.TestCase):
    def test_stub_returns_non_empty_string(self):
        provider = StubProvider()
        result = provider.summarize([{"role": "user", "content": "hello"}])

        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_stub_provider_name(self):
        provider = StubProvider()
        self.assertEqual(provider.provider_name, "stub")


class ProviderFromConfigTest(unittest.TestCase):
    def test_returns_stub_when_env_set(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            provider = provider_from_config()

        self.assertIsNotNone(provider)
        self.assertEqual(provider.provider_name, "stub")

    def test_returns_none_when_env_not_set(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        with patch.dict(os.environ, env, clear=True):
            provider = provider_from_config()

        self.assertIsNone(provider)

    def test_returns_none_when_anthropic_without_key(self):
        env_patch = {"SOULPRINT_LLM_PROVIDER": "anthropic"}
        env_remove = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env_remove.update(env_patch)
        with patch.dict(os.environ, env_remove, clear=True):
            provider = provider_from_config()

        self.assertIsNone(provider)

    def test_returns_none_when_openai_without_key(self):
        env_patch = {"SOULPRINT_LLM_PROVIDER": "openai"}
        env_remove = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env_remove.update(env_patch)
        with patch.dict(os.environ, env_remove, clear=True):
            provider = provider_from_config()

        self.assertIsNone(provider)


class OpenAIProviderEnvVarTest(unittest.TestCase):
    """Verify OpenAIProvider reads SOULPRINT_LLM_BASE_URL and SOULPRINT_LLM_MODEL."""

    def test_defaults_when_env_unset(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        with patch.dict(os.environ, env, clear=True):
            provider = OpenAIProvider(api_key="sk-test")
        self.assertIsNone(provider._base_url)
        self.assertEqual(provider._model, "gpt-4o-mini")

    def test_reads_base_url_and_model_from_env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env["SOULPRINT_LLM_BASE_URL"] = "http://localhost:11434/v1"
        env["SOULPRINT_LLM_MODEL"] = "gemma4"
        with patch.dict(os.environ, env, clear=True):
            provider = OpenAIProvider(api_key="ollama")
        self.assertEqual(provider._base_url, "http://localhost:11434/v1")
        self.assertEqual(provider._model, "gemma4")

    def test_provider_name_without_base_url(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        with patch.dict(os.environ, env, clear=True):
            provider = OpenAIProvider(api_key="sk-test")
        self.assertEqual(provider.provider_name, "openai/gpt-4o-mini")

    def test_provider_name_with_base_url(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env["SOULPRINT_LLM_BASE_URL"] = "http://localhost:11434/v1"
        env["SOULPRINT_LLM_MODEL"] = "gemma4:26b"
        with patch.dict(os.environ, env, clear=True):
            provider = OpenAIProvider(api_key="ollama")
        self.assertEqual(provider.provider_name, "openai-compat/gemma4:26b")


class OllamaFallbackTest(unittest.TestCase):
    """Provider factory fills a dummy api_key when base_url is set for Ollama."""

    def test_fills_dummy_key_for_openai_with_base_url(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env["SOULPRINT_LLM_PROVIDER"] = "openai"
        env["SOULPRINT_LLM_BASE_URL"] = "http://localhost:11434/v1"
        with patch.dict(os.environ, env, clear=True):
            provider = provider_from_config()
        self.assertIsNotNone(provider)
        self.assertEqual(provider._api_key, "ollama")

    def test_no_fallback_for_anthropic_with_base_url(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env["SOULPRINT_LLM_PROVIDER"] = "anthropic"
        env["SOULPRINT_LLM_BASE_URL"] = "http://localhost:11434/v1"
        with patch.dict(os.environ, env, clear=True):
            provider = provider_from_config()
        self.assertIsNone(provider)


class ModelMissingWarningTest(unittest.TestCase):
    """Warn when SOULPRINT_LLM_BASE_URL is set without SOULPRINT_LLM_MODEL."""

    def test_warns_when_base_url_set_without_model(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env["SOULPRINT_LLM_PROVIDER"] = "openai"
        env["SOULPRINT_LLM_BASE_URL"] = "http://localhost:11434/v1"
        with patch.dict(os.environ, env, clear=True):
            with self.assertLogs("src.intelligence.provider", level="WARNING") as captured:
                provider_from_config()
        self.assertTrue(
            any("SOULPRINT_LLM_MODEL" in msg for msg in captured.output),
            f"Expected a MODEL warning, got: {captured.output!r}",
        )

    def test_no_warning_when_model_is_set(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        env["SOULPRINT_LLM_PROVIDER"] = "openai"
        env["SOULPRINT_LLM_BASE_URL"] = "http://localhost:11434/v1"
        env["SOULPRINT_LLM_MODEL"] = "gemma4"
        with patch.dict(os.environ, env, clear=True):
            import logging
            logger = logging.getLogger("src.intelligence.provider")
            with patch.object(logger, "warning") as mock_warn:
                provider_from_config()
                mock_warn.assert_not_called()


class OpenAIProviderSummarizeMaxTokensTest(unittest.TestCase):
    """The summarize() default is 4096 and explicit overrides pass through.

    Guards against regressions where a pushed-up default would reserve too
    much output budget on non-OpenAI backends (Anthropic, Ollama/Gemma4)
    that enforce ``max_tokens + input_tokens <= context_window`` server-side.
    """

    def _make_provider(self) -> OpenAIProvider:
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        with patch.dict(os.environ, env, clear=True):
            return OpenAIProvider(api_key="sk-test")

    def _make_mock_response(self, text: str = "summary") -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = text
        return mock_resp

    def test_uses_max_tokens_4096_by_default(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.summarize([{"role": "user", "content": "hi"}])

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 4096)

    def test_accepts_explicit_max_tokens(self):
        provider = self._make_provider()
        mock_resp = self._make_mock_response()

        with patch("openai.OpenAI") as mock_cls:
            mock_client = mock_cls.return_value
            mock_client.chat.completions.create.return_value = mock_resp
            provider.summarize(
                [{"role": "user", "content": "hi"}],
                max_tokens=16384,
            )

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 16384)


class AnthropicProviderSummarizeMaxTokensTest(unittest.TestCase):
    """Anthropic summarize() honors the default and explicit overrides."""

    def _make_context(self, text: str = "summary"):
        import sys

        mock_resp = MagicMock()
        mock_resp.content[0].text = text
        fake_anthropic = MagicMock()
        mock_client = fake_anthropic.Anthropic.return_value
        mock_client.messages.create.return_value = mock_resp
        return fake_anthropic, mock_client

    def test_uses_max_tokens_4096_by_default(self):
        import sys

        fake_anthropic, mock_client = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.summarize([{"role": "user", "content": "hi"}])

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 4096)

    def test_accepts_explicit_max_tokens(self):
        import sys

        fake_anthropic, mock_client = self._make_context()
        provider = AnthropicProvider(api_key="sk-ant-test")

        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider.summarize(
                [{"role": "user", "content": "hi"}],
                max_tokens=16384,
            )

        kwargs = mock_client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["max_tokens"], 16384)


class IsLlmConfiguredTest(unittest.TestCase):
    def test_true_when_stub_configured(self):
        with patch.dict(os.environ, {"SOULPRINT_LLM_PROVIDER": "stub"}, clear=False):
            self.assertTrue(is_llm_configured())

    def test_false_when_not_configured(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SOULPRINT_LLM_")}
        with patch.dict(os.environ, env, clear=True):
            self.assertFalse(is_llm_configured())


if __name__ == "__main__":
    unittest.main()
