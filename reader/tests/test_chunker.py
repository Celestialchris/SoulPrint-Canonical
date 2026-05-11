"""Tests for reader.backend.chunker.

Pure-Python tests: no GPU, no Chatterbox, no FastAPI required.
"""
from __future__ import annotations

import pytest

from reader.backend.chunker import chunk_text


def test_empty_text():
    assert chunk_text("") == []


def test_whitespace_only_text():
    assert chunk_text("   \n\n   \t  ") == []


def test_single_paragraph():
    text = "This is a single paragraph of moderate length."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0]["text"].strip() == text


def test_heading_split():
    text = "# First Heading\n\nSome content.\n\n# Second Heading\n\nMore content."
    chunks = chunk_text(text)
    # Should produce at least one heading chunk and content chunks
    kinds = [c["kind"] for c in chunks]
    assert "heading" in kinds
    # Two headings present
    headings = [c for c in chunks if c["kind"] == "heading"]
    assert len(headings) == 2
    assert "First Heading" in headings[0]["text"]
    assert "Second Heading" in headings[1]["text"]


def test_paragraph_split():
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
    chunks = chunk_text(text)
    # Each paragraph becomes its own chunk
    assert len(chunks) == 3
    assert all(c["kind"] == "paragraph" for c in chunks)
    assert "First" in chunks[0]["text"]
    assert "Second" in chunks[1]["text"]
    assert "Third" in chunks[2]["text"]


def test_long_paragraph_sentence_fallback():
    # Build a single paragraph longer than 1600 chars from many sentences.
    sentence = "This is a sentence with a reasonable amount of words in it. "
    long_para = sentence * 40  # ~2400 chars, no double newlines
    chunks = chunk_text(long_para)
    # Should split into multiple sentence-group chunks
    assert len(chunks) > 1
    assert all(c["kind"] == "sentence_group" for c in chunks)
    # No chunk should exceed the hard maximum of 1600 chars
    assert all(len(c["text"]) <= 1600 for c in chunks)


def test_code_block_preserved():
    text = (
        "Here is some intro.\n\n"
        "```python\n"
        "def hello():\n"
        "    return 'world'\n"
        "```\n\n"
        "And some outro."
    )
    chunks = chunk_text(text)
    code_chunks = [c for c in chunks if c["kind"] == "code"]
    assert len(code_chunks) == 1
    assert "def hello()" in code_chunks[0]["text"]
    assert "```" in code_chunks[0]["text"]


def test_chunk_metadata_shape():
    chunks = chunk_text("# Heading\n\nA paragraph of text.")
    for c in chunks:
        assert set(c.keys()) >= {"chunk_id", "index", "kind", "text", "char_start", "char_end"}
        assert isinstance(c["chunk_id"], str)
        assert isinstance(c["index"], int)
        assert isinstance(c["kind"], str)
        assert isinstance(c["text"], str)
        assert isinstance(c["char_start"], int)
        assert isinstance(c["char_end"], int)
        assert c["char_end"] >= c["char_start"]


def test_chunk_ids_sequential():
    text = "Para one.\n\nPara two.\n\nPara three."
    chunks = chunk_text(text)
    ids = [c["chunk_id"] for c in chunks]
    assert ids == ["c001", "c002", "c003"]
    indexes = [c["index"] for c in chunks]
    assert indexes == [0, 1, 2]


def test_single_oversized_sentence_is_hard_sliced():
    """Regression: a single sentence/unpunctuated run longer than the hard max
    must be sliced, not emitted whole. The Reader contract is that no chunk
    ever exceeds _MAX_CHARS (1600 chars) so Chatterbox never sees oversized text.
    """
    text = "a" * 1700
    chunks = chunk_text(text)
    assert len(chunks) >= 2
    assert all(len(c["text"]) <= 1600 for c in chunks)
    assert all(c["kind"] == "sentence_group" for c in chunks)


def test_oversized_sentence_with_spaces_prefers_word_boundaries():
    """When the oversized text has whitespace, slicing should prefer word
    boundaries so the seam is not in the middle of a word."""
    word = "blockchain "  # 11 chars including trailing space
    text = word * 200  # ~2200 chars, well over the hard max
    chunks = chunk_text(text)
    assert all(len(c["text"]) <= 1600 for c in chunks)
    # No chunk should end mid-word.
    for c in chunks:
        last_token = c["text"].rsplit(" ", 1)[-1].strip()
        assert last_token == "blockchain", f"slice ended mid-word: {last_token!r}"


def test_chunk_kind_values_are_documented():
    """All chunk kinds returned must be one of the documented enum values."""
    text = (
        "# Heading\n\n"
        "A paragraph.\n\n"
        "```\ncode\n```\n\n"
        + ("Sentence. " * 200)
    )
    chunks = chunk_text(text)
    allowed = {"heading", "paragraph", "code", "sentence_group"}
    for c in chunks:
        assert c["kind"] in allowed, f"Unknown kind: {c['kind']}"
