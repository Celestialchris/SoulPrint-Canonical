"""Obsidian Bridge renderer — produces markdown strings with frontmatter and wiki-links.

Pure functions. No file I/O, no DB access. The caller (exporter) is responsible
for gathering data from the canonical ledger and intelligence stores.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RENDER_VERSION: int = 1

AUTO_BEGIN = "<!-- SOULPRINT:BEGIN AUTO -->"
AUTO_END = "<!-- SOULPRINT:END AUTO -->"

PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    "chatgpt": "ChatGPT",
    "claude": "Claude",
    "gemini": "Gemini",
}

PROVIDER_DESCRIPTIONS: dict[str, str] = {
    "chatgpt": "OpenAI's ChatGPT export",
    "claude": "Anthropic's Claude export",
    "gemini": "Google's Gemini export",
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _format_unix_to_date(timestamp_unix: float | None) -> str | None:
    """Convert Unix timestamp to YYYY-MM-DD string, or None."""
    if timestamp_unix is None:
        return None
    return datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).strftime("%Y-%m-%d")


def _format_unix_to_iso(timestamp_unix: float | None) -> str | None:
    """Convert Unix timestamp to ISO 8601 UTC string, or None."""
    if timestamp_unix is None:
        return None
    return (
        datetime.fromtimestamp(timestamp_unix, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _yaml_quote(value: str) -> str:
    """Wrap a string in double quotes for safe YAML embedding."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _render_yaml_frontmatter(
    fields: list[tuple[str, str | int | list[str]]],
) -> str:
    """Produce a YAML frontmatter block from ordered (key, value) pairs.

    - str values are double-quoted via _yaml_quote
    - int values are bare
    - list[str] values become multi-line YAML lists
    """
    lines = ["---"]
    for key, value in fields:
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {_yaml_quote(item)}")
        elif isinstance(value, int):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {_yaml_quote(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _provider_display(provider_id: str) -> str:
    """Return human-readable provider name."""
    return PROVIDER_DISPLAY_NAMES.get(provider_id, provider_id.capitalize())


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------


def chat_note_filename(provider: str, conversation_id: int) -> str:
    """Return the vault filename for a chat note, e.g. 'chatgpt--142.md'."""
    return f"{provider}--{conversation_id}.md"


def theme_note_filename(topic_label: str) -> str:
    """Return the vault filename for a theme note, e.g. 'retrieval-architecture.md'."""
    if not topic_label or not topic_label.strip():
        return "untitled.md"
    slug = re.sub(r"[^a-z0-9]+", "-", topic_label.lower()).strip("-")
    if not slug:
        return "untitled.md"
    return f"{slug}.md"


def daily_note_filename(date_str: str) -> str:
    """Return the vault filename for a daily note, e.g. '2026-03-22.md'."""
    return f"{date_str}.md"


# ---------------------------------------------------------------------------
# Main renderers
# ---------------------------------------------------------------------------


def render_chat_note(
    *,
    conversation_id: int,
    source: str,
    title: str,
    created_at_unix: float | None,
    updated_at_unix: float | None,
    message_count: int,
    summary_text: str | None = None,
    continuity_artifacts: list[dict[str, str]] | None = None,
    lineage_suggestions: list[dict[str, str | int | float]] | None = None,
    topic_labels: list[str] | None = None,
) -> str:
    """Render a complete chat note with YAML frontmatter and AUTO block."""
    display = _provider_display(source)
    date_str = _format_unix_to_date(created_at_unix)
    iso_str = _format_unix_to_iso(updated_at_unix)

    # -- Frontmatter --
    fm_fields: list[tuple[str, str | int | list[str]]] = [
        ("type", "chat"),
        ("source", "soulprint"),
        ("stable_id", f"imported_conversation:{conversation_id}"),
        ("provider", f"[[{display}]]"),
        ("lane", "imported"),
        ("title", title),
        ("created", f"[[{date_str}]]" if date_str else "unknown"),
    ]
    if iso_str:
        fm_fields.append(("updated", iso_str))
    fm_fields.extend([
        ("categories", ["[[Chat]]"]),
        ("tags", ["chat", "imported", source]),
        ("render_version", RENDER_VERSION),
        ("soulprint_url", f"http://127.0.0.1:5678/imported/{conversation_id}/explorer"),
    ])

    created_display = f"[[{date_str}]]" if date_str else "unknown"
    parts = [_render_yaml_frontmatter(fm_fields)]

    # -- Heading + metadata --
    parts.append(f"# {title}\n")
    parts.append(
        f"> **Provider:** [[{display}]] · **Messages:** {message_count}"
        f" · **Created:** {created_display}\n"
    )

    # -- AUTO block --
    auto_sections: list[str] = []

    if summary_text:
        auto_sections.append(f"## Summary\n\n{summary_text}")

    artifacts = continuity_artifacts or []
    for art in artifacts:
        atype = art.get("artifact_type", "")
        text = art.get("content_text", "")
        if not text:
            continue
        if atype == "decisions":
            auto_sections.append(f"## Key Decisions\n\n{text}")
        elif atype == "open_loops":
            auto_sections.append(f"## Open Loops\n\n{text}")
        elif atype == "entity_map":
            auto_sections.append(f"## Entities\n\n{text}")

    suggestions = lineage_suggestions or []
    if suggestions:
        lines = ["## Related Conversations\n"]
        for s in suggestions:
            tid = s["target_conversation_id"]
            tprov = s["target_provider"]
            ttitle = s["target_title"]
            rel = s["relation_type"]
            fname = chat_note_filename(tprov, tid).removesuffix(".md")
            lines.append(f"- [[{fname}]] — {rel} ({ttitle})")
        auto_sections.append("\n".join(lines))

    labels = topic_labels or []
    if labels:
        lines = ["## Themes\n"]
        for label in labels:
            lines.append(f"- [[{label}]]")
        auto_sections.append("\n".join(lines))

    parts.append(AUTO_BEGIN)
    if auto_sections:
        parts.append("\n\n" + "\n\n".join(auto_sections) + "\n\n")
    else:
        parts.append("\n\n*No intelligence data generated yet.*\n\n")
    parts.append(AUTO_END + "\n")

    return "".join(parts)


def render_theme_note(
    *,
    topic_label: str,
    conversations: list[dict[str, str | int]],
    confidence: str,
    digest_text: str | None = None,
) -> str:
    """Render a theme note with YAML frontmatter and AUTO block."""
    fm_fields: list[tuple[str, str | int | list[str]]] = [
        ("type", "theme"),
        ("source", "soulprint"),
        ("topic_label", topic_label),
        ("categories", ["[[Theme]]"]),
        ("confidence", confidence),
        ("conversation_count", len(conversations)),
        ("render_version", RENDER_VERSION),
    ]

    parts = [_render_yaml_frontmatter(fm_fields)]
    parts.append(f"# {topic_label}\n\n")

    # -- AUTO block --
    auto_sections: list[str] = []

    if digest_text:
        auto_sections.append(f"## Digest\n\n{digest_text}")
    else:
        auto_sections.append(
            "## Digest\n\n*Run a digest in SoulPrint to populate this section.*"
        )

    if conversations:
        lines = ["## Conversations\n"]
        for c in conversations:
            cid = c["conversation_id"]
            cprov = c["provider"]
            ctitle = c["title"]
            fname = chat_note_filename(cprov, cid).removesuffix(".md")
            lines.append(f"- [[{fname}]] — {ctitle}")
        auto_sections.append("\n".join(lines))

    parts.append(AUTO_BEGIN + "\n\n")
    parts.append("\n\n".join(auto_sections))
    parts.append("\n\n" + AUTO_END + "\n")

    return "".join(parts)


def render_daily_note(*, date_str: str) -> str:
    """Render an empty daily note shell."""
    fm_fields: list[tuple[str, str | int | list[str]]] = [
        ("type", "daily"),
        ("date", date_str),
    ]
    return _render_yaml_frontmatter(fm_fields)


def render_provider_note(*, provider_id: str, conversation_count: int) -> str:
    """Render a provider reference note with AUTO block."""
    display = _provider_display(provider_id)
    desc = PROVIDER_DESCRIPTIONS.get(
        provider_id, f"{display} export"
    )

    fm_fields: list[tuple[str, str | int | list[str]]] = [
        ("type", "provider"),
        ("provider_id", provider_id),
    ]

    parts = [_render_yaml_frontmatter(fm_fields)]
    parts.append(f"# {display}\n\n")
    parts.append(f"Conversations imported from {desc}.\n\n")
    parts.append(AUTO_BEGIN + "\n")
    parts.append(f"**Conversation count:** {conversation_count}\n")
    parts.append(AUTO_END + "\n")

    return "".join(parts)


def render_category_note(
    *,
    category_name: str,
    folder_source: str,
    dataview_fields: list[str],
    sort_field: str,
) -> str:
    """Render a category note with a Dataview query."""
    fm_fields: list[tuple[str, str | int | list[str]]] = [
        ("type", "category"),
    ]

    fields_str = ", ".join(dataview_fields)
    parts = [_render_yaml_frontmatter(fm_fields)]
    parts.append(f"# {category_name}\n\n")
    parts.append("```dataview\n")
    parts.append(f"TABLE {fields_str}\n")
    parts.append(f'FROM "{folder_source}"\n')
    parts.append(f"SORT {sort_field} DESC\n")
    parts.append("```\n")

    return "".join(parts)
