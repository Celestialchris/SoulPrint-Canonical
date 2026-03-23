"""Tests for the Obsidian Bridge renderer — pure unit tests, no DB or app context."""

import unittest

from src.obsidian.renderer import (
    AUTO_BEGIN,
    AUTO_END,
    RENDER_VERSION,
    chat_note_filename,
    daily_note_filename,
    render_category_note,
    render_chat_note,
    render_daily_note,
    render_provider_note,
    render_theme_note,
    theme_note_filename,
)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

SAMPLE_CHAT_KWARGS = dict(
    conversation_id=142,
    source="chatgpt",
    title="Retrieval architecture for federated search",
    created_at_unix=1742673000.0,  # 2025-03-22 18:30:00 UTC
    updated_at_unix=1742673000.0,
    message_count=47,
)

FULL_INTEL_KWARGS = dict(
    summary_text="Discussed federated search architecture across providers.",
    continuity_artifacts=[
        {"artifact_type": "decisions", "content_text": "Use lane-aware retrieval."},
        {"artifact_type": "open_loops", "content_text": "Pagination not resolved."},
        {"artifact_type": "entity_map", "content_text": "- SoulPrint\n- Obsidian"},
    ],
    lineage_suggestions=[
        {
            "target_conversation_id": 138,
            "target_title": "Lane-aware search design",
            "target_provider": "chatgpt",
            "relation_type": "continues",
        },
        {
            "target_conversation_id": 45,
            "target_title": "Federated retrieval boundary",
            "target_provider": "claude",
            "relation_type": "forks_from",
        },
    ],
    topic_labels=["Retrieval Architecture", "Federated Search"],
)


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------


class ChatNoteFilenameTest(unittest.TestCase):
    def test_standard_format(self):
        self.assertEqual(chat_note_filename("chatgpt", 142), "chatgpt--142.md")

    def test_different_provider(self):
        self.assertEqual(chat_note_filename("claude", 45), "claude--45.md")


class ThemeNoteFilenameTest(unittest.TestCase):
    def test_slugifies_spaces(self):
        self.assertEqual(
            theme_note_filename("Retrieval Architecture"),
            "retrieval-architecture.md",
        )

    def test_slugifies_special_chars(self):
        self.assertEqual(theme_note_filename("AI / ML Topics"), "ai-ml-topics.md")

    def test_empty_label_fallback(self):
        self.assertEqual(theme_note_filename(""), "untitled.md")

    def test_lowercase(self):
        self.assertEqual(theme_note_filename("UPPERCASE"), "uppercase.md")

    def test_whitespace_only_fallback(self):
        self.assertEqual(theme_note_filename("   "), "untitled.md")


class DailyNoteFilenameTest(unittest.TestCase):
    def test_standard_format(self):
        self.assertEqual(daily_note_filename("2026-03-22"), "2026-03-22.md")


# ---------------------------------------------------------------------------
# Chat note — frontmatter
# ---------------------------------------------------------------------------


class ChatNoteFrontmatterTest(unittest.TestCase):
    def setUp(self):
        self.output = render_chat_note(**SAMPLE_CHAT_KWARGS)
        # Extract frontmatter (between first and second ---)
        parts = self.output.split("---", 2)
        self.frontmatter = parts[1] if len(parts) >= 3 else ""

    def test_has_yaml_delimiters(self):
        self.assertTrue(self.output.startswith("---\n"))
        self.assertGreater(self.output.count("---"), 1)

    def test_type_field(self):
        self.assertIn("type: \"chat\"", self.frontmatter)

    def test_source_field(self):
        self.assertIn("source: \"soulprint\"", self.frontmatter)

    def test_stable_id_field(self):
        self.assertIn("stable_id: \"imported_conversation:142\"", self.frontmatter)

    def test_provider_is_wiki_link(self):
        self.assertIn('provider: "[[ChatGPT]]"', self.frontmatter)

    def test_lane_field(self):
        self.assertIn("lane: \"imported\"", self.frontmatter)

    def test_title_field(self):
        self.assertIn("Retrieval architecture for federated search", self.frontmatter)

    def test_created_is_wiki_link(self):
        self.assertIn('created: "[[2025-03-22]]"', self.frontmatter)

    def test_updated_field(self):
        self.assertIn("2025-03-22T19:50:00Z", self.frontmatter)

    def test_categories_field(self):
        self.assertIn('"[[Chat]]"', self.frontmatter)

    def test_tags_field(self):
        self.assertIn('"chat"', self.frontmatter)
        self.assertIn('"imported"', self.frontmatter)
        self.assertIn('"chatgpt"', self.frontmatter)

    def test_render_version(self):
        self.assertIn(f"render_version: {RENDER_VERSION}", self.frontmatter)

    def test_soulprint_url(self):
        self.assertIn(
            "http://127.0.0.1:5678/imported/142/explorer", self.frontmatter
        )


