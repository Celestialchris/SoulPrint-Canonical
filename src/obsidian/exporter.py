"""Obsidian Bridge exporter — orchestrates data gathering and file writing.

Reads canonical conversations from SQLite and intelligence data from JSONL
stores, renders markdown notes via the renderer, and writes them to a vault.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask

from src.app.models import ImportedConversation
from src.app.models.db import db
from src.intelligence.continuity.lineage import ConversationSummary, suggest_lineage
from src.intelligence.continuity.store import (
    default_continuity_store_path,
    list_artifacts_for_conversation,
)
from src.intelligence.store import (
    default_digest_store_path,
    default_summary_store_path,
    default_topic_store_path,
    list_digests,
    list_summaries,
    list_topic_scans,
)
from src.obsidian.config import generate_config, generate_templates
from src.obsidian.renderer import (
    AUTO_BEGIN,
    AUTO_END,
    PROVIDER_DISPLAY_NAMES,
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
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExportResult:
    chat_count: int
    theme_count: int
    daily_count: int
    provider_count: int
    skipped: int
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RefreshResult:
    updated: int
    skipped: int
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _sqlite_app(sqlite_path: str | Path) -> Flask:
    """Create a minimal Flask app for ORM access to a SQLite database."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{Path(sqlite_path).resolve()}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _format_unix_to_date(timestamp_unix: float | None) -> str | None:
    """Convert Unix timestamp to YYYY-MM-DD string, or None."""
    if timestamp_unix is None:
        return None
    return datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).strftime("%Y-%m-%d")


def _build_intelligence_lookups(
    db_path: str,
) -> tuple[dict[str, str], dict[str, list[str]], dict[str, str], list[dict] | None]:
    """Load all intelligence stores and build lookup dicts.

    Returns:
        summaries_by_stable_id: {stable_id: summary_text}
        topic_labels_by_stable_id: {stable_id: [topic_labels]}
        digests_by_topic: {topic_label: digest_text}
        latest_topic_scan: the full scan dict, or None
    """
    # Summaries
    summary_store = str(default_summary_store_path(db_path))
    summaries_by_stable_id: dict[str, str] = {}
    for s in list_summaries(summary_store, limit=9999):
        sid = s.get("source_conversation_stable_id", "")
        if sid and sid not in summaries_by_stable_id:
            summaries_by_stable_id[sid] = s.get("summary_text", "")

    # Topic scans (latest only)
    topic_store = str(default_topic_store_path(db_path))
    scans = list_topic_scans(topic_store, limit=1)
    latest_topic_scan = scans[0] if scans else None

    topic_labels_by_stable_id: dict[str, list[str]] = {}
    if latest_topic_scan:
        for cluster in latest_topic_scan.get("clusters", []):
            label = cluster.get("topic_label", "")
            for sid in cluster.get("conversation_stable_ids", []):
                topic_labels_by_stable_id.setdefault(sid, []).append(label)

    # Digests
    digest_store = str(default_digest_store_path(db_path))
    digests_by_topic: dict[str, str] = {}
    for d in list_digests(digest_store, limit=9999):
        topic = d.get("topic_label", "")
        if topic and topic not in digests_by_topic:
            digests_by_topic[topic] = d.get("digest_text", "")

    return (
        summaries_by_stable_id,
        topic_labels_by_stable_id,
        digests_by_topic,
        latest_topic_scan,
    )


def _update_auto_block(existing_content: str, new_auto_content: str) -> str | None:
    """Replace content between AUTO markers. Return None if markers not found."""
    try:
        begin_idx = existing_content.index(AUTO_BEGIN)
        end_idx = existing_content.index(AUTO_END)
    except ValueError:
        return None

    return (
        existing_content[: begin_idx + len(AUTO_BEGIN)]
        + new_auto_content
        + existing_content[end_idx:]
    )


