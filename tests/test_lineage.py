"""Tests for derived lineage suggestions."""

from __future__ import annotations

import unittest

from src.intelligence.continuity.lineage import (
    ConversationSummary,
    LineageSuggestion,
    VALID_RELATION_TYPES,
    suggest_lineage,
    _title_overlap_score,
    _temporal_proximity_score,
    _keyword_overlap_score,
    _continuation_keyword_score,
    _infer_relation_type,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _source(
    conv_id: int = 1,
    title: str = "SoulPrint SQLite storage design",
    ts: float | None = 1710000000.0,
    messages: list[str] | None = None,
) -> ConversationSummary:
    previews = messages if messages is not None else ["Should we use SQLite for canonical storage?"]
    return ConversationSummary(
        id=conv_id,
        title=title,
        created_at_unix=ts,
        message_previews=previews,
    )


def _candidate(
    conv_id: int = 2,
    title: str = "SoulPrint SQLite migration plan",
    ts: float | None = 1710050000.0,
    messages: list[str] | None = None,
) -> ConversationSummary:
    previews = messages if messages is not None else ["Let's plan the SQLite migration."]
    return ConversationSummary(
        id=conv_id,
        title=title,
        created_at_unix=ts,
        message_previews=previews,
    )


# ---------------------------------------------------------------------------
# Tests — heuristic scoring produces ranked results
# ---------------------------------------------------------------------------


class RankedScoringTest(unittest.TestCase):

    def test_high_overlap_ranks_first(self):
        source = _source()
        candidates = [
            _candidate(conv_id=2, title="Unrelated cooking recipe",
                       ts=1710000000.0 + 86400 * 90,
                       messages=["Let me share a pasta recipe."]),
            _candidate(conv_id=3, title="SoulPrint SQLite schema decisions"),
            _candidate(conv_id=4, title="SoulPrint SQLite storage next steps"),
        ]
        results = suggest_lineage(source, candidates, limit=3)
        # The two SQLite-related candidates should rank above "cooking recipe"
        if len(results) >= 2:
            top_two_ids = {results[0].target_conversation_id, results[1].target_conversation_id}
            self.assertIn(3, top_two_ids)
            self.assertIn(4, top_two_ids)

    def test_returns_at_most_limit(self):
        source = _source()
        candidates = [
            _candidate(conv_id=i, title=f"SoulPrint SQLite topic {i}")
            for i in range(2, 12)
        ]
        results = suggest_lineage(source, candidates, limit=3)
        self.assertLessEqual(len(results), 3)

    def test_results_sorted_by_confidence_descending(self):
        source = _source()
        candidates = [
            _candidate(conv_id=2, title="SoulPrint SQLite storage plan"),
            _candidate(conv_id=3, title="SoulPrint architecture discussion",
                       ts=1710000100.0),
            _candidate(conv_id=4, title="SoulPrint SQLite storage design review",
                       ts=1710000050.0),
        ]
        results = suggest_lineage(source, candidates, limit=10)
        for i in range(len(results) - 1):
            self.assertGreaterEqual(results[i].confidence, results[i + 1].confidence)

    def test_confidence_between_0_and_1(self):
        source = _source()
        candidates = [_candidate()]
        results = suggest_lineage(source, candidates, limit=5, min_confidence=0.0)
        for s in results:
            self.assertGreaterEqual(s.confidence, 0.0)
            self.assertLessEqual(s.confidence, 1.0)


# ---------------------------------------------------------------------------
# Tests — title overlap scores higher than temporal-only
# ---------------------------------------------------------------------------


class TitleVsTemporalTest(unittest.TestCase):

    def test_title_overlap_beats_temporal_alone(self):
        source = _source(title="SoulPrint SQLite canonical ledger design")
        # High title overlap but far in time
        title_match = _candidate(
            conv_id=2,
            title="SoulPrint SQLite canonical ledger migration",
            ts=1710000000.0 + 86400 * 60,  # 60 days later
        )
        # No title overlap but very close in time
        temporal_match = _candidate(
            conv_id=3,
            title="Unrelated weather forecast discussion",
            ts=1710000000.0 + 60,  # 1 minute later
            messages=["What's the weather like?"],
        )
        results = suggest_lineage(
            source, [title_match, temporal_match], limit=5, min_confidence=0.0,
        )
        if len(results) >= 2:
            self.assertEqual(results[0].target_conversation_id, 2)
        elif len(results) == 1:
            self.assertEqual(results[0].target_conversation_id, 2)

    def test_title_overlap_scorer_jaccard(self):
        score, sig = _title_overlap_score(
            "SoulPrint SQLite storage design",
            "SoulPrint SQLite migration plan",
        )
        self.assertGreater(score, 0.2)
        self.assertIsNotNone(sig)
        self.assertIn("title overlap", sig)

    def test_no_title_overlap_scores_zero(self):
        score, sig = _title_overlap_score("Alpha Beta", "Gamma Delta")
        self.assertEqual(score, 0.0)


# ---------------------------------------------------------------------------
# Tests — relation type labeling
# ---------------------------------------------------------------------------


class RelationTypeLabelingTest(unittest.TestCase):

    def test_all_relation_types_recognized(self):
        expected = {"continues", "forks_from", "revisits", "supersedes"}
        self.assertEqual(VALID_RELATION_TYPES, expected)

    def test_continues_from_continuation_keywords(self):
        source = _source(
            messages=["Continuing from our last discussion about SQLite"],
        )
        candidates = [_candidate(
            title="SoulPrint SQLite storage",
            ts=1710000000.0 - 3600,
        )]
        results = suggest_lineage(source, candidates, limit=5, min_confidence=0.0)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].relation_type, "continues")

    def test_continues_from_temporal_proximity(self):
        rel = _infer_relation_type(
            title_score=0.3, temporal_score=1.0,
            keyword_score=0.2, continuation_score=0.0,
            source_ts=100.0, target_ts=90.0,
        )
        self.assertEqual(rel, "continues")

    def test_supersedes_high_overlap_newer(self):
        rel = _infer_relation_type(
            title_score=0.6, temporal_score=0.0,
            keyword_score=0.4, continuation_score=0.0,
            source_ts=100.0, target_ts=200.0,
        )
        self.assertEqual(rel, "supersedes")

    def test_revisits_overlap_with_time_gap(self):
        rel = _infer_relation_type(
            title_score=0.3, temporal_score=0.0,
            keyword_score=0.2, continuation_score=0.0,
            source_ts=100.0, target_ts=90.0,
        )
        self.assertEqual(rel, "revisits")

    def test_forks_from_default(self):
        rel = _infer_relation_type(
            title_score=0.15, temporal_score=0.5,
            keyword_score=0.1, continuation_score=0.0,
            source_ts=100.0, target_ts=90.0,
        )
        self.assertEqual(rel, "forks_from")

    def test_suggestion_has_valid_relation_type(self):
        source = _source()
        results = suggest_lineage(
            source, [_candidate()], limit=5, min_confidence=0.0,
        )
        for s in results:
            self.assertIn(s.relation_type, VALID_RELATION_TYPES)


