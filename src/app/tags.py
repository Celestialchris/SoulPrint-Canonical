"""Tag normalization and auto-tag extraction for imported conversations.

Per docs/specs/tagging-spec.md v2. Comma-string storage on
ImportedConversation.tags; normalized on every write path through
normalize_tag_string.
"""

from __future__ import annotations

STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "my", "your", "how", "do", "can", "what", "why",
    "when", "where", "is", "are", "i", "you", "we", "us", "to", "for",
    "of", "and", "or", "but", "in", "on", "at", "with", "this", "that",
    "these", "those", "it",
})


def normalize_tag_string(raw: str) -> str:
    """Normalize one tag or a comma-separated list to the canonical form.

    Rules (per spec Section 7):
      1. Split on commas.
      2. Strip outer whitespace, lowercase each part.
      3. Collapse internal whitespace runs to a single space.
      4. Truncate to 64 characters.
      5. Drop empty parts.
      6. Deduplicate, preserving first occurrence order.
      7. Rejoin with ', ' (comma + space).
    """
    if not raw:
        return ""
    parts = [p.strip().lower() for p in raw.split(",")]
    parts = [" ".join(p.split()) for p in parts]
    parts = [p[:64] for p in parts]
    parts = [p for p in parts if p]
    seen: set[str] = set()
    deduped: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return ", ".join(deduped)


def auto_tag_from_title(title: str) -> str:
    """Extract the first meaningful word from a conversation title.

    Per spec Section 5:
      - Split the title on whitespace.
      - Drop leading tokens matching STOPWORDS (lowercase compare).
      - Take the first remaining token, normalize, return.
      - Return empty string if title is empty or all stopwords.
    """
    if not title:
        return ""
    for word in title.strip().split():
        if word.lower() not in STOPWORDS:
            return normalize_tag_string(word)
    return ""