# ---------------------------------------------------------------------------
# Chat note — body with full intelligence
# ---------------------------------------------------------------------------


class ChatNoteBodyFullIntelligenceTest(unittest.TestCase):
    def setUp(self):
        self.output = render_chat_note(**SAMPLE_CHAT_KWARGS, **FULL_INTEL_KWARGS)

    def test_heading(self):
        self.assertIn("# Retrieval architecture for federated search", self.output)

    def test_metadata_line(self):
        self.assertIn("**Provider:** [[ChatGPT]]", self.output)
        self.assertIn("**Messages:** 47", self.output)
        self.assertIn("**Created:** [[2025-03-22]]", self.output)

    def test_auto_markers_present(self):
        self.assertIn(AUTO_BEGIN, self.output)
        self.assertIn(AUTO_END, self.output)

    def test_summary_section(self):
        self.assertIn("## Summary", self.output)
        self.assertIn(
            "Discussed federated search architecture across providers.", self.output
        )

    def test_decisions_section(self):
        self.assertIn("## Key Decisions", self.output)
        self.assertIn("Use lane-aware retrieval.", self.output)

    def test_open_loops_section(self):
        self.assertIn("## Open Loops", self.output)
        self.assertIn("Pagination not resolved.", self.output)

    def test_entities_section(self):
        self.assertIn("## Entities", self.output)
        self.assertIn("- SoulPrint", self.output)

    def test_related_conversations_section(self):
        self.assertIn("## Related Conversations", self.output)
        self.assertIn("[[chatgpt--138]]", self.output)
        self.assertIn("[[claude--45]]", self.output)

    def test_lineage_relation_type(self):
        self.assertIn("continues", self.output)
        self.assertIn("forks_from", self.output)

    def test_themes_section(self):
        self.assertIn("## Themes", self.output)
        self.assertIn("[[Retrieval Architecture]]", self.output)
        self.assertIn("[[Federated Search]]", self.output)

    def test_auto_block_contains_all_sections(self):
        begin_idx = self.output.index(AUTO_BEGIN)
        end_idx = self.output.index(AUTO_END)
        auto_block = self.output[begin_idx:end_idx]
        self.assertIn("## Summary", auto_block)
        self.assertIn("## Key Decisions", auto_block)
        self.assertIn("## Open Loops", auto_block)
        self.assertIn("## Entities", auto_block)
        self.assertIn("## Related Conversations", auto_block)
        self.assertIn("## Themes", auto_block)


# ---------------------------------------------------------------------------
# Chat note — thin (no intelligence)
# ---------------------------------------------------------------------------


class ChatNoteThinTest(unittest.TestCase):
    def setUp(self):
        self.output = render_chat_note(**SAMPLE_CHAT_KWARGS)

    def test_thin_note_valid_frontmatter(self):
        self.assertTrue(self.output.startswith("---\n"))

    def test_thin_note_has_heading(self):
        self.assertIn("# Retrieval architecture for federated search", self.output)

    def test_thin_note_has_auto_markers(self):
        self.assertIn(AUTO_BEGIN, self.output)
        self.assertIn(AUTO_END, self.output)

    def test_thin_note_placeholder_text(self):
        self.assertIn("*No intelligence data generated yet.*", self.output)

    def test_thin_note_no_summary_section(self):
        self.assertNotIn("## Summary", self.output)

    def test_thin_note_no_decisions_section(self):
        self.assertNotIn("## Key Decisions", self.output)


