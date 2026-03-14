"""Tests for intelligence LLM provider protocol and factory."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.intelligence.provider import (
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
