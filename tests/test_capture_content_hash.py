"""Tests for the capture content hash recipe v1 and serialization helpers."""

from __future__ import annotations

import unicodedata
import unittest

from src.capture.content_hash import (
    CONTENT_HASH_RECIPE_VERSION,
    canonical_json,
    content_hash,
    sha256_hex,
)


# Frozen recipe-v1 digest. Computed once against the fully-specified envelope
# in test_content_hash_matches_recipe_v1; a failure here means recipe v1
# changed and CONTENT_HASH_RECIPE_VERSION must be bumped to 2.
_RECIPE_V1_EXPECTED = (
    "2427d7f82310f0a91a6e7828d2717a8b3a2405e89592831f43729c289d6e5a7c"
)

# Standard FIPS 180-2 SHA-256 test vector for the ASCII string "abc".
_SHA256_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


class ContentHashRecipeTest(unittest.TestCase):
    def test_content_hash_matches_recipe_v1(self):
        # Vector: captured_at_unix=1747227615.5 truncates to minute 1747227600.
        digest = content_hash(
            "soulprint-cli",
            "paste",
            "Hello, SoulPrint.",
            "https://example.com/x",
            1747227615.5,
        )

        self.assertEqual(digest, _RECIPE_V1_EXPECTED)

    def test_content_hash_is_nfc_normalized(self):
        # Same grapheme, two encodings: precomposed e-acute (NFC) vs
        # "e" + combining acute accent U+0301 (NFD). Built via chr() so the
        # source stays pure ASCII and the inputs are provably distinct.
        base = "cafe" + chr(0x0301)
        composed = unicodedata.normalize("NFC", base)
        decomposed = unicodedata.normalize("NFD", base)
        # Guard: the two inputs really are distinct code point sequences.
        self.assertNotEqual(composed, decomposed)

        composed_hash = content_hash("a", "paste", composed, None, 1000.0)
        decomposed_hash = content_hash("a", "paste", decomposed, None, 1000.0)

        self.assertEqual(composed_hash, decomposed_hash)

    def test_content_hash_rstrips_body_text(self):
        clean = content_hash("a", "paste", "hello", None, 1000.0)
        trailing = content_hash("a", "paste", "hello   \n\t ", None, 1000.0)
        self.assertEqual(clean, trailing)

        # rstrip only: leading whitespace stays significant.
        leading = content_hash("a", "paste", "  hello", None, 1000.0)
        self.assertNotEqual(clean, leading)

    def test_content_hash_truncates_captured_at_to_minute(self):
        # Two timestamps inside the same minute hash identically.
        same_minute_a = content_hash("a", "paste", "x", None, 1747227600.0)
        same_minute_b = content_hash("a", "paste", "x", None, 1747227659.9)
        self.assertEqual(same_minute_a, same_minute_b)

        # The next minute hashes differently.
        next_minute = content_hash("a", "paste", "x", None, 1747227660.0)
        self.assertNotEqual(same_minute_a, next_minute)

    def test_content_hash_empty_source_url(self):
        none_url = content_hash("a", "paste", "x", None, 1000.0)
        empty_url = content_hash("a", "paste", "x", "", 1000.0)

        self.assertEqual(none_url, empty_url)

    def test_content_hash_recipe_version_is_one(self):
        self.assertEqual(CONTENT_HASH_RECIPE_VERSION, 1)

    def test_canonical_json_is_deterministic(self):
        # Reordering input keys does not change the serialized output.
        self.assertEqual(
            canonical_json({"b": 1, "a": 2}),
            canonical_json({"a": 2, "b": 1}),
        )
        self.assertEqual(canonical_json({"b": 1, "a": 2}), '{"a":2,"b":1}')

    def test_sha256_hex_known_vector(self):
        self.assertEqual(sha256_hex("abc"), _SHA256_ABC)
        # str and bytes inputs agree.
        self.assertEqual(sha256_hex("abc"), sha256_hex(b"abc"))


if __name__ == "__main__":
    unittest.main()