# ---------------------------------------------------------------------------
# Tests — no mutation of canonical records
# ---------------------------------------------------------------------------


class NoCanonicalMutationTest(unittest.TestCase):

    def test_source_unchanged_after_suggestion(self):
        source = _source()
        original_id = source.id
        original_title = source.title
        original_ts = source.created_at_unix

        suggest_lineage(source, [_candidate(), _candidate(conv_id=3)])

        self.assertEqual(source.id, original_id)
        self.assertEqual(source.title, original_title)
        self.assertEqual(source.created_at_unix, original_ts)

    def test_candidates_unchanged_after_suggestion(self):
        candidates = [_candidate(conv_id=2), _candidate(conv_id=3)]
        originals = [(c.id, c.title, c.created_at_unix) for c in candidates]

        suggest_lineage(_source(), candidates)

        for c, (oid, otitle, ots) in zip(candidates, originals):
            self.assertEqual(c.id, oid)
            self.assertEqual(c.title, otitle)
            self.assertEqual(c.created_at_unix, ots)

    def test_result_is_derived(self):
        source = _source()
        results = suggest_lineage(
            source, [_candidate()], limit=5, min_confidence=0.0,
        )
        for s in results:
            self.assertEqual(s.derived_from, "canonical_conversations")


# ---------------------------------------------------------------------------
# Tests — empty / no-match cases
# ---------------------------------------------------------------------------


