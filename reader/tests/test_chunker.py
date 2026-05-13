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


def test_oversized_code_block_is_sliced():
    """Regression: a fenced code block longer than the hard max must be sliced.
    Structural blocks were previously bypassing the size check entirely."""
    body = "print('x')\n" * 200  # ~2200 chars of code
    text = "```python\n" + body + "```"
    chunks = chunk_text(text)
    assert all(len(c["text"]) <= 1600 for c in chunks), \
        f"oversized code block leaked: {max(len(c['text']) for c in chunks)} chars"
    # At least one of the resulting chunks must still be a code chunk.
    assert any(c["kind"] == "code" for c in chunks)


def test_oversized_heading_is_sliced():
    """Regression: an absurdly long heading line must not bypass the hard max."""
    text = "# " + ("Word " * 400)  # ~2000-char heading line
    chunks = chunk_text(text)
    assert all(len(c["text"]) <= 1600 for c in chunks)


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


def test_first_chunk_max_does_not_split_code_block():
    """First-chunk shrink is for spoken-narrative latency. A fenced code block
    at the head of the document, even if longer than first_chunk_max, must
    remain a single code chunk so the opening and closing fences stay together.
    """
    text = "```python\n" + ("print('hello')\n" * 80) + "```"
    # Sanity: this block stays under the hard max, so without the kind guard
    # it would otherwise be split by the first_chunk_max=400 logic.
    assert len(text) < 1600
    chunks = chunk_text(text, first_chunk_max=400)
    assert len(chunks) == 1
    assert chunks[0]["kind"] == "code"
    assert "```python" in chunks[0]["text"]
    assert chunks[0]["text"].rstrip().endswith("```")


def test_first_chunk_shrink_emits_two_chunks_for_long_first_paragraph():
    """A first paragraph longer than first_chunk_max but inside _MAX_CHARS
    must split into exactly two chunks: a small starter and the remainder
    as one normal chunk. Previously the optimization emitted N starter-sized
    chunks across the whole paragraph; only the first chunk needs to be
    small for fast time-to-first-audio."""
    sentence = "This is a moderately long sentence with several words. "  # 55 chars
    text = (sentence * 25).rstrip()
    # Sanity: between 1200 and 1500, inside _MAX_CHARS so the chunker would
    # normally produce ONE paragraph chunk.
    assert 1200 <= len(text) <= 1500
    assert len(chunk_text(text, first_chunk_max=10_000)) == 1

    chunks = chunk_text(text, first_chunk_max=400)
    assert len(chunks) == 2
    assert len(chunks[0]["text"]) <= 400
    # Remainder is kept whole, not further sliced into 400-char pieces.
    assert len(chunks[1]["text"]) > 400


def test_first_chunk_offsets_preserved_with_double_space_separators():
    """When source sentences are separated by double spaces, head['char_end']
    must point at the real position in the ORIGINAL text where the starter
    ends — not at a position computed from a single-space-joined piece
    length. The character just before char_end should be a sentence
    terminator, not a mid-word letter."""
    sentence = "A short sentence here."  # 22 chars
    text = "  ".join([sentence] * 25)  # double-space separator, ~598 chars

    chunks = chunk_text(text, first_chunk_max=400)
    head = chunks[0]

    # The exact char at char_end - 1 must be a real sentence terminator in
    # the original text; under the old approximation it landed mid-word.
    assert text[head["char_end"] - 1] in ".!?", (
        f"char_end landed at offset {head['char_end']}; "
        f"surrounding original text: "
        f"{text[max(0, head['char_end'] - 8):head['char_end'] + 4]!r}"
    )
    # And the original span between char_start and char_end should match
    # the head's stored text exactly (no approximation drift).
    assert text[head["char_start"]:head["char_end"]] == head["text"]


def test_first_chunk_offsets_preserved_with_newline_separators():
    """Paragraphs that span multiple input lines (joined with '\\n' by the
    block walker) must still produce truthful offsets — a newline counts
    as one separator char, but if the original source had indented
    continuations, the head's char_end shouldn't drift either."""
    line = "A sentence that ends with a period."  # 35 chars
    text = "\n".join([line] * 15)  # 15 lines, ~539 chars

    chunks = chunk_text(text, first_chunk_max=400)
    head = chunks[0]

    assert text[head["char_end"] - 1] == "."
    assert text[head["char_start"]:head["char_end"]] == head["text"]
