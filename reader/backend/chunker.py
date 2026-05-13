"""Text chunker for the Reader backend.

Splits input text into TTS-friendly chunks: headings, paragraphs, code blocks,
and sentence groups for paragraphs that exceed the maximum chunk size.

Pure-Python: no GPU, no Chatterbox, no FastAPI imports.
"""
from __future__ import annotations

import re
from typing import Any

# Hard maximum per chunk. Chatterbox handles long contexts unevenly past this.
_MAX_CHARS = 1600
# Soft target so we do not produce many tiny groups when sentences are short.
_TARGET_CHARS = 1000

_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, first_chunk_max: int = 400) -> list[dict[str, Any]]:
    """Split text into Reader chunks.

    Returns a list of dicts shaped:
        {"chunk_id": "c001", "index": 0, "kind": ..., "text": ...,
         "char_start": int, "char_end": int}

    Returns an empty list for empty or whitespace-only input.

    ``first_chunk_max`` caps the size of the *first* chunk only, so first audio
    reaches the user roughly 4x faster than waiting for a full-sized chunk to
    synthesize. All subsequent chunks keep the normal ~1600-char ceiling for
    fewer chunk-boundary stitches in the playback stream.
    """
    if not text or not text.strip():
        return []

    blocks = _split_blocks(text)

    chunks: list[dict[str, Any]] = []
    for block in blocks:
        if len(block["text"]) <= _MAX_CHARS:
            chunks.append(block)
        elif block["kind"] == "paragraph":
            chunks.extend(_split_long_paragraph(block))
        else:
            # Headings and code blocks larger than the hard max still need to
            # be sliced. Chatterbox cannot reliably handle oversized chunks,
            # regardless of structural kind.
            chunks.extend(_hard_slice_block(block))

    # Skip code: first-chunk shrink is for spoken-narrative latency, and
    # splitting a fenced block puts the opening ``` and closing ``` on
    # separate chunks for no audible benefit.
    if (
        chunks
        and chunks[0]["kind"] != "code"
        and first_chunk_max > 0
        and len(chunks[0]["text"]) > first_chunk_max
    ):
        head = _split_first_chunk(chunks[0], first_chunk_max)
        chunks = head + chunks[1:]

    for i, chunk in enumerate(chunks):
        chunk["index"] = i
        chunk["chunk_id"] = f"c{i + 1:03d}"

    return chunks


def _split_blocks(text: str) -> list[dict[str, Any]]:
    """Walk the text once, producing structural blocks with char offsets."""
    lines = text.split("\n")
    line_positions: list[tuple[int, str]] = []
    pos = 0
    for line in lines:
        line_positions.append((pos, line))
        pos += len(line) + 1
    end_of_text = len(text)

    blocks: list[dict[str, Any]] = []
    i = 0
    while i < len(line_positions):
        line_pos, line = line_positions[i]

        if line.startswith("```"):
            # Code fence: accumulate until matching closing fence or end of text.
            block_start = line_pos
            j = i + 1
            while j < len(line_positions):
                if line_positions[j][1].startswith("```"):
                    j += 1
                    break
                j += 1
            if j < len(line_positions):
                block_end = line_positions[j][0] - 1
            else:
                block_end = end_of_text
            block_text = text[block_start:block_end].rstrip("\n")
            blocks.append(
                {
                    "kind": "code",
                    "text": block_text,
                    "char_start": block_start,
                    "char_end": block_start + len(block_text),
                }
            )
            i = j
            continue

        if line.lstrip().startswith("#"):
            heading_text = line.rstrip()
            blocks.append(
                {
                    "kind": "heading",
                    "text": heading_text,
                    "char_start": line_pos,
                    "char_end": line_pos + len(heading_text),
                }
            )
            i += 1
            continue

        if line.strip() == "":
            i += 1
            continue

        # Paragraph: consecutive non-blank, non-heading, non-fence lines.
        para_start = line_pos
        para_lines: list[str] = []
        j = i
        while j < len(line_positions):
            _, ln = line_positions[j]
            if ln.strip() == "" or ln.lstrip().startswith("#") or ln.startswith("```"):
                break
            para_lines.append(ln)
            j += 1
        para_text = "\n".join(para_lines).rstrip()
        if para_text:
            blocks.append(
                {
                    "kind": "paragraph",
                    "text": para_text,
                    "char_start": para_start,
                    "char_end": para_start + len(para_text),
                }
            )
        i = j

    return blocks


