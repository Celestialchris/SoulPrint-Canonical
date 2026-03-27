"""Thread suggestion — group related conversations by title overlap.

Heuristic approach (no LLM needed):
1. Normalize titles, extract significant words
2. Compute pairwise word overlap
3. Cluster conversations sharing 2+ significant title words
4. Also cluster conversations within 48h sharing 1+ title word
5. Return clusters of 2+ conversations, sorted by size
"""

from __future__ import annotations

import re
import string
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "that", "this", "was", "are",
    "be", "has", "had", "have", "will", "can", "do", "does", "did", "not",
    "so", "if", "my", "me", "we", "our", "you", "your", "its", "i", "about",
    "up", "out", "just", "how", "what", "when", "where", "which", "who",
    "some", "all", "no", "new", "more", "very", "into", "over", "after",
    "also", "than", "then", "been", "could", "would", "should", "there",
    "their", "them", "these", "those", "other", "one", "two", "first",
    "chat", "conversation", "untitled",
})


@dataclass
class SuggestedThread:
    """A cluster of related conversations."""

    label: str
    conversations: list  # list of conversation-like objects
    date_range: str
    total_messages: int


def _significant_words(title: str) -> set[str]:
    """Extract significant words from a conversation title."""
    title = title.lower()
    title = re.sub(f"[{re.escape(string.punctuation)}]", " ", title)
    words = title.split()
    return {w for w in words if len(w) >= 2 and w not in STOPWORDS}


def _format_date(ts: float | None) -> str:
    """Format a unix timestamp as 'Mar 27, 2026'."""
    if ts is None:
        return ""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%b %d, %Y").replace(" 0", " ")


def _date_range_str(timestamps: list[float | None]) -> str:
    """Build a date range string from a list of unix timestamps."""
    valid = sorted(t for t in timestamps if t is not None)
    if not valid:
        return ""
    start = _format_date(valid[0])
    end = _format_date(valid[-1])
    if start == end:
        return start
    # Strip year from start if same year
    start_dt = datetime.fromtimestamp(valid[0], tz=timezone.utc)
    end_dt = datetime.fromtimestamp(valid[-1], tz=timezone.utc)
    if start_dt.year == end_dt.year:
        start_short = start_dt.strftime("%b %d").replace(" 0", " ")
        return f"{start_short} — {end}"
    return f"{start} — {end}"


def _derive_label(word_counts: dict[str, int], max_words: int = 3) -> str:
    """Derive a thread label from the most common shared words."""
    if not word_counts:
        return "Related conversations"
    ranked = sorted(word_counts.items(), key=lambda x: (-x[1], x[0]))
    words = [w for w, _ in ranked[:max_words]]
    label = " ".join(words)
    return label[0].upper() + label[1:] if label else "Related conversations"


def suggest_threads(
    conversations: list,
    max_threads: int = 5,
    min_cluster_size: int = 2,
) -> list[SuggestedThread]:
    """Group conversations that likely belong to the same topic.

    Parameters
    ----------
    conversations:
        Objects with ``.id``, ``.title``, ``.source``,
        ``.created_at_unix`` (or ``None``), and ``.messages``.
    max_threads:
        Maximum number of thread suggestions to return.
    min_cluster_size:
        Minimum conversations to form a thread (default 2).

    Returns clusters sorted by size descending.
    """
    if not conversations:
        return []

    # Build word sets per conversation
    conv_words: dict[int, set[str]] = {}
    conv_by_id: dict[int, object] = {}
    for conv in conversations:
        cid = conv.id
        conv_by_id[cid] = conv
        conv_words[cid] = _significant_words(conv.title or "")

    # Union-Find for clustering
    parent: dict[int, int] = {cid: cid for cid in conv_by_id}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    ids = list(conv_by_id.keys())

    # Cluster by word overlap
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            words_a, words_b = conv_words[a], conv_words[b]
            shared = words_a & words_b

            if len(shared) >= 2:
                union(a, b)
            elif len(shared) >= 1:
                # Also cluster if within 48 hours
                ts_a = getattr(conv_by_id[a], "created_at_unix", None)
                ts_b = getattr(conv_by_id[b], "created_at_unix", None)
                if ts_a is not None and ts_b is not None:
                    if abs(ts_a - ts_b) <= 48 * 3600:
                        union(a, b)

    # Collect clusters
    clusters: dict[int, list[int]] = defaultdict(list)
    for cid in ids:
        clusters[find(cid)].append(cid)

    # Build thread objects for clusters meeting minimum size
    threads: list[SuggestedThread] = []
    for member_ids in clusters.values():
        if len(member_ids) < min_cluster_size:
            continue

        convs = [conv_by_id[cid] for cid in member_ids]

        # Count shared words across the cluster for label
        word_counts: dict[str, int] = defaultdict(int)
        for cid in member_ids:
            for w in conv_words[cid]:
                word_counts[w] += 1
        # Keep only words appearing in 2+ conversations
        shared_counts = {w: c for w, c in word_counts.items() if c >= 2}

        timestamps = [
            getattr(c, "created_at_unix", None) or getattr(c, "updated_at_unix", None)
            for c in convs
        ]

        total_msgs = sum(len(c.messages) for c in convs)

        # Sort conversations by date (newest first)
        convs.sort(
            key=lambda c: getattr(c, "created_at_unix", None) or 0,
            reverse=True,
        )

        threads.append(SuggestedThread(
            label=_derive_label(shared_counts),
            conversations=convs,
            date_range=_date_range_str(timestamps),
            total_messages=total_msgs,
        ))

    # Sort by cluster size descending, then by label
    threads.sort(key=lambda t: (-len(t.conversations), t.label))
    return threads[:max_threads]
