"""Tests for intelligence LLM provider protocol and factory."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.intelligence.provider import (
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
        env_remove = {k: v for k, v in os.environ.items() if k != "SOULPRINT_LLM_API_KEY"}
        env_remove.update(env_patch)
        with patch.dict(os.environ, env_remove, clear=True):
            provider = provider_from_config()

        self.assertIsNone(provider)

    def test_returns_none_when_openai_without_key(self):
        env_patch = {"SOULPRINT_LLM_PROVIDER": "openai"}
        env_remove = {k: v for k, v in os.environ.items() if k != "SOULPRINT_LLM_API_KEY"}
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