def _split_long_paragraph(block: dict[str, Any]) -> list[dict[str, Any]]:
    """Split an overlong paragraph into sentence groups at most _MAX_CHARS long."""
    sentences = _split_sentences(block["text"])
    if not sentences:
        return [block]

    groups: list[dict[str, Any]] = []
    current: list[str] = []
    current_len = 0
    char_pos = block["char_start"]

    def flush() -> None:
        nonlocal current, current_len, char_pos
        if not current:
            return
        group_text = " ".join(current)
        groups.append(
            {
                "kind": "sentence_group",
                "text": group_text,
                "char_start": char_pos,
                "char_end": char_pos + len(group_text),
            }
        )
        char_pos += len(group_text) + 1
        current = []
        current_len = 0

    for sentence in sentences:
        s_len = len(sentence)

        if s_len > _MAX_CHARS:
            # A single sentence already exceeds the hard max. Slice it into
            # pieces of at most _MAX_CHARS, preferring word boundaries, so we
            # never hand oversized text to Chatterbox.
            flush()
            for slice_text in _hard_slice(sentence, _MAX_CHARS):
                groups.append(
                    {
                        "kind": "sentence_group",
                        "text": slice_text,
                        "char_start": char_pos,
                        "char_end": char_pos + len(slice_text),
                    }
                )
                char_pos += len(slice_text) + 1
            continue

        projected = current_len + s_len + (1 if current else 0)
        if current and projected > _MAX_CHARS:
            flush()
            projected = s_len
        current.append(sentence)
        current_len = projected

        # Soft cap: prefer flushing near the target rather than waiting for max.
        if current_len >= _TARGET_CHARS:
            flush()

    flush()
    return groups


def _split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_END_RE.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _hard_slice_block(block: dict[str, Any]) -> list[dict[str, Any]]:
    """Slice an oversized structural block (heading or code) preserving its kind."""
    pieces = _hard_slice(block["text"], _MAX_CHARS)
    out: list[dict[str, Any]] = []
    char_pos = block["char_start"]
    for piece in pieces:
        out.append(
            {
                "kind": block["kind"],
                "text": piece,
                "char_start": char_pos,
                "char_end": char_pos + len(piece),
            }
        )
        char_pos += len(piece) + 1
    return out


def _split_first_chunk(chunk: dict[str, Any], target_max: int) -> list[dict[str, Any]]:
    """Emit a small starter chunk plus the remainder as a normally-chunked tail.

    The starter is cut at the last sentence boundary within ``target_max``
    when possible, then at the last word boundary, then at a hard cut. The
    remainder is kept as a single chunk when it fits ``_MAX_CHARS`` so a
    1500-char first paragraph becomes [starter, rest] — not three or four
    small slices. When the remainder exceeds ``_MAX_CHARS`` it flows through
    the same long-paragraph / hard-slice path the initial pass would use.

    Offsets are computed against the original chunk's text rather than
    approximated by joined-piece lengths, so separators wider than one
    character (double space, indented newline) don't drift the indices.
    """
    text = chunk["text"]
    base = chunk["char_start"]
    kind = chunk["kind"]

    cut = _find_head_cut(text, target_max)

    head_raw = text[:cut]
    head_lead = len(head_raw) - len(head_raw.lstrip())
    head_trail = len(head_raw) - len(head_raw.rstrip())
    head = {
        "kind": kind,
        "text": head_raw.strip(),
        "char_start": base + head_lead,
        "char_end": base + cut - head_trail,
    }

    rest_raw = text[cut:]
    rest_text = rest_raw.strip()
    if not rest_text:
        return [head]

    rest_lead = len(rest_raw) - len(rest_raw.lstrip())
    rest_trail = len(rest_raw) - len(rest_raw.rstrip())
    rest = {
        "kind": kind,
        "text": rest_text,
        "char_start": base + cut + rest_lead,
        "char_end": base + len(text) - rest_trail,
    }

    if len(rest_text) <= _MAX_CHARS:
        return [head, rest]
    if kind == "paragraph":
        return [head] + _split_long_paragraph(rest)
    return [head] + _hard_slice_block(rest)


def _find_head_cut(text: str, target_max: int) -> int:
    """Return an index ``n`` such that ``text[:n]`` is the starter piece.

    Prefers the largest sentence boundary at or under ``target_max``, then
    the last word boundary within ``target_max``, then a hard cut.
    """
    if len(text) <= target_max:
        return len(text)

    last_sentence_end = 0
    for m in _SENTENCE_END_RE.finditer(text):
        if m.end() > target_max:
            break
        last_sentence_end = m.end()
    if last_sentence_end > 0:
        return last_sentence_end

    space = text.rfind(" ", 0, target_max)
    if space > 0:
        return space + 1

    return target_max


def _hard_slice(text: str, max_chars: int) -> list[str]:
    """Slice text into pieces of at most ``max_chars``.

    Prefers slicing at the last whitespace within the window so we don't cut
    mid-word, but falls back to a hard cut when there is no whitespace (or it
    is too far back to be useful).
    """
    pieces: list[str] = []
    pos = 0
    n = len(text)
    while pos < n:
        end = min(pos + max_chars, n)
        if end < n:
            space = text.rfind(" ", pos, end)
            if space > pos:
                end = space
        piece = text[pos:end].strip()
        if piece:
            pieces.append(piece)
        pos = end
        while pos < n and text[pos] == " ":
            pos += 1
    return pieces
