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


def chunk_text(text: str) -> list[dict[str, Any]]:
    """Split text into Reader chunks.

    Returns a list of dicts shaped:
        {"chunk_id": "c001", "index": 0, "kind": ..., "text": ...,
         "char_start": int, "char_end": int}

    Returns an empty list for empty or whitespace-only input.
    """
    if not text or not text.strip():
        return []

    blocks = _split_blocks(text)

    chunks: list[dict[str, Any]] = []
    for block in blocks:
        if block["kind"] in ("heading", "code"):
            chunks.append(block)
        else:
            if len(block["text"]) <= _MAX_CHARS:
                chunks.append(block)
            else:
                chunks.extend(_split_long_paragraph(block))

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
            # A single sentence already exceeds max: emit alone.
            flush()
            groups.append(
                {
                    "kind": "sentence_group",
                    "text": sentence,
                    "char_start": char_pos,
                    "char_end": char_pos + s_len,
                }
            )
            char_pos += s_len + 1
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