# ---------------------------------------------------------------------------
# Chat note — partial intelligence
# ---------------------------------------------------------------------------


class ChatNotePartialIntelligenceTest(unittest.TestCase):
    def test_summary_only_no_decisions(self):
        output = render_chat_note(
            **SAMPLE_CHAT_KWARGS, summary_text="Just a summary."
        )
        self.assertIn("## Summary", output)
        self.assertNotIn("## Key Decisions", output)

    def test_no_lineage_no_related_section(self):
        output = render_chat_note(
            **SAMPLE_CHAT_KWARGS, summary_text="Has summary."
        )
        self.assertNotIn("## Related Conversations", output)

    def test_no_topics_no_themes_section(self):
        output = render_chat_note(
            **SAMPLE_CHAT_KWARGS, summary_text="Has summary."
        )
        self.assertNotIn("## Themes", output)


# ---------------------------------------------------------------------------
# Theme note
# ---------------------------------------------------------------------------


class ThemeNoteTest(unittest.TestCase):
    CONVERSATIONS = [
        {"conversation_id": 142, "provider": "chatgpt", "title": "Retrieval arch"},
        {"conversation_id": 138, "provider": "chatgpt", "title": "Lane-aware search"},
        {"conversation_id": 45, "provider": "claude", "title": "Federated retrieval"},
    ]

    def setUp(self):
        self.with_digest = render_theme_note(
            topic_label="Retrieval Architecture",
            conversations=self.CONVERSATIONS,
            confidence="high",
            digest_text="Cross-conversation synthesis of retrieval patterns.",
        )
        self.without_digest = render_theme_note(
            topic_label="Retrieval Architecture",
            conversations=self.CONVERSATIONS,
            confidence="high",
        )

    def test_frontmatter_type(self):
        self.assertIn('type: "theme"', self.with_digest)

    def test_frontmatter_topic_label(self):
        self.assertIn("Retrieval Architecture", self.with_digest)

    def test_frontmatter_confidence(self):
        self.assertIn('confidence: "high"', self.with_digest)

    def test_frontmatter_conversation_count(self):
        self.assertIn("conversation_count: 3", self.with_digest)

    def test_frontmatter_render_version(self):
        self.assertIn(f"render_version: {RENDER_VERSION}", self.with_digest)

    def test_digest_section_with_text(self):
        self.assertIn("## Digest", self.with_digest)
        self.assertIn(
            "Cross-conversation synthesis of retrieval patterns.", self.with_digest
        )

    def test_digest_section_without_text(self):
        self.assertIn("## Digest", self.without_digest)
        self.assertIn(
            "Run a digest in SoulPrint to populate this section.", self.without_digest
        )

    def test_conversations_as_wiki_links(self):
        self.assertIn("[[chatgpt--142]]", self.with_digest)
        self.assertIn("[[chatgpt--138]]", self.with_digest)
        self.assertIn("[[claude--45]]", self.with_digest)

    def test_auto_markers_present(self):
        self.assertIn(AUTO_BEGIN, self.with_digest)
        self.assertIn(AUTO_END, self.with_digest)

    def test_valid_frontmatter_delimiters(self):
        self.assertTrue(self.with_digest.startswith("---\n"))


# ---------------------------------------------------------------------------
# Daily note
# ---------------------------------------------------------------------------


class DailyNoteTest(unittest.TestCase):
    def setUp(self):
        self.output = render_daily_note(date_str="2026-03-22")

    def test_frontmatter_type(self):
        self.assertIn('type: "daily"', self.output)

    def test_frontmatter_date(self):
        self.assertIn('date: "2026-03-22"', self.output)

    def test_empty_body(self):
        # After the closing ---, there should be nothing meaningful
        parts = self.output.split("---", 2)
        body = parts[2] if len(parts) >= 3 else ""
        self.assertEqual(body.strip(), "")

    def test_valid_frontmatter_delimiters(self):
        self.assertTrue(self.output.startswith("---\n"))
        self.assertGreater(self.output.count("---"), 1)


