"""Tests for suggest_threads() — conversation grouping by title overlap."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.intelligence.threads import (
    SuggestedThread,
    _date_range_str,
    _derive_label,
    _significant_words,
    suggest_threads,
)


# ---------------------------------------------------------------------------
# Minimal conversation stub
# ---------------------------------------------------------------------------


@dataclass
class FakeConversation:
    id: int
    title: str
    source: str = "chatgpt"
    created_at_unix: float | None = None
    updated_at_unix: float | None = None
    messages: list = field(default_factory=list)


@dataclass
class FakeMessage:
    role: str = "user"
    content: str = "hello"
    sequence_index: int = 0


# ---------------------------------------------------------------------------
# Tests: empty input
# ---------------------------------------------------------------------------


def test_empty_input_returns_empty():
    assert suggest_threads([]) == []


def test_none_titles_handled():
    convs = [FakeConversation(id=1, title=None)]
    assert suggest_threads(convs) == []


# ---------------------------------------------------------------------------
# Tests: single conversation doesn't form a thread
# ---------------------------------------------------------------------------


def test_single_conversation_no_thread():
    convs = [FakeConversation(id=1, title="SoulPrint architecture review")]
    assert suggest_threads(convs) == []


def test_two_unrelated_no_thread():
    convs = [
        FakeConversation(id=1, title="Cooking pasta recipe"),
        FakeConversation(id=2, title="Python decorator patterns"),
    ]
    assert suggest_threads(convs) == []


# ---------------------------------------------------------------------------
# Tests: conversations with 2+ shared title words get grouped
# ---------------------------------------------------------------------------


def test_two_shared_words_grouped():
    convs = [
        FakeConversation(id=1, title="SoulPrint architecture review"),
        FakeConversation(id=2, title="SoulPrint architecture decisions"),
        FakeConversation(id=3, title="Cooking pasta recipe"),
    ]
    threads = suggest_threads(convs)
    assert len(threads) == 1
    assert len(threads[0].conversations) == 2
    thread_ids = {c.id for c in threads[0].conversations}
    assert thread_ids == {1, 2}


def test_three_conversations_same_topic():
    convs = [
        FakeConversation(id=1, title="SoulPrint strategic direction"),
        FakeConversation(id=2, title="SoulPrint execution plan"),
        FakeConversation(id=3, title="SoulPrint social media promotion"),
    ]
    threads = suggest_threads(convs)
    # "soulprint" is shared by all three, but only 1 word overlap between
    # pairs — needs temporal proximity or 2+ words. Since only "soulprint"
    # is shared (1 word), these won't cluster unless within 48h.
    # With no timestamps, they won't cluster.
    assert len(threads) == 0


def test_three_conversations_two_shared_words():
    convs = [
        FakeConversation(id=1, title="SoulPrint design system update"),
        FakeConversation(id=2, title="SoulPrint design token review"),
        FakeConversation(id=3, title="SoulPrint design visual direction"),
    ]
    threads = suggest_threads(convs)
    assert len(threads) == 1
    assert len(threads[0].conversations) == 3


# ---------------------------------------------------------------------------
# Tests: temporal proximity with 1 shared word
# ---------------------------------------------------------------------------


def test_temporal_proximity_clusters():
    """Conversations within 48h sharing 1 title word get grouped."""
    base_ts = 1711500000.0  # arbitrary
    convs = [
        FakeConversation(id=1, title="SoulPrint strategic direction", created_at_unix=base_ts),
        FakeConversation(id=2, title="SoulPrint execution plan", created_at_unix=base_ts + 3600),
    ]
    threads = suggest_threads(convs)
    assert len(threads) == 1
    assert len(threads[0].conversations) == 2


def test_temporal_proximity_too_far_no_cluster():
    """Conversations >48h apart with only 1 shared word don't cluster."""
    base_ts = 1711500000.0
    convs = [
        FakeConversation(id=1, title="SoulPrint strategic direction", created_at_unix=base_ts),
        FakeConversation(id=2, title="SoulPrint execution plan", created_at_unix=base_ts + 200_000),
    ]
    threads = suggest_threads(convs)
    assert len(threads) == 0


# ---------------------------------------------------------------------------
# Tests: thread label derived from common words
# ---------------------------------------------------------------------------


def test_label_derived_from_common_words():
    convs = [
        FakeConversation(id=1, title="SoulPrint architecture review"),
        FakeConversation(id=2, title="SoulPrint architecture decisions"),
    ]
    threads = suggest_threads(convs)
    label = threads[0].label.lower()
    assert "soulprint" in label
    assert "architecture" in label


def test_label_capitalized():
    convs = [
        FakeConversation(id=1, title="flask routing patterns"),
        FakeConversation(id=2, title="flask routing middleware"),
    ]
    threads = suggest_threads(convs)
    assert threads[0].label[0].isupper()


# ---------------------------------------------------------------------------
# Tests: date_range computed correctly
# ---------------------------------------------------------------------------


def test_date_range_same_date():
    result = _date_range_str([1711500000.0, 1711500000.0])
    assert result  # Non-empty
    assert "—" not in result  # Same date, no range


def test_date_range_different_dates():
    # Jan 1 2026 and Mar 27 2026
    ts1 = 1767225600.0  # 2026-01-01 UTC
    ts2 = 1774828800.0  # 2026-03-26 UTC (approx)
    result = _date_range_str([ts1, ts2])
    assert "—" in result


def test_date_range_empty():
    assert _date_range_str([]) == ""
    assert _date_range_str([None, None]) == ""


# ---------------------------------------------------------------------------
# Tests: total_messages counted
# ---------------------------------------------------------------------------


def test_total_messages_counted():
    convs = [
        FakeConversation(
            id=1,
            title="SoulPrint design system",
            messages=[FakeMessage(), FakeMessage(), FakeMessage()],
        ),
        FakeConversation(
            id=2,
            title="SoulPrint design tokens",
            messages=[FakeMessage(), FakeMessage()],
        ),
    ]
    threads = suggest_threads(convs)
    assert len(threads) == 1
    assert threads[0].total_messages == 5


# ---------------------------------------------------------------------------
# Tests: max_threads limit
# ---------------------------------------------------------------------------


def test_max_threads_respected():
    # Create enough distinct clusters
    convs = []
    for i in range(10):
        convs.append(FakeConversation(id=i * 2, title=f"topic{i} design review"))
        convs.append(FakeConversation(id=i * 2 + 1, title=f"topic{i} design decisions"))
    threads = suggest_threads(convs, max_threads=3)
    assert len(threads) <= 3


# ---------------------------------------------------------------------------
# Tests: significant words extraction
# ---------------------------------------------------------------------------


def test_stopwords_excluded():
    words = _significant_words("The quick brown fox and the lazy dog")
    assert "the" not in words
    assert "and" not in words
    assert "quick" in words
    assert "brown" in words


def test_short_words_excluded():
    words = _significant_words("I a x")
    # Single-char words excluded (min length 2)
    assert len(words) == 0


def test_punctuation_stripped():
    words = _significant_words("SoulPrint's architecture: review!")
    assert "soulprint" in words or "soulprints" in words
    assert "architecture" in words
    assert "review" in words