def _extract_auto_content(rendered: str) -> str | None:
    """Extract the content between AUTO markers from a rendered string."""
    try:
        begin = rendered.index(AUTO_BEGIN) + len(AUTO_BEGIN)
        end = rendered.index(AUTO_END)
        return rendered[begin:end]
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_vault(
    db_path: str | Path,
    vault_path: str | Path,
    *,
    incremental: bool = False,
    dry_run: bool = False,
) -> ExportResult:
    """Export canonical conversations and intelligence data to an Obsidian vault."""
    db_path = str(Path(db_path).resolve())
    vault_root = Path(vault_path)

    # Create vault directories
    if not dry_run:
        for subdir in ("Chats", "Themes", "Daily", "References"):
            (vault_root / subdir).mkdir(parents=True, exist_ok=True)

    # Build intelligence lookups (plain file I/O, no Flask needed)
    (
        summaries_by_stable_id,
        topic_labels_by_stable_id,
        digests_by_topic,
        latest_topic_scan,
    ) = _build_intelligence_lookups(db_path)

    continuity_store = str(default_continuity_store_path(db_path))

    # Counters
    chat_count = 0
    theme_count = 0
    daily_count = 0
    provider_count = 0
    skipped = 0
    errors: list[str] = []
    unique_dates: set[str] = set()
    unique_providers: dict[str, int] = {}

    # Open DB
    app = _sqlite_app(db_path)
    with app.app_context():
        try:
            conversations = ImportedConversation.query.order_by(
                ImportedConversation.id.asc()
            ).all()

            # Build lookup and lineage summaries
            conversation_by_id: dict[int, ImportedConversation] = {
                c.id: c for c in conversations
            }
            all_summaries: list[ConversationSummary] = []
            for c in conversations:
                sorted_msgs = sorted(c.messages, key=lambda m: m.sequence_index)
                previews = [m.content for m in sorted_msgs[:3]]
                all_summaries.append(
                    ConversationSummary(
                        id=c.id,
                        title=c.title or "",
                        created_at_unix=c.created_at_unix,
                        message_previews=previews,
                    )
                )

            # Sort for candidate windowing
            sorted_summaries = sorted(
                all_summaries, key=lambda s: s.created_at_unix or 0
            )
            summary_index = {s.id: idx for idx, s in enumerate(sorted_summaries)}

            # ---- Chat notes ----
            for conv in conversations:
                stable_id = f"imported_conversation:{conv.id}"
                filename = chat_note_filename(conv.source, conv.id)
                filepath = vault_root / "Chats" / filename

                # Track providers
                unique_providers[conv.source] = (
                    unique_providers.get(conv.source, 0) + 1
                )

                # Track dates
                date_str = _format_unix_to_date(conv.created_at_unix)
                if date_str:
                    unique_dates.add(date_str)

                # Incremental: skip existing
                if incremental and filepath.exists():
                    skipped += 1
                    continue

                # Gather intelligence
                summary_text = summaries_by_stable_id.get(stable_id)
                topic_labels = topic_labels_by_stable_id.get(stable_id, [])

                # Continuity artifacts
                try:
                    continuity_artifacts = list_artifacts_for_conversation(
                        continuity_store, stable_id, limit=50
                    )
                except Exception:
                    continuity_artifacts = []

                # Lineage: nearest 50 candidates by timestamp
                idx = summary_index.get(conv.id, 0)
                start = max(0, idx - 25)
                end = min(len(sorted_summaries), idx + 26)
                candidates = [
                    s for s in sorted_summaries[start:end] if s.id != conv.id
                ]

                source_summary = next(
                    (s for s in all_summaries if s.id == conv.id), None
                )
                lineage_dicts: list[dict[str, str | int | float]] = []
                if source_summary and candidates:
                    try:
                        raw = suggest_lineage(source_summary, candidates, limit=3)
                        for ls in raw:
                            target_conv = conversation_by_id.get(
                                ls.target_conversation_id
                            )
                            lineage_dicts.append(
                                {
                                    "target_conversation_id": ls.target_conversation_id,
                                    "target_title": ls.target_title,
                                    "target_provider": (
                                        target_conv.source
                                        if target_conv
                                        else "unknown"
                                    ),
                                    "relation_type": ls.relation_type,
                                }
                            )
                    except Exception:
                        pass

                # Render
                try:
                    md = render_chat_note(
                        conversation_id=conv.id,
                        source=conv.source,
                        title=conv.title or "Untitled",
                        created_at_unix=conv.created_at_unix,
                        updated_at_unix=conv.updated_at_unix,
                        message_count=len(conv.messages),
                        summary_text=summary_text,
                        continuity_artifacts=continuity_artifacts or None,
                        lineage_suggestions=lineage_dicts or None,
                        topic_labels=topic_labels or None,
                    )
                except Exception as exc:
                    errors.append(f"Chat {conv.id}: {exc}")
                    continue

                if not dry_run:
                    filepath.write_text(md, encoding="utf-8")
                chat_count += 1

            # ---- Theme notes ----
            if latest_topic_scan:
                for cluster in latest_topic_scan.get("clusters", []):
                    topic_label = cluster.get("topic_label", "")
                    conv_stable_ids = cluster.get("conversation_stable_ids", [])
                    conv_titles = cluster.get("conversation_titles", [])
                    confidence = cluster.get("confidence", "low")

                    theme_conversations: list[dict[str, str | int]] = []
                    for sid, title in zip(conv_stable_ids, conv_titles):
                        try:
                            cid = int(sid.split(":")[1])
                        except (IndexError, ValueError):
                            continue
                        target_conv = conversation_by_id.get(cid)
                        provider = target_conv.source if target_conv else "unknown"
                        theme_conversations.append(
                            {
                                "conversation_id": cid,
                                "provider": provider,
                                "title": title,
                            }
                        )

                    digest_text = digests_by_topic.get(topic_label)
                    filename = theme_note_filename(topic_label)
                    filepath = vault_root / "Themes" / filename

                    try:
                        md = render_theme_note(
                            topic_label=topic_label,
                            conversations=theme_conversations,
                            confidence=confidence,
                            digest_text=digest_text,
                        )
                    except Exception as exc:
                        errors.append(f"Theme '{topic_label}': {exc}")
                        continue

                    if not dry_run:
                        filepath.write_text(md, encoding="utf-8")
                    theme_count += 1

        finally:
            db.session.remove()
            db.engine.dispose()

    # ---- Daily notes ----
    for date_str in sorted(unique_dates):
        filename = daily_note_filename(date_str)
        filepath = vault_root / "Daily" / filename
        if filepath.exists():
            continue
        md = render_daily_note(date_str=date_str)
        if not dry_run:
            filepath.write_text(md, encoding="utf-8")
        daily_count += 1

    # ---- Provider reference notes ----
    for provider_id, conv_count in sorted(unique_providers.items()):
        display = PROVIDER_DISPLAY_NAMES.get(provider_id, provider_id.capitalize())
        filepath = vault_root / "References" / f"{display}.md"
        md = render_provider_note(provider_id=provider_id, conversation_count=conv_count)
        if not dry_run:
            filepath.write_text(md, encoding="utf-8")
        provider_count += 1

    # ---- Category notes ----
    if not dry_run:
        chat_cat = render_category_note(
            category_name="Chats",
            folder_source="Chats",
            dataview_fields=["provider", "created", "title"],
            sort_field="created",
        )
        (vault_root / "Chat.md").write_text(chat_cat, encoding="utf-8")

        theme_cat = render_category_note(
            category_name="Themes",
            folder_source="Themes",
            dataview_fields=["conversation_count", "confidence"],
            sort_field="conversation_count",
        )
        (vault_root / "Theme.md").write_text(theme_cat, encoding="utf-8")

    # ---- Vault config ----
    if not dry_run:
        generate_config(vault_root)
        generate_templates(vault_root)

    return ExportResult(
        chat_count=chat_count,
        theme_count=theme_count,
        daily_count=daily_count,
        provider_count=provider_count,
        skipped=skipped,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


def refresh_vault(
    db_path: str | Path,
    vault_path: str | Path,
) -> RefreshResult:
    """Refresh AUTO blocks in existing vault notes with fresh intelligence data."""
    db_path = str(Path(db_path).resolve())
    vault_root = Path(vault_path)

    (
        summaries_by_stable_id,
        topic_labels_by_stable_id,
        digests_by_topic,
        latest_topic_scan,
    ) = _build_intelligence_lookups(db_path)

    continuity_store = str(default_continuity_store_path(db_path))

    updated = 0
    skipped = 0
    errors: list[str] = []

    app = _sqlite_app(db_path)
    with app.app_context():
        try:
            conversations = ImportedConversation.query.all()
            conversation_by_id: dict[int, ImportedConversation] = {
                c.id: c for c in conversations
            }

            # Build lineage infrastructure
            all_summaries: list[ConversationSummary] = []
            for c in conversations:
                sorted_msgs = sorted(c.messages, key=lambda m: m.sequence_index)
                previews = [m.content for m in sorted_msgs[:3]]
                all_summaries.append(
                    ConversationSummary(
                        id=c.id,
                        title=c.title or "",
                        created_at_unix=c.created_at_unix,
                        message_previews=previews,
                    )
                )
            sorted_summaries = sorted(
                all_summaries, key=lambda s: s.created_at_unix or 0
            )
            summary_index = {s.id: idx for idx, s in enumerate(sorted_summaries)}

            # ---- Refresh chat notes ----
            chats_dir = vault_root / "Chats"
            if chats_dir.exists():
                for filepath in chats_dir.glob("*.md"):
                    existing = filepath.read_text(encoding="utf-8")
                    if AUTO_BEGIN not in existing or AUTO_END not in existing:
                        skipped += 1
                        continue

                    # Parse conversation ID from filename: provider--id.md
                    stem = filepath.stem
                    parts = stem.split("--")
                    if len(parts) < 2:
                        skipped += 1
                        continue
                    try:
                        conv_id = int(parts[-1])
                    except ValueError:
                        skipped += 1
                        continue

                    conv = conversation_by_id.get(conv_id)
                    if not conv:
                        skipped += 1
                        continue

                    stable_id = f"imported_conversation:{conv.id}"
                    summary_text = summaries_by_stable_id.get(stable_id)
                    topic_labels = topic_labels_by_stable_id.get(stable_id, [])

                    try:
                        continuity_artifacts = list_artifacts_for_conversation(
                            continuity_store, stable_id, limit=50
                        )
                    except Exception:
                        continuity_artifacts = []

                    # Lineage
                    idx = summary_index.get(conv.id, 0)
                    start = max(0, idx - 25)
                    end = min(len(sorted_summaries), idx + 26)
                    candidates = [
                        s for s in sorted_summaries[start:end] if s.id != conv.id
                    ]
                    source_summary = next(
                        (s for s in all_summaries if s.id == conv.id), None
                    )
                    lineage_dicts: list[dict[str, str | int | float]] = []
                    if source_summary and candidates:
                        try:
                            raw = suggest_lineage(
                                source_summary, candidates, limit=3
                            )
                            for ls in raw:
                                tc = conversation_by_id.get(
                                    ls.target_conversation_id
                                )
                                lineage_dicts.append(
                                    {
                                        "target_conversation_id": ls.target_conversation_id,
                                        "target_title": ls.target_title,
                                        "target_provider": (
                                            tc.source if tc else "unknown"
                                        ),
                                        "relation_type": ls.relation_type,
                                    }
                                )
                        except Exception:
                            pass

                    try:
                        fresh = render_chat_note(
                            conversation_id=conv.id,
                            source=conv.source,
                            title=conv.title or "Untitled",
                            created_at_unix=conv.created_at_unix,
                            updated_at_unix=conv.updated_at_unix,
                            message_count=len(conv.messages),
                            summary_text=summary_text,
                            continuity_artifacts=continuity_artifacts or None,
                            lineage_suggestions=lineage_dicts or None,
                            topic_labels=topic_labels or None,
                        )
                    except Exception as exc:
                        errors.append(f"Refresh chat {conv.id}: {exc}")
                        continue

                    new_auto = _extract_auto_content(fresh)
                    if new_auto is None:
                        skipped += 1
                        continue

                    result = _update_auto_block(existing, new_auto)
                    if result is None:
                        skipped += 1
                        continue

                    filepath.write_text(result, encoding="utf-8")
                    updated += 1

            # ---- Refresh theme notes ----
            themes_dir = vault_root / "Themes"
            if themes_dir.exists() and latest_topic_scan:
                # Build topic label -> cluster lookup
                cluster_by_label: dict[str, dict] = {}
                for cluster in latest_topic_scan.get("clusters", []):
                    cluster_by_label[cluster.get("topic_label", "")] = cluster

                for filepath in themes_dir.glob("*.md"):
                    existing = filepath.read_text(encoding="utf-8")
                    if AUTO_BEGIN not in existing or AUTO_END not in existing:
                        skipped += 1
                        continue

                    # Extract topic_label from frontmatter
                    topic_label = None
                    in_frontmatter = False
                    for line in existing.splitlines():
                        if line.strip() == "---":
                            if in_frontmatter:
                                break
                            in_frontmatter = True
                            continue
                        if in_frontmatter and line.startswith("topic_label:"):
                            raw = line.split(":", 1)[1].strip()
                            topic_label = raw.strip('"').strip("'")
                            break

                    if not topic_label:
                        skipped += 1
                        continue

                    cluster = cluster_by_label.get(topic_label)
                    if not cluster:
                        skipped += 1
                        continue

                    conv_stable_ids = cluster.get("conversation_stable_ids", [])
                    conv_titles = cluster.get("conversation_titles", [])
                    confidence = cluster.get("confidence", "low")

                    theme_conversations: list[dict[str, str | int]] = []
                    for sid, title in zip(conv_stable_ids, conv_titles):
                        try:
                            cid = int(sid.split(":")[1])
                        except (IndexError, ValueError):
                            continue
                        tc = conversation_by_id.get(cid)
                        provider = tc.source if tc else "unknown"
                        theme_conversations.append(
                            {
                                "conversation_id": cid,
                                "provider": provider,
                                "title": title,
                            }
                        )

                    digest_text = digests_by_topic.get(topic_label)

                    try:
                        fresh = render_theme_note(
                            topic_label=topic_label,
                            conversations=theme_conversations,
                            confidence=confidence,
                            digest_text=digest_text,
                        )
                    except Exception as exc:
                        errors.append(f"Refresh theme '{topic_label}': {exc}")
                        continue

                    new_auto = _extract_auto_content(fresh)
                    if new_auto is None:
                        skipped += 1
                        continue

                    result = _update_auto_block(existing, new_auto)
                    if result is None:
                        skipped += 1
                        continue

                    filepath.write_text(result, encoding="utf-8")
                    updated += 1

            # ---- Refresh provider notes ----
            refs_dir = vault_root / "References"
            if refs_dir.exists():
                # Recount conversations per provider
                provider_counts: dict[str, int] = {}
                for c in conversations:
                    provider_counts[c.source] = (
                        provider_counts.get(c.source, 0) + 1
                    )

                for filepath in refs_dir.glob("*.md"):
                    existing = filepath.read_text(encoding="utf-8")
                    if AUTO_BEGIN not in existing or AUTO_END not in existing:
                        skipped += 1
                        continue

                    # Extract provider_id from frontmatter
                    provider_id = None
                    in_frontmatter = False
                    for line in existing.splitlines():
                        if line.strip() == "---":
                            if in_frontmatter:
                                break
                            in_frontmatter = True
                            continue
                        if in_frontmatter and line.startswith("provider_id:"):
                            raw = line.split(":", 1)[1].strip()
                            provider_id = raw.strip('"').strip("'")
                            break

                    if not provider_id:
                        skipped += 1
                        continue

                    conv_count = provider_counts.get(provider_id, 0)

                    try:
                        fresh = render_provider_note(
                            provider_id=provider_id,
                            conversation_count=conv_count,
                        )
                    except Exception as exc:
                        errors.append(f"Refresh provider '{provider_id}': {exc}")
                        continue

                    new_auto = _extract_auto_content(fresh)
                    if new_auto is None:
                        skipped += 1
                        continue

                    result_content = _update_auto_block(existing, new_auto)
                    if result_content is None:
                        skipped += 1
                        continue

                    filepath.write_text(result_content, encoding="utf-8")
                    updated += 1

        finally:
            db.session.remove()
            db.engine.dispose()

    return RefreshResult(updated=updated, skipped=skipped, errors=errors)