# ---------------------------------------------------------------------------
# Provider note
# ---------------------------------------------------------------------------


class ProviderNoteTest(unittest.TestCase):
    def setUp(self):
        self.output = render_provider_note(
            provider_id="chatgpt", conversation_count=882
        )

    def test_frontmatter_type(self):
        self.assertIn('type: "provider"', self.output)

    def test_frontmatter_provider_id(self):
        self.assertIn('provider_id: "chatgpt"', self.output)

    def test_heading_display_name(self):
        self.assertIn("# ChatGPT", self.output)

    def test_description_text(self):
        self.assertIn("OpenAI's ChatGPT export", self.output)

    def test_conversation_count_in_auto_block(self):
        begin_idx = self.output.index(AUTO_BEGIN)
        end_idx = self.output.index(AUTO_END)
        auto_block = self.output[begin_idx:end_idx]
        self.assertIn("**Conversation count:** 882", auto_block)

    def test_auto_markers_present(self):
        self.assertIn(AUTO_BEGIN, self.output)
        self.assertIn(AUTO_END, self.output)


# ---------------------------------------------------------------------------
# Category note
# ---------------------------------------------------------------------------


class CategoryNoteTest(unittest.TestCase):
    def setUp(self):
        self.output = render_category_note(
            category_name="Chats",
            folder_source="Chats",
            dataview_fields=["provider", "created", "title"],
            sort_field="created",
        )

    def test_frontmatter_type(self):
        self.assertIn('type: "category"', self.output)

    def test_heading(self):
        self.assertIn("# Chats", self.output)

    def test_dataview_query_table(self):
        self.assertIn("TABLE provider, created, title", self.output)

    def test_dataview_query_from(self):
        self.assertIn('FROM "Chats"', self.output)

    def test_dataview_query_sort(self):
        self.assertIn("SORT created DESC", self.output)

    def test_dataview_code_block(self):
        self.assertIn("```dataview", self.output)
        # Must close the code block
        parts = self.output.split("```dataview")
        self.assertIn("```", parts[1])


# ---------------------------------------------------------------------------
# YAML safety edge cases
# ---------------------------------------------------------------------------


class YamlSafetyTest(unittest.TestCase):
    def test_title_with_colon(self):
        output = render_chat_note(
            conversation_id=1,
            source="chatgpt",
            title="Note: this has a colon",
            created_at_unix=1742673000.0,
            updated_at_unix=None,
            message_count=5,
        )
        self.assertIn('"Note: this has a colon"', output)

    def test_title_with_quotes(self):
        output = render_chat_note(
            conversation_id=2,
            source="chatgpt",
            title='She said "hello"',
            created_at_unix=1742673000.0,
            updated_at_unix=None,
            message_count=3,
        )
        self.assertIn('She said \\"hello\\"', output)

    def test_none_created_at(self):
        output = render_chat_note(
            conversation_id=3,
            source="chatgpt",
            title="No date",
            created_at_unix=None,
            updated_at_unix=None,
            message_count=1,
        )
        self.assertIn('created: "unknown"', output)

    def test_none_updated_omitted(self):
        output = render_chat_note(
            conversation_id=4,
            source="chatgpt",
            title="No update",
            created_at_unix=1742673000.0,
            updated_at_unix=None,
            message_count=1,
        )
        self.assertNotIn("updated:", output)

    def test_all_notes_start_with_yaml_delimiter(self):
        """Every renderer produces output starting with ---."""
        for output in [
            render_chat_note(**SAMPLE_CHAT_KWARGS),
            render_theme_note(
                topic_label="Test",
                conversations=[],
                confidence="low",
            ),
            render_daily_note(date_str="2026-01-01"),
            render_provider_note(provider_id="claude", conversation_count=10),
            render_category_note(
                category_name="X",
                folder_source="X",
                dataview_fields=["a"],
                sort_field="a",
            ),
        ]:
            self.assertTrue(output.startswith("---\n"), f"Failed for: {output[:40]}")


if __name__ == "__main__":
    unittest.main()