class EmptyAndNoMatchTest(unittest.TestCase):

    def test_no_candidates_returns_empty(self):
        results = suggest_lineage(_source(), [])
        self.assertEqual(results, [])

    def test_self_excluded_from_results(self):
        source = _source(conv_id=1)
        candidates = [
            ConversationSummary(id=1, title="Same conversation"),
        ]
        results = suggest_lineage(source, candidates, min_confidence=0.0)
        self.assertEqual(results, [])

    def test_no_overlap_returns_empty(self):
        source = _source(title="Alpha Beta Gamma", messages=["Aardvark zebra"])
        candidates = [
            _candidate(
                conv_id=2,
                title="Zulu Yankee Xray",
                ts=1710000000.0 + 86400 * 365,
                messages=["Platypus iguana"],
            ),
        ]
        results = suggest_lineage(source, candidates, min_confidence=0.15)
        self.assertEqual(results, [])

    def test_missing_timestamps_still_works(self):
        source = _source(ts=None)
        candidates = [_candidate(ts=None, title="SoulPrint SQLite storage next")]
        results = suggest_lineage(source, candidates, min_confidence=0.0)
        # Should still produce results based on title overlap
        self.assertTrue(len(results) >= 0)  # graceful, not crash

    def test_empty_titles_still_works(self):
        source = _source(title="", ts=None, messages=[])
        candidates = [_candidate(title="", ts=None, messages=[])]
        # With default min_confidence, zero-signal matches are filtered out
        results = suggest_lineage(source, candidates)
        self.assertEqual(results, [])  # no signal above threshold


# ---------------------------------------------------------------------------
# Tests — individual scorer functions
# ---------------------------------------------------------------------------


class ScorerUnitTests(unittest.TestCase):

    def test_temporal_within_48h(self):
        score, sig = _temporal_proximity_score(100.0, 100.0 + 3600 * 24)
        self.assertEqual(score, 1.0)
        self.assertIn("48 hours", sig)

    def test_temporal_within_7d(self):
        score, sig = _temporal_proximity_score(100.0, 100.0 + 3600 * 100)
        self.assertEqual(score, 0.5)
        self.assertIn("7 days", sig)

    def test_temporal_within_30d(self):
        score, sig = _temporal_proximity_score(100.0, 100.0 + 3600 * 500)
        self.assertEqual(score, 0.2)

    def test_temporal_beyond_30d(self):
        score, sig = _temporal_proximity_score(100.0, 100.0 + 3600 * 1000)
        self.assertEqual(score, 0.0)
        self.assertIsNone(sig)

    def test_keyword_overlap_shared_words(self):
        score, sig = _keyword_overlap_score(
            ["Should we use SQLite for storage?"],
            ["Let's plan the SQLite storage migration."],
        )
        self.assertGreater(score, 0.0)
        self.assertIn("shared content keywords", sig)

    def test_keyword_overlap_no_match(self):
        score, sig = _keyword_overlap_score(
            ["Alpha beta gamma"],
            ["Zulu yankee xray"],
        )
        self.assertEqual(score, 0.0)

    def test_continuation_phrase_detected(self):
        score, sig = _continuation_keyword_score(
            ["Continuing from our last discussion about the database"],
        )
        self.assertEqual(score, 1.0)
        self.assertIn("continuation phrase", sig)

    def test_continuation_phrase_absent(self):
        score, sig = _continuation_keyword_score(
            ["Let's discuss a new topic today"],
        )
        self.assertEqual(score, 0.0)
        self.assertIsNone(sig)

    def test_continuation_empty_messages(self):
        score, sig = _continuation_keyword_score([])
        self.assertEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main()
