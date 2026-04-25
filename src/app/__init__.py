from dataclasses import asdict
from urllib.parse import urlparse
from flask import Flask, abort, redirect, render_template, request, jsonify, session, url_for
from datetime import datetime, timezone
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

from .imported_explorer import anchor_for_message, build_prompt_toc, format_timestamp
from .models.db import db
from ..config import Config, normalize_sqlite_uri
from ..runtime import default_instance_dir, static_dir, templates_dir
from .models import ImportedConversation, ImportedMessage, ImportRun, MemoryEntry
from .import_runs import classify_import_outcome, latest_import_runs, record_import_run
from .citation_handoff import build_answer_trace_citation_view
from .decorators import require_license
from .licensing import get_license_status, is_licensed
from .viewmodels import build_workspace_summary
from sqlalchemy import func
from ..importers.cli import import_conversation_export_to_sqlite
from ..importers.errors import (
    ImportProviderDetectionError,
    MalformedImportFileError,
    UnsupportedImportFormatError,
)
from ..passport import export_memory_passport, validate_memory_passport
from ..verify import quick_health_summary


def federated_search(*args, **kwargs):
    """Lazy import wrapper to avoid retrieval/app circular imports."""

    from ..retrieval.federated import federated_search as _federated_search

    return _federated_search(*args, **kwargs)


def _relative_time_from_unix(unix_ts) -> str:
    """Short relative-time label for a unix seconds timestamp."""

    if unix_ts is None:
        return ""
    try:
        ts = float(unix_ts)
    except (TypeError, ValueError):
        return ""

    now = datetime.now(timezone.utc).timestamp()
    diff = int(now - ts)
    if diff < 0:
        return "just now"
    if diff < 60:
        return "just now"
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    if diff < 2592000:
        return f"{diff // 86400}d ago"
    if diff < 31536000:
        return f"{diff // 2592000}mo ago"
    return f"{diff // 31536000}y ago"


def _memory_timestamp_to_unix(entry: MemoryEntry) -> float | None:
    """Normalize native memory timestamps for UI display."""

    if entry.timestamp is None:
        return None

    timestamp = entry.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return timestamp.timestamp()


def format_handoff_briefing(distilled_text: str, conversation_count: int,
                            date_range: str | None) -> str:
    """Reformat distill output as an AI-consumable handoff briefing.

    Parses markdown headings from distilled_text to extract known sections,
    then assembles a compact briefing designed for pasting into a new AI chat.
    """
    lines: list[str] = ["## Context from SoulPrint", ""]

    span = date_range or "an unknown period"
    lines.append(
        f"I'm continuing a thread that spans {conversation_count} "
        f"conversations over {span}."
    )
    lines.append("")

    # Parse sections from markdown by ## headings
    sections: dict[str, str] = {}
    raw = distilled_text.strip()
    if "\n## " in raw or raw.startswith("## "):
        parts = raw.split("\n## ")
        for i, part in enumerate(parts):
            if i == 0 and not raw.startswith("## "):
                sections["_preamble"] = part.strip()
            else:
                heading, _, body = part.partition("\n")
                key = heading.strip().lstrip("#").strip().lower()
                sections[key] = body.strip()

    # Decisions
    for key in ("decisions", "decisions made"):
        if key in sections and sections[key]:
            lines.append("**Decisions made:**")
            lines.append(sections[key])
            lines.append("")
            break

    # Open loops
    for key in ("open loops", "open questions", "unresolved"):
        if key in sections and sections[key]:
            lines.append("**Open loops:**")
            lines.append(sections[key])
            lines.append("")
            break

    # Key context from summary
    for key in ("summary", "executive summary", "key context", "context"):
        if key in sections and sections[key]:
            lines.append("**Key context:**")
            summary_lines = sections[key].split("\n")
            lines.append("\n".join(summary_lines[:4]))
            lines.append("")
            break

    # Where I left off — from evolution/thinking section
    for key in ("how thinking evolved", "evolution", "thinking evolved",
                "trajectory", "where things stand"):
        if key in sections and sections[key]:
            lines.append("**Where I left off:**")
            paragraphs = [p.strip() for p in sections[key].split("\n\n") if p.strip()]
            if paragraphs:
                lines.append(paragraphs[-1])
            lines.append("")
            break

    # Fallback: if no sections were matched, include the full text
    if len(lines) <= 4:  # only header + count + blanks
        lines.append(raw)
        lines.append("")

    lines.append("---")
    lines.append("Please continue from this context.")

    return "\n".join(lines)


def _native_memory_entry_id(stable_id: str) -> int | None:
    """Extract the canonical entry id from a native-memory stable id."""

    prefix = "memory:"
    if not stable_id.startswith(prefix):
        return None

    entry_id = stable_id.removeprefix(prefix)
    if not entry_id.isdigit():
        return None

    return int(entry_id)


def _sqlite_path_from_uri(sqlite_uri: str) -> str:
    """Resolve an absolute SQLite file path from app config URI."""

    return sqlite_uri.removeprefix("sqlite:///")


def _extract_loop_texts(artifact: dict) -> list[str]:
    """Extract individual loop text strings from a continuity open_loops artifact.

    Prefers content_json['open_loops'] list; falls back to parsing content_text lines.
    """
    content_json = artifact.get("content_json")
    if content_json and isinstance(content_json, dict):
        loops = content_json.get("open_loops", [])
        if loops:
            return [str(t).strip() for t in loops if str(t).strip()]
    text = artifact.get("content_text", "")
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for prefix in ("- ", "* ", "• ", "– "):
            if line.startswith(prefix):
                line = line[len(prefix):]
                break
        if line:
            lines.append(line)
    return lines


def _resolve_open_loop_conversation(source_ids: list[str]) -> dict:
    """Resolve the first valid imported_conversation stable ID to display info.

    Returns a dict with id, title, source, explorer_url, continuity_url.
    Falls back gracefully when no stable ID resolves to a live conversation.
    """
    prefix = "imported_conversation:"
    for sid in source_ids:
        if not sid.startswith(prefix):
            continue
        raw_id = sid.removeprefix(prefix)
        if not raw_id.isdigit():
            continue
        conv = ImportedConversation.query.get(int(raw_id))
        if conv is None:
            continue
        return {
            "id": conv.id,
            "title": conv.title or "Untitled conversation",
            "source": conv.source,
            "explorer_url": f"/imported/{conv.id}/explorer",
            "continuity_url": f"/intelligence/continuity/{conv.id}",
        }
    stable_text = source_ids[0] if source_ids else ""
    return {
        "id": None,
        "title": stable_text or "Unknown conversation",
        "source": "",
        "explorer_url": None,
        "continuity_url": None,
    }


def render_conversation_markdown(conversation, messages) -> tuple[str, str]:
    """Return (markdown_content, safe_filename) for a conversation + messages."""

    lines = []
    title = conversation.title or "Untitled conversation"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Provider:** {conversation.source}")
    lines.append(f"**Created:** {format_timestamp(conversation.created_at_unix)}")
    lines.append(f"**Updated:** {format_timestamp(conversation.updated_at_unix)}")
    lines.append(f"**Messages:** {len(messages)}")
    lines.append(f"**Exported from:** SoulPrint")
    lines.append("")
    lines.append("---")
    lines.append("")

    for msg in messages:
        role_label = msg.role.capitalize() if msg.role else "Unknown"
        ts = format_timestamp(msg.created_at_unix) if msg.created_at_unix is not None else ""
        lines.append(f"### {role_label}")
        if ts:
            lines.append(f"*{ts}*")
        lines.append("")
        lines.append(msg.content or "")
        lines.append("")
        lines.append("---")
        lines.append("")

    content = "\n".join(lines)
    safe_title = "".join(c if c.isascii() and (c.isalnum() or c in " -_.") else "" for c in title)[:60].strip()
    filename = f"{safe_title or 'conversation'}.md"
    return content, filename


def _pick_unique_filename(base: str, conv_id: int, taken) -> str:
    """Return base, or a disambiguated variant that `taken(name)` rejects.

    First tries `<stem>-<conv_id>.<ext>`, then `<stem>-<conv_id>-<n>.<ext>`
    for n = 2, 3, … until an unused name is found. Safe against the case
    where the first-try suffix happens to collide with another batch entry
    whose title already contained the same id suffix.
    """

    if not taken(base):
        return base
    stem, _, ext = base.rpartition(".")
    ext = ext or "md"
    stem = stem or base
    candidate = f"{stem}-{conv_id}.{ext}"
    if not taken(candidate):
        return candidate
    n = 2
    while True:
        candidate = f"{stem}-{conv_id}-{n}.{ext}"
        if not taken(candidate):
            return candidate
        n += 1


def _atomic_write_text(target: Path, content: str) -> None:
    """Write *content* to *target* via a ``.tmp`` sibling + atomic rename.

    On OSError anywhere in the write/rename, best-effort-unlink the tmp
    and re-raise. An existing file at *target* is preserved on failure
    because the rename is the commit step.
    """
    tmp = target.with_suffix(target.suffix + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
    except OSError:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass  # best-effort cleanup; don't mask the original error
        raise


def create_app():
    instance_dir = default_instance_dir()
    app = Flask(
        __name__,
        template_folder=str(templates_dir()),
        static_folder=str(static_dir()),
        instance_path=str(instance_dir),
    )
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_sqlite_uri(
        app.config.get("SQLALCHEMY_DATABASE_URI", "")
    )

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # One-time column guard for existing databases (no migration framework in use)
    import sqlite3 as _sqlite3
    _guard_path = _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"])
    try:
        _gc = _sqlite3.connect(_guard_path)
        _cols = {r[1] for r in _gc.execute("PRAGMA table_info(imported_conversation)")}
        if "is_archived" not in _cols:
            _gc.execute(
                "ALTER TABLE imported_conversation ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0"
            )
            _gc.commit()
        if "source_metadata_json" not in _cols:
            _gc.execute(
                "ALTER TABLE imported_conversation ADD COLUMN source_metadata_json TEXT"
            )
            _gc.commit()
        if "is_starred" not in _cols:
            _gc.execute(
                "ALTER TABLE imported_conversation ADD COLUMN is_starred BOOLEAN NOT NULL DEFAULT 0"
            )
            _gc.commit()
        if "tags" not in _cols:
            _gc.execute(
                "ALTER TABLE imported_conversation ADD COLUMN tags VARCHAR NOT NULL DEFAULT ''"
            )
            _gc.commit()
        _mcols = {r[1] for r in _gc.execute("PRAGMA table_info(memory_entry)")}
        if "is_starred" not in _mcols:
            _gc.execute(
                "ALTER TABLE memory_entry ADD COLUMN is_starred BOOLEAN NOT NULL DEFAULT 0"
            )
            _gc.commit()
        _gc.close()
    except Exception:
        pass

    # Create FTS5 virtual tables (derived indexes, not canonical)
    try:
        from ..retrieval.fts import ensure_fts_tables

        ensure_fts_tables(_sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"]))
    except Exception:
        logger.warning("FTS indexing failed", exc_info=True)

    # Jinja filters
    @app.template_filter("format_ts")
    def _format_ts(unix_ts):
        """Render a unix timestamp as 'Mar 27, 2026'."""
        if unix_ts is None:
            return ""
        from datetime import datetime, timezone

        dt = datetime.fromtimestamp(float(unix_ts), tz=timezone.utc)
        return dt.strftime("%b %d, %Y").replace(" 0", " ")

    @app.template_filter("relative_time")
    def _relative_time(unix_ts):
        """Render a unix timestamp as a short relative string ('2h ago', '3d ago')."""
        return _relative_time_from_unix(unix_ts)

    @app.template_filter("provider_display_name")
    def _provider_display_name(slug: str) -> str:
        from ..importers.contracts import PROVIDER_DISPLAY_NAMES
        return PROVIDER_DISPLAY_NAMES.get(slug, (slug or "").capitalize())

    @app.get("/")
    def home():
        from ..answering.trace import default_trace_store_path
        from ..intelligence.store import default_distillation_store_path, list_distillations
        import json as _json
        from pathlib import Path as _Path

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        db_path = _sqlite_path_from_uri(sqlite_uri)
        trace_store = default_trace_store_path(db_path)
        workspace = build_workspace_summary(trace_store_path=trace_store)

        # distill_count — limit=10_000 so the display reflects reality for large archives
        _distill_recs = list_distillations(default_distillation_store_path(db_path), limit=10_000)
        distill_count = len(_distill_recs)

        # last_passport_date (YYYY-MM-DD or None)
        _passport_manifest = _Path(db_path).parent / "exports" / "passports" / "memory-passport-v1" / "manifest.json"
        last_passport_date = None
        if _passport_manifest.exists():
            try:
                with open(_passport_manifest) as _f:
                    last_passport_date = _json.load(_f).get("created_at", "")[:10]
            except (_json.JSONDecodeError, OSError, ValueError):
                logger.warning("Could not parse passport manifest", exc_info=True)

        # Greeting: time-of-day from local system clock
        _hour = datetime.now().hour
        time_of_day = "morning" if _hour < 12 else "afternoon" if _hour < 18 else "evening"

        # Recent conversations (across providers): shape workspace.recent_imported
        # into the template contract (id/title/provider/relative_time).
        recent_conversations = [
            {
                "id": row["id"],
                "title": row.get("title") or "Untitled",
                "provider": row.get("source", ""),
                "relative_time": _relative_time_from_unix(
                    row.get("updated_at_unix") or row.get("created_at_unix")
                ),
            }
            for row in workspace.recent_imported
        ]

        license_status = get_license_status(instance_dir=app.instance_path)
        health_summary = quick_health_summary(Path(db_path))
        _badge_labels = {
            "healthy": "Archive available",
            "needs_attention": "Needs attention",
            "unknown": "No archive yet",
        }
        badge_label = _badge_labels.get(health_summary["state"], "Unknown")
        return render_template(
            "index.html",
            workspace=workspace,
            license_status=license_status,
            distill_count=distill_count,
            last_passport_date=last_passport_date,
            time_of_day=time_of_day,
            recent_conversations=recent_conversations,
            health_summary=health_summary,
            badge_label=badge_label,
        )

    @app.get("/archive/health")
    def archive_health():
        from ..verify import verify_archive
        from .import_runs import last_import_run_per_provider
        from ..importers.contracts import PROVIDER_DISPLAY_NAMES

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        db_path = _sqlite_path_from_uri(sqlite_uri)

        verify_result = verify_archive(Path(db_path))
        provider_runs = last_import_run_per_provider()

        return render_template(
            "archive_health.html",
            verify=verify_result,
            provider_runs=provider_runs,
            provider_ids=list(PROVIDER_DISPLAY_NAMES.keys()),
            format_timestamp=format_timestamp,
            db_path=db_path,
            provider_counts=verify_result["counts"].get("providers", {}),
        )

    @app.get("/passport")
    def passport_surface():
        capability = {
            "export_available": callable(export_memory_passport),
            "validation_available": callable(validate_memory_passport),
        }

        status = {
            "inspection_available": False,
            "artifact_detected": False,
            "message": (
                "Export and validation capabilities are available through the existing "
                "CLI surface. No specific passport artifact is currently being "
                "inspected in the web app."
            ),
        }

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        db_path = _sqlite_path_from_uri(sqlite_uri)

        return render_template(
            "passport.html",
            capability=capability,
            status=status,
            db_path=db_path,
        )

    def _passport_output_dir() -> Path:
        """Resolve passport export directory as a sibling of the SQLite file."""
        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        db_dir = Path(_sqlite_path_from_uri(sqlite_uri)).parent
        return db_dir / "exports" / "passports"

    @app.post("/passport/export")
    def passport_export():
        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_path = _sqlite_path_from_uri(sqlite_uri)
        output_dir = _passport_output_dir()

        try:
            result = export_memory_passport(
                sqlite_path=sqlite_path,
                output_dir=str(output_dir),
            )
            return jsonify({
                "status": "ok",
                "path": str(result.package_dir),
                "canonical_units": result.canonical_units,
                "derived_units": result.derived_units,
            })
        except Exception as exc:
            logger.exception("Passport export failed")
            return jsonify({"status": "error", "message": "Export failed"}), 500

    @app.post("/passport/validate")
    def passport_validate():
        output_dir = _passport_output_dir()
        passport_dir = output_dir / "memory-passport-v1"

        if not passport_dir.exists() or not (passport_dir / "manifest.json").exists():
            return jsonify({
                "status": "error",
                "message": "No exported passport found. Export one first.",
            }), 404

        try:
            result = validate_memory_passport(str(passport_dir))
            return jsonify({
                "status": "ok",
                "valid": result.status != "invalid",
                "validation_status": result.status,
                "summary": _format_validation_summary(result),
                "issues": [d.message for d in result.errors] + [d.message for d in result.warnings],
                "checked_counts": result.checked_counts,
            })
        except Exception as exc:
            logger.exception("Passport validation failed")
            return jsonify({"status": "error", "message": "Validation failed"}), 500

    def _format_validation_summary(result) -> str:
        """Build a human-readable one-line validation summary."""
        parts = [f"Status: {result.status}"]
        if result.checked_counts:
            counts = ", ".join(
                f"{k}: {v}" for k, v in sorted(result.checked_counts.items())
            )
            parts.append(f"Checked: {counts}")
        if result.errors:
            parts.append(f"{len(result.errors)} error(s)")
        if result.warnings:
            parts.append(f"{len(result.warnings)} warning(s)")
        return " · ".join(parts)

    @app.post("/save")
    def save():
        data = request.get_json(force=True) or {}

        role = data.get("role", "user")
        content = data.get("content", "")
        tags = data.get("tags", "")

        if not content.strip():
            return jsonify({"ok": False, "error": "content is required"}), 400

        entry = MemoryEntry(
            timestamp=datetime.utcnow(),
            role=role,
            content=content,
            tags=tags,
        )
        db.session.add(entry)
        db.session.commit()

        try:
            from ..retrieval.fts import index_new_note

            index_new_note(
                _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"]),
                entry.id,
            )
        except Exception:
            logger.warning("FTS indexing failed", exc_info=True)

        return jsonify({"ok": True, "id": entry.id})

    @app.post("/api/clip")
    def api_clip():
        data = request.get_json(force=True) or {}

        content = data.get("content", "").strip()
        source_conversation_id = data.get("source_conversation_id")
        source_conversation_title = data.get("source_conversation_title", "Untitled")
        source_provider = data.get("source_provider", "")
        source_message_index = data.get("source_message_index")

        if not content:
            return jsonify({"status": "error", "message": "content is required"}), 400
        if source_conversation_id is None:
            return jsonify({"status": "error", "message": "source_conversation_id is required"}), 400

        # Build citation block
        citation_parts = [
            content,
            "",
            "---",
            f'Clipped from "{source_conversation_title}" \u00b7 {source_provider} \u00b7 message {source_message_index}',
            f"Source: /imported/{source_conversation_id}/explorer#msg-{source_message_index}",
        ]
        full_content = "\n".join(citation_parts)

        entry = MemoryEntry(
            timestamp=datetime.utcnow(),
            role="user",
            content=full_content,
            tags="clipped",
        )
        db.session.add(entry)
        db.session.commit()

        try:
            from ..retrieval.fts import index_new_note

            index_new_note(
                _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"]),
                entry.id,
            )
        except Exception:
            logger.warning("FTS indexing failed", exc_info=True)

        return jsonify({"status": "ok", "note_id": entry.id})

    @app.get("/imported/<int:conversation_id>/explorer")
    def imported_explorer(conversation_id: int):
        from ..intelligence.continuity.lineage import ConversationSummary, suggest_lineage
        from ..intelligence.provider import is_llm_configured

        conversation = ImportedConversation.query.filter_by(id=conversation_id).first_or_404()

        messages = sorted(conversation.messages, key=lambda m: m.sequence_index)
        toc_entries = build_prompt_toc(messages)

        # Lineage suggestions (derived, best-effort)
        other_convs = (
            ImportedConversation.query
            .filter(ImportedConversation.id != conversation_id)
            .order_by(ImportedConversation.id.desc())
            .limit(50)
            .all()
        )
        source_previews = [m.content for m in messages[:5]]
        source_summary = ConversationSummary(
            id=conversation.id,
            title=conversation.title or "",
            created_at_unix=conversation.created_at_unix,
            message_previews=source_previews,
        )
        candidate_summaries = [
            ConversationSummary(
                id=c.id,
                title=c.title or "",
                created_at_unix=c.created_at_unix,
                message_previews=[
                    m.content
                    for m in sorted(c.messages, key=lambda m: m.sequence_index)[:3]
                ],
            )
            for c in other_convs
        ]
        lineage_suggestions = suggest_lineage(source_summary, candidate_summaries, limit=3)

        return render_template(
            "imported_explorer.html",
            conversation=conversation,
            messages=messages,
            toc_entries=toc_entries,
            format_timestamp=format_timestamp,
            anchor_for_message=anchor_for_message,
            llm_configured=is_llm_configured(),
            licensed=is_licensed(instance_dir=app.instance_path),
            lineage_suggestions=lineage_suggestions,
        )

    @app.get("/imported/<int:conversation_id>/export")
    def export_conversation_markdown(conversation_id: int):
        """Export a single conversation.

        When SOULPRINT_EXPORT_DIR is set and points at a writable directory,
        write the .md there and redirect to /imported with a confirmation
        notice. Otherwise (or on filesystem write failure) serve a browser
        download.
        """
        from flask import Response

        conversation = ImportedConversation.query.get_or_404(conversation_id)
        messages = (
            ImportedMessage.query
            .filter_by(conversation_id=conversation_id)
            .order_by(ImportedMessage.sequence_index)
            .all()
        )

        content, filename = render_conversation_markdown(conversation, messages)

        export_dir = app.config.get("SOULPRINT_EXPORT_DIR", "") or ""
        dest = Path(export_dir).resolve() if export_dir else None

        if dest is not None and dest.is_dir():
            try:
                name = _pick_unique_filename(
                    filename,
                    conversation.id,
                    lambda n: (dest / n).exists(),
                )
                _atomic_write_text(dest / name, content)
            except OSError as exc:
                app.logger.warning(
                    "Single-conv export to %s failed: %s. Falling back to download.",
                    dest, exc,
                )
            else:
                session["export_notice"] = (
                    f"Exported '{conversation.title or 'Untitled conversation'}' "
                    f"to {dest / name}"
                )
                return redirect(url_for("imported_conversations"))

        return Response(
            content,
            mimetype="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/imported/export-selected")
    def export_selected_conversations():
        """Export multiple conversations as markdown — to a configured
        directory when SOULPRINT_EXPORT_DIR is set, otherwise as a zip."""
        import io
        import zipfile
        from flask import Response

        raw_ids = request.form.getlist("conversation_ids")
        ids: list[int] = []
        for raw in raw_ids:
            try:
                ids.append(int(raw))
            except (TypeError, ValueError):
                continue

        if not ids:
            session["export_error"] = "No conversations selected."
            return redirect(url_for("imported_conversations"))

        conversations = (
            ImportedConversation.query
            .filter(ImportedConversation.id.in_(ids))
            .all()
        )

        if not conversations:
            session["export_error"] = "No conversations selected."
            return redirect(url_for("imported_conversations"))

        rendered: list[tuple[int, str, str]] = []
        for conversation in conversations:
            messages = (
                ImportedMessage.query
                .filter_by(conversation_id=conversation.id)
                .order_by(ImportedMessage.sequence_index)
                .all()
            )
            content, base_filename = render_conversation_markdown(conversation, messages)
            rendered.append((conversation.id, content, base_filename))

        export_dir = app.config.get("SOULPRINT_EXPORT_DIR", "") or ""
        dest = Path(export_dir).resolve() if export_dir else None

        if dest is not None and dest.is_dir():
            used: set[str] = set()
            written = 0
            try:
                for conv_id, content, base_filename in rendered:
                    name = _pick_unique_filename(
                        base_filename,
                        conv_id,
                        lambda n: n in used or (dest / n).exists(),
                    )
                    _atomic_write_text(dest / name, content)
                    used.add(name)
                    written += 1
            except OSError as exc:
                detail = (
                    f" {written} of {len(rendered)} conversations were written before the failure."
                    if written > 0
                    else ""
                )
                session["export_error"] = (
                    f"Failed to write to {dest}: {exc}."
                    f"{detail} Check that the path exists and is writable."
                )
                return redirect(url_for("imported_conversations"))
            session["export_notice"] = (
                f"Exported {len(rendered)} conversations to {dest}"
            )
            return redirect(url_for("imported_conversations"))

        zip_used: set[str] = set()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for conv_id, content, base_filename in rendered:
                name = _pick_unique_filename(
                    base_filename, conv_id, zip_used.__contains__
                )
                zf.writestr(name, content)
                zip_used.add(name)
        count = len(rendered)
        return Response(
            buf.getvalue(),
            mimetype="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="soulprint-export-{count}.zip"'
            },
        )

    @app.get("/imported")
    def imported_conversations():
        from ..importers.contracts import SUPPORTED_IMPORT_PROVIDERS

        PER_PAGE = 50
        keyword = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        provider = request.args.get("provider", "").strip().lower()
        if page < 1:
            page = 1

        if provider and provider not in SUPPORTED_IMPORT_PROVIDERS:
            provider = ""

        rows_query = (
            db.session.query(
                ImportedConversation,
                func.count(ImportedMessage.id).label("message_count"),
            )
            .outerjoin(ImportedConversation.messages)
            .filter(ImportedConversation.is_archived.is_(False))
            .group_by(ImportedConversation.id)
        )

        if provider:
            rows_query = rows_query.filter(ImportedConversation.source == provider)

        if keyword:
            pattern = f"%{keyword.lower()}%"
            rows_query = rows_query.filter(
                (func.lower(ImportedConversation.title).like(pattern))
                | ImportedConversation.messages.any(
                    func.lower(ImportedMessage.content).like(pattern)
                )
            )

        total = rows_query.count()
        total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        if page > total_pages:
            page = total_pages

        rows = (
            rows_query
            .order_by(ImportedConversation.id.desc())
            .offset((page - 1) * PER_PAGE)
            .limit(PER_PAGE)
            .all()
        )

        export_notice = session.pop("export_notice", None)
        export_error = session.pop("export_error", None)

        return render_template(
            "imported_list.html",
            rows=rows,
            keyword=keyword,
            provider=provider,
            format_timestamp=format_timestamp,
            page=page,
            total_pages=total_pages,
            total=total,
            export_notice=export_notice,
            export_error=export_error,
        )

    @app.route("/import", methods=["GET", "POST"])
    def import_conversations():
        error_message = None
        result = None

        if request.method == "POST":
            run_provider: str | None = None
            run_filename: str | None = None
            run_imported = 0
            run_messages_imported = 0
            run_skipped = 0
            run_failed = 0
            run_error_message: str | None = None
            run_reached_importer = False

            try:
                # Capture count before import for first-import redirect
                count_before = ImportedConversation.query.count()

                upload = request.files.get("export_file")
                if upload is None or upload.filename == "":
                    error_message = "Choose an export file before importing."
                    run_error_message = "No file submitted."
                else:
                    run_filename = upload.filename
                    temp_path: Path | None = None
                    try:
                        filename_lower = (upload.filename or "").lower()
                        if filename_lower.endswith(".zip"):
                            suffix = ".zip"
                        elif filename_lower.endswith(".jsonl"):
                            suffix = ".jsonl"
                        else:
                            suffix = ".json"
                        with tempfile.NamedTemporaryFile(
                            mode="wb",
                            suffix=suffix,
                            delete=False,
                        ) as handle:
                            upload.save(handle)
                            temp_path = Path(handle.name)

                        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
                        sqlite_path = _sqlite_path_from_uri(sqlite_uri)
                        import_result = import_conversation_export_to_sqlite(temp_path, sqlite_path)
                        run_reached_importer = True
                        run_provider = import_result.provider_id
                        run_imported = import_result.imported_conversations
                        run_messages_imported = import_result.imported_messages
                        run_skipped = import_result.skipped_conversations

                        # First import: redirect to summary page
                        if count_before == 0 and import_result.imported_conversations > 0:
                            return redirect(url_for("summary"))

                        # New conversations arrived → flash page
                        if import_result.imported_conversations > 0:
                            session["import_stats"] = {
                                "messages_imported": import_result.imported_messages,
                                "conversations_imported": import_result.imported_conversations,
                                "provider_name": import_result.provider_id,
                            }
                            return redirect(url_for("import_complete"))

                        # All duplicates — show inline feedback on import page
                        result = {
                            "provider_id": import_result.provider_id,
                            "imported_conversations": import_result.imported_conversations,
                            "skipped_conversations": import_result.skipped_conversations,
                            "imported_messages": import_result.imported_messages,
                            "warnings": import_result.warnings,
                            "show_summary_link": False,
                        }
                    except ImportProviderDetectionError:
                        error_message = (
                            "We could not recognize this export format. Supported imports are ChatGPT, Claude, Claude Code, Gemini, and Grok conversation exports."
                        )
                        run_error_message = "Unrecognized export format."
                    except UnsupportedImportFormatError as exc:
                        error_message = f"This export format is not supported yet: {exc}"
                        run_error_message = str(exc)
                    except MalformedImportFileError as exc:
                        error_message = str(exc)
                        run_error_message = str(exc)
                    except Exception as exc:
                        run_error_message = f"unexpected: {exc}"
                        raise
                    finally:
                        if temp_path is not None and temp_path.exists():
                            temp_path.unlink()
            finally:
                status = classify_import_outcome(
                    run_imported, run_skipped, run_failed,
                    reached_importer=run_reached_importer,
                )
                record_import_run(
                    provider=run_provider,
                    filename=run_filename,
                    status=status,
                    conversations_imported=run_imported,
                    messages_imported=run_messages_imported,
                    conversations_skipped=run_skipped,
                    conversations_failed=run_failed,
                    error_message=run_error_message,
                )

        return render_template(
            "import.html",
            error_message=error_message,
            result=result,
            recent_runs=latest_import_runs(limit=10),
            format_timestamp=format_timestamp,
        )

    @app.get("/import/complete")
    def import_complete():
        stats = session.pop("import_stats", None)
        if not stats:
            return redirect(url_for("import_conversations"))
        return render_template("import_flash.html", **stats)

    @app.get("/chats")
    def chats():
        tag = request.args.get("tag", "").strip()
        q = MemoryEntry.query.order_by(MemoryEntry.timestamp.desc())
        if tag:
            q = q.filter(MemoryEntry.tags.contains(tag))
        entries = q.limit(100).all()
        sq = (
            db.session.query(
                ImportedConversation,
                func.count(ImportedMessage.id).label("message_count"),
            )
            .outerjoin(ImportedConversation.messages)
            .filter(ImportedConversation.is_starred == True)  # noqa: E712
            .group_by(ImportedConversation.id)
            .order_by(ImportedConversation.updated_at_unix.desc())
        )
        if tag:
            sq = sq.filter(ImportedConversation.tags.contains(tag))
        starred_imports = sq.limit(100).all()
        return render_template(
            "view.html",
            entries=entries,
            starred_imports=starred_imports,
            format_timestamp=format_timestamp,
        )

    @app.get("/imported/<int:conv_id>/delete")
    def delete_imported_confirm(conv_id: int):
        from ..intelligence.store import (
            default_digest_store_path,
            default_distillation_store_path,
            default_summary_store_path,
            default_topic_store_path,
            list_digests_for_conversation,
            list_distillations_for_conversation,
            list_summaries_for_conversation,
            list_topic_scans_for_conversation,
        )
        from ..intelligence.continuity.store import (
            default_continuity_store_path,
            list_artifacts_for_conversation,
        )

        conversation = ImportedConversation.query.get_or_404(conv_id)
        stable_id = f"imported_conversation:{conv_id}"
        db_path = _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"])

        summaries = list_summaries_for_conversation(default_summary_store_path(db_path), stable_id)
        topic_scans = list_topic_scans_for_conversation(default_topic_store_path(db_path), stable_id)
        digests = list_digests_for_conversation(default_digest_store_path(db_path), stable_id)
        distillations = list_distillations_for_conversation(default_distillation_store_path(db_path), stable_id)
        continuity = list_artifacts_for_conversation(default_continuity_store_path(db_path), stable_id, limit=None)

        def _resolve_stable_ids(artifacts: list[dict]) -> dict[str, str]:
            all_ids: set[str] = set()
            for r in artifacts:
                all_ids.update(r.get("source_conversation_stable_ids", []))
            result: dict[str, str] = {}
            for sid in all_ids:
                parts = sid.split(":", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    conv = ImportedConversation.query.get(int(parts[1]))
                    result[sid] = conv.title or "Untitled" if conv else sid
                else:
                    result[sid] = sid
            return result

        digest_id_map = _resolve_stable_ids(digests)
        distillation_id_map = _resolve_stable_ids(distillations)

        raw_return = request.args.get("return_url", "")
        return_url = (
            raw_return
            if raw_return.startswith("/") and not raw_return.startswith("//")
            else url_for("imported_conversations")
        )

        return render_template(
            "imported_delete_confirm.html",
            conversation=conversation,
            stable_id=stable_id,
            summaries=summaries,
            topic_scans=topic_scans,
            digests=digests,
            distillations=distillations,
            continuity=continuity,
            digest_id_map=digest_id_map,
            distillation_id_map=distillation_id_map,
            format_timestamp=format_timestamp,
            return_url=return_url,
        )

    @app.post("/imported/<int:conv_id>/delete")
    def delete_imported_conversation(conv_id: int):
        from ..intelligence.store import (
            default_digest_store_path,
            default_distillation_store_path,
            default_summary_store_path,
            default_topic_store_path,
            delete_digests_for_conversation,
            delete_distillations_for_conversation,
            delete_summaries_for_conversation,
            delete_topic_scans_for_conversation,
        )
        from ..intelligence.continuity.store import (
            default_continuity_store_path,
            delete_artifacts_for_conversation,
        )
        from ..retrieval.fts import remove_conversation_from_fts

        conversation = ImportedConversation.query.get_or_404(conv_id)
        stable_id = f"imported_conversation:{conv_id}"
        title = conversation.title or "Untitled conversation"
        db_path = _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"])

        s = delete_summaries_for_conversation(default_summary_store_path(db_path), stable_id)
        t = delete_topic_scans_for_conversation(default_topic_store_path(db_path), stable_id)
        d = delete_digests_for_conversation(default_digest_store_path(db_path), stable_id)
        x = delete_distillations_for_conversation(default_distillation_store_path(db_path), stable_id)
        c = delete_artifacts_for_conversation(default_continuity_store_path(db_path), stable_id)

        db.session.delete(conversation)
        db.session.commit()

        try:
            remove_conversation_from_fts(db_path, conv_id)
        except Exception:
            pass

        session["export_notice"] = (
            f"Deleted conversation '{title}' and {s} summaries, {t} topic scans, "
            f"{d} digests, {x} distillations, {c} continuity artifacts."
        )
        return redirect(url_for("imported_conversations"))

    @app.post("/imported/<int:conv_id>/archive")
    def archive_imported_conversation(conv_id: int):
        conv = ImportedConversation.query.get_or_404(conv_id)
        if not conv.is_archived:
            conv.is_archived = True
            db.session.commit()
        session["export_notice"] = f"Archived '{conv.title or '(untitled)'}'."
        return redirect(url_for("imported_conversations"))

    @app.post("/imported/<int:conv_id>/unarchive")
    def unarchive_imported_conversation(conv_id: int):
        conv = ImportedConversation.query.get_or_404(conv_id)
        if conv.is_archived:
            conv.is_archived = False
            db.session.commit()
        session["export_notice"] = f"Restored '{conv.title or '(untitled)'}'."
        return redirect(url_for("imported_archived_conversations"))

    @app.post("/imported/<int:conv_id>/star")
    def star_imported_conversation(conv_id: int):
        conv = ImportedConversation.query.get_or_404(conv_id)
        if not conv.is_starred:
            conv.is_starred = True
            db.session.commit()
        session["export_notice"] = f"Starred '{conv.title or '(untitled)'}'."
        nxt = request.form.get("next", "")
        nxt = nxt.replace("\\", "")
        if nxt and not urlparse(nxt).netloc and not urlparse(nxt).scheme:
            return redirect(nxt)
        return redirect(url_for("federated_browser"))

    @app.post("/imported/<int:conv_id>/unstar")
    def unstar_imported_conversation(conv_id: int):
        conv = ImportedConversation.query.get_or_404(conv_id)
        if conv.is_starred:
            conv.is_starred = False
            db.session.commit()
        session["export_notice"] = f"Unstarred '{conv.title or '(untitled)'}'."
        nxt = request.form.get("next", "")
        nxt = nxt.replace("\\", "")
        if nxt and not urlparse(nxt).netloc and not urlparse(nxt).scheme:
            return redirect(nxt)
        return redirect(url_for("federated_browser"))

    @app.post("/memory/<int:memory_id>/star")
    def star_memory(memory_id: int):
        entry = MemoryEntry.query.get_or_404(memory_id)
        if not entry.is_starred:
            entry.is_starred = True
            db.session.commit()
        session["export_notice"] = "Starred note."
        nxt = request.form.get("next", "")
        nxt = nxt.replace("\\", "")
        if nxt and not urlparse(nxt).netloc and not urlparse(nxt).scheme:
            return redirect(nxt)
        return redirect(url_for("chats"))

    @app.post("/memory/<int:memory_id>/unstar")
    def unstar_memory(memory_id: int):
        entry = MemoryEntry.query.get_or_404(memory_id)
        if entry.is_starred:
            entry.is_starred = False
            db.session.commit()
        session["export_notice"] = "Unstarred note."
        nxt = request.form.get("next", "")
        nxt = nxt.replace("\\", "")
        if nxt and not urlparse(nxt).netloc and not urlparse(nxt).scheme:
            return redirect(nxt)
        return redirect(url_for("chats"))

    @app.post("/imported/<int:conv_id>/tags/add")
    def add_imported_conversation_tag(conv_id: int):
        from .tags import normalize_tag_string
        conv = ImportedConversation.query.get_or_404(conv_id)
        raw_new = request.form.get("tag", "")
        normalized_new = normalize_tag_string(raw_new)
        if normalized_new:
            combined = f"{conv.tags}, {normalized_new}" if conv.tags else normalized_new
            conv.tags = normalize_tag_string(combined)
            db.session.commit()
        nxt = request.form.get("next", "")
        nxt = nxt.replace("\\", "")
        if nxt and not urlparse(nxt).netloc and not urlparse(nxt).scheme:
            return redirect(nxt)
        return redirect(url_for("imported_conversations"))

    @app.post("/imported/<int:conv_id>/tags/remove/<path:tag>")
    def remove_imported_conversation_tag(conv_id: int, tag: str):
        from .tags import normalize_tag_string
        conv = ImportedConversation.query.get_or_404(conv_id)
        target = normalize_tag_string(tag)
        if conv.tags and target:
            current = [t.strip() for t in conv.tags.split(",") if t.strip()]
            new_tags = [t for t in current if t != target]
            conv.tags = normalize_tag_string(", ".join(new_tags))
            db.session.commit()
        nxt = request.form.get("next", "")
        nxt = nxt.replace("\\", "")
        if nxt and not urlparse(nxt).netloc and not urlparse(nxt).scheme:
            return redirect(nxt)
        return redirect(url_for("imported_conversations"))

    @app.get("/imported/archived")
    def imported_archived_conversations():
        from ..importers.contracts import SUPPORTED_IMPORT_PROVIDERS

        PER_PAGE = 50
        keyword = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        provider = request.args.get("provider", "").strip().lower()
        if page < 1:
            page = 1

        if provider and provider not in SUPPORTED_IMPORT_PROVIDERS:
            provider = ""

        rows_query = (
            db.session.query(
                ImportedConversation,
                func.count(ImportedMessage.id).label("message_count"),
            )
            .outerjoin(ImportedConversation.messages)
            .filter(ImportedConversation.is_archived.is_(True))
            .group_by(ImportedConversation.id)
        )

        if provider:
            rows_query = rows_query.filter(ImportedConversation.source == provider)

        if keyword:
            pattern = f"%{keyword.lower()}%"
            rows_query = rows_query.filter(
                (func.lower(ImportedConversation.title).like(pattern))
                | ImportedConversation.messages.any(
                    func.lower(ImportedMessage.content).like(pattern)
                )
            )

        total = rows_query.count()
        total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        if page > total_pages:
            page = total_pages

        rows = (
            rows_query
            .order_by(ImportedConversation.id.desc())
            .offset((page - 1) * PER_PAGE)
            .limit(PER_PAGE)
            .all()
        )

        export_notice = session.pop("export_notice", None)
        export_error = session.pop("export_error", None)

        return render_template(
            "imported_archived.html",
            rows=rows,
            keyword=keyword,
            provider=provider,
            format_timestamp=format_timestamp,
            page=page,
            total_pages=total_pages,
            total=total,
            export_notice=export_notice,
            export_error=export_error,
        )

    @app.post("/imported/delete-selected")
    def delete_selected_imported_confirm():
        raw_ids = request.form.getlist("conversation_ids")
        ids: list[int] = [int(r) for r in raw_ids if r.isdigit()]
        if not ids:
            session["export_error"] = "No conversations selected."
            return redirect(url_for("imported_conversations"))

        conversations = ImportedConversation.query.filter(ImportedConversation.id.in_(ids)).all()
        if not conversations:
            session["export_error"] = "No conversations selected."
            return redirect(url_for("imported_conversations"))

        from ..intelligence.store import (
            default_digest_store_path,
            default_distillation_store_path,
            default_summary_store_path,
            default_topic_store_path,
            list_digests,
            list_distillations,
            list_summaries,
            list_topic_scans,
        )
        from ..intelligence.continuity.store import (
            default_continuity_store_path,
            list_artifacts,
        )

        db_path = _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"])

        # Load each store once; filter per conversation in memory to avoid N×full-file scans.
        all_summaries = list_summaries(default_summary_store_path(db_path), limit=9999)
        all_topic_scans = list_topic_scans(default_topic_store_path(db_path), limit=9999)
        all_digests = list_digests(default_digest_store_path(db_path), limit=9999)
        all_distillations = list_distillations(default_distillation_store_path(db_path), limit=9999)
        all_artifacts = list_artifacts(default_continuity_store_path(db_path), limit=9999)

        rows = []
        for conv in conversations:
            sid = f"imported_conversation:{conv.id}"
            rows.append({
                "id": conv.id,
                "title": conv.title or "(untitled)",
                "provider": conv.source,
                "created_at_unix": conv.created_at_unix,
                "summary_count": sum(1 for r in all_summaries if r.get("source_conversation_stable_id") == sid),
                "topic_scan_count": sum(
                    1 for r in all_topic_scans
                    if any(sid in c.get("conversation_stable_ids", []) for c in r.get("clusters", []))
                ),
                "digest_count": sum(1 for r in all_digests if sid in r.get("source_conversation_stable_ids", [])),
                "distillation_count": sum(1 for r in all_distillations if sid in r.get("source_conversation_stable_ids", [])),
                "continuity_count": sum(1 for r in all_artifacts if sid in r.get("source_conversation_ids", [])),
            })

        return render_template("imported_bulk_delete_confirm.html", rows=rows, ids=ids)

    @app.post("/imported/delete-selected/execute")
    def delete_selected_imported_execute():
        raw_ids = request.form.getlist("conversation_ids")
        ids: list[int] = [int(r) for r in raw_ids if r.isdigit()]
        if not ids:
            session["export_error"] = "No conversations selected."
            return redirect(url_for("imported_conversations"))

        from ..intelligence.store import (
            default_digest_store_path,
            default_distillation_store_path,
            default_summary_store_path,
            default_topic_store_path,
            delete_digests_for_conversation,
            delete_distillations_for_conversation,
            delete_summaries_for_conversation,
            delete_topic_scans_for_conversation,
        )
        from ..intelligence.continuity.store import (
            default_continuity_store_path,
            delete_artifacts_for_conversation,
        )
        from ..retrieval.fts import remove_conversation_from_fts

        db_path = _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"])
        deleted_titles: list[str] = []
        failed_titles: list[str] = []

        for conv_id in ids:
            conv = ImportedConversation.query.get(conv_id)
            if conv is None:
                continue
            sid = f"imported_conversation:{conv.id}"
            title = conv.title or "(untitled)"
            # DB delete is the only hard-fail step. If it succeeds, the canonical
            # record is gone; JSONL + FTS cleanup are best-effort so orphan artifacts
            # never prevent reporting the conversation as deleted.
            try:
                db.session.delete(conv)
                db.session.commit()
            except Exception:
                db.session.rollback()
                failed_titles.append(title)
                continue
            try:
                delete_summaries_for_conversation(default_summary_store_path(db_path), sid)
                delete_topic_scans_for_conversation(default_topic_store_path(db_path), sid)
                delete_digests_for_conversation(default_digest_store_path(db_path), sid)
                delete_distillations_for_conversation(default_distillation_store_path(db_path), sid)
                delete_artifacts_for_conversation(default_continuity_store_path(db_path), sid)
            except Exception:
                pass
            try:
                remove_conversation_from_fts(db_path, conv_id)
            except Exception:
                pass
            deleted_titles.append(title)

        parts = []
        if deleted_titles:
            n = len(deleted_titles)
            parts.append(f"Deleted {n} conversation{'s' if n != 1 else ''}.")
        if failed_titles:
            parts.append(f"Failed: {', '.join(failed_titles)}.")
        session["export_notice"] = " ".join(parts) if parts else "No conversations deleted."
        return redirect(url_for("imported_conversations"))

    @app.post("/memory/<int:memory_id>/delete")
    def delete_memory(memory_id: int):
        entry = MemoryEntry.query.get_or_404(memory_id)
        db.session.delete(entry)
        db.session.commit()
        try:
            from ..retrieval.fts import remove_note_from_fts
            remove_note_from_fts(_sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"]), memory_id)
        except Exception:
            pass
        return redirect(url_for("chats"))

    @app.get("/memory/<int:entry_id>")
    def memory_detail(entry_id: int):
        entry = MemoryEntry.query.filter_by(id=entry_id).first_or_404()
        federated_query = request.args.get("q", "").strip()
        came_from_federated = request.args.get("from", "").strip() == "federated"
        federated_href = None
        if came_from_federated:
            federated_href = url_for("federated_browser", q=federated_query)

        return render_template(
            "memory_detail.html",
            entry=entry,
            stable_id=f"memory:{entry.id}",
            timestamp_label=format_timestamp(_memory_timestamp_to_unix(entry)),
            federated_href=federated_href,
        )

    @app.get("/federated")
    def federated_browser():
        keyword = request.args.get("q", "").strip()
        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_path = _sqlite_path_from_uri(sqlite_uri)

        archaeology_mode = request.args.get("mode") == "archaeology"
        sort_param = request.args.get("sort", "relevance")
        if sort_param not in ("relevance", "newest", "oldest"):
            sort_param = "relevance"
        if archaeology_mode:
            sort_param = "oldest"
            fts_limit = 1
        else:
            fts_limit = 50

        # Try FTS5 message-level search when a keyword is present
        fts_results: list[dict] = []
        if keyword:
            try:
                from ..retrieval.fts import sanitize_fts_query, search_fts

                fts_query = sanitize_fts_query(keyword)
                if fts_query:
                    fts_results = search_fts(sqlite_path, fts_query, sort=sort_param, limit=fts_limit)
            except Exception:
                logger.warning("FTS indexing failed", exc_info=True)
                fts_results = []

        callout = None
        if len(fts_results) > 1 and not archaeology_mode:
            oldest = min(fts_results, key=lambda r: r.get("timestamp") or "9999-12-31T23:59:59Z")
            ts_str = oldest.get("timestamp") or ""
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                ts_unix = dt.timestamp()
                relative = _relative_time_from_unix(ts_unix)
                absolute = dt.strftime("%B %d, %Y").replace(" 0", " ")
            except (ValueError, AttributeError):
                relative = ""
                absolute = ts_str
            callout = {
                "relative_date": relative,
                "absolute_date": absolute,
                "provider": oldest.get("provider", ""),
                "conversation_id": oldest.get("conversation_id", ""),
                "title": oldest.get("conversation_title", ""),
                "excerpt": oldest.get("snippet", ""),
            }

        if archaeology_mode and keyword and not fts_results:
            return render_template(
                "federated.html",
                keyword=keyword,
                fts_results=[],
                fts_active=True,
                rows=[],
                format_timestamp=format_timestamp,
                callout=None,
                sort=sort_param,
                archaeology_mode=True,
            )

        if fts_results:
            return render_template(
                "federated.html",
                keyword=keyword,
                fts_results=fts_results,
                fts_active=True,
                rows=[],
                format_timestamp=format_timestamp,
                callout=callout,
                sort=sort_param,
                archaeology_mode=archaeology_mode,
            )

        # No FTS results (or no keyword) — existing browse/search behavior
        results = federated_search(sqlite_path=sqlite_path, keyword=keyword)

        rows = []
        for result in results:
            handoff_href = None
            if (
                result.source_lane == "imported_conversation"
                and result.stable_id.startswith("imported_conversation:")
            ):
                conversation_id = result.stable_id.split(":", maxsplit=1)[1]
                if conversation_id.isdigit():
                    handoff_href = f"/imported/{conversation_id}/explorer"
            elif result.source_lane == "native_memory":
                entry_id = _native_memory_entry_id(result.stable_id)
                if entry_id is not None:
                    handoff_href = url_for(
                        "memory_detail",
                        entry_id=entry_id,
                        **{"from": "federated", "q": keyword},
                    )

            rows.append({"result": result, "handoff_href": handoff_href})

        return render_template(
            "federated.html",
            keyword=keyword,
            rows=rows,
            fts_active=False,
            fts_results=[],
            format_timestamp=format_timestamp,
            sort=sort_param,
            archaeology_mode=archaeology_mode,
        )

    @app.get("/answer-traces")
    def answer_trace_list():
        from ..answering.trace import default_trace_store_path, list_answer_traces

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        trace_store = default_trace_store_path(_sqlite_path_from_uri(sqlite_uri))
        traces = list_answer_traces(trace_store, limit=50)

        return render_template(
            "answer_trace_list.html",
            traces=traces,
            trace_store=trace_store,
        )

    @app.get("/answer-traces/<path:trace_id>")
    def answer_trace_detail(trace_id: str):
        from ..answering.trace import default_trace_store_path, get_answer_trace

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        trace_store = default_trace_store_path(_sqlite_path_from_uri(sqlite_uri))
        trace = get_answer_trace(trace_store, trace_id)
        if trace is None:
            abort(404)

        trace_citations = [
            build_answer_trace_citation_view(citation)
            for citation in trace.get("citations") or []
        ]

        return render_template(
            "answer_trace_detail.html",
            trace=trace,
            trace_citations=trace_citations,
            trace_store=trace_store,
        )

    @app.route("/ask", methods=["GET", "POST"])
    @require_license
    def ask():
        from ..answering.local import answer_from_federated_hits, retrieval_keyword_from_question
        from ..answering.trace import (
            append_answer_trace,
            create_answer_trace,
            default_trace_store_path,
            list_answer_traces,
        )

        question = ""
        validation_error = None
        runtime_error = None
        result = None

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_path = _sqlite_path_from_uri(sqlite_uri)
        trace_store = default_trace_store_path(sqlite_path)

        if request.method == "POST":
            question = request.form.get("question", "").strip()
            if not question:
                validation_error = "Enter a question before asking."
            else:
                try:
                    retrieval_terms = retrieval_keyword_from_question(question)
                    hits = federated_search(
                        sqlite_path=sqlite_path,
                        keyword=retrieval_terms,
                        limit_per_lane=10,
                    )
                    answer = answer_from_federated_hits(question, hits)

                    trace = create_answer_trace(
                        question=question,
                        retrieval_terms=retrieval_terms,
                        answer=answer,
                    )
                    append_answer_trace(trace_store, trace)

                    result = {
                        "answer_text": answer.answer_text,
                        "status": answer.status,
                        "notes": answer.notes,
                        "trace_id": trace.trace_id,
                        "trace_href": url_for("answer_trace_detail", trace_id=trace.trace_id),
                        "citations": [
                            build_answer_trace_citation_view(asdict(citation))
                            for citation in answer.citations
                        ],
                    }
                except Exception:
                    runtime_error = (
                        "Ask could not complete right now. Please try again in a moment."
                    )

        recent_traces = list_answer_traces(trace_store, limit=5)
        return render_template(
            "ask.html",
            question=question,
            validation_error=validation_error,
            runtime_error=runtime_error,
            result=result,
            recent_traces=recent_traces,
        )

    @app.get("/intelligence")
    def intelligence():
        from ..intelligence.provider import is_llm_configured
        from ..intelligence.store import (
            default_digest_store_path,
            default_summary_store_path,
            default_topic_store_path,
            list_digests,
            list_summaries,
            list_topic_scans,
        )

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_path = _sqlite_path_from_uri(sqlite_uri)
        configured = is_llm_configured()

        summaries = list_summaries(default_summary_store_path(sqlite_path)) if configured else []

        topic_scans = list_topic_scans(default_topic_store_path(sqlite_path))
        latest_scan = topic_scans[0] if topic_scans else None

        digests = list_digests(default_digest_store_path(sqlite_path))

        return render_template(
            "intelligence.html",
            llm_configured=configured,
            summaries=summaries,
            latest_scan=latest_scan,
            digests=digests,
        )

    @app.post("/intelligence/summarize/<int:conversation_id>")
    @require_license
    def intelligence_summarize(conversation_id: int):
        from ..intelligence.provider import provider_from_config
        from ..intelligence.store import append_summary, default_summary_store_path
        from ..intelligence.summarizer import summarize_conversation

        conversation = ImportedConversation.query.filter_by(id=conversation_id).first_or_404()
        provider = provider_from_config()
        if provider is None:
            abort(400)

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        summary_store = default_summary_store_path(_sqlite_path_from_uri(sqlite_uri))

        summary = summarize_conversation(conversation, provider)
        append_summary(summary_store, summary)

        return redirect(url_for("intelligence"))

    @app.post("/intelligence/scan-topics")
    @require_license
    def intelligence_scan_topics():
        from ..intelligence.provider import provider_from_config
        from ..intelligence.store import append_topic_scan, default_topic_store_path
        from ..intelligence.topics import extract_topics

        provider = provider_from_config()
        conversations = (
            ImportedConversation.query
            .order_by(ImportedConversation.id.desc())
            .limit(50)
            .all()
        )

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        topic_store = default_topic_store_path(_sqlite_path_from_uri(sqlite_uri))

        scan = extract_topics(conversations, provider)
        append_topic_scan(topic_store, scan)

        return redirect(url_for("intelligence"))

    @app.post("/intelligence/digest/<int:topic_index>")
    @require_license
    def intelligence_digest(topic_index: int):
        from ..intelligence.digest import generate_digest
        from ..intelligence.provider import provider_from_config
        from ..intelligence.store import (
            append_digest,
            default_digest_store_path,
            default_topic_store_path,
            list_topic_scans,
        )

        provider = provider_from_config()
        if provider is None:
            abort(400)

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_path = _sqlite_path_from_uri(sqlite_uri)

        topic_scans = list_topic_scans(default_topic_store_path(sqlite_path))
        if not topic_scans:
            abort(404)

        latest_scan = topic_scans[0]
        clusters = latest_scan.get("clusters", [])
        if topic_index < 0 or topic_index >= len(clusters):
            abort(404)

        cluster = clusters[topic_index]

        # Resolve conversation IDs from stable IDs
        conv_ids = []
        for sid in cluster["conversation_stable_ids"]:
            parts = sid.split(":", 1)
            if len(parts) == 2 and parts[1].isdigit():
                conv_ids.append(int(parts[1]))

        conversations = ImportedConversation.query.filter(
            ImportedConversation.id.in_(conv_ids)
        ).all()

        if not conversations:
            abort(404)

        digest = generate_digest(cluster["topic_label"], conversations, provider)
        append_digest(default_digest_store_path(sqlite_path), digest)

        return redirect(url_for("intelligence"))

    # ------------------------------------------------------------------
    # Wrapped summary route
    # ------------------------------------------------------------------

    @app.get("/summary")
    def summary():
        from .viewmodels.wrapped import build_wrapped_summary

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_path = _sqlite_path_from_uri(sqlite_uri)
        wrapped = build_wrapped_summary(sqlite_path=sqlite_path)

        # Pre-format date range for the template
        def _format_unix_date(ts):
            if ts is None:
                return "\u2014"
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%b %Y")

        date_range_start = _format_unix_date(wrapped.date_range.get("earliest"))
        date_range_end = _format_unix_date(wrapped.date_range.get("latest"))

        earliest_date = None
        if wrapped.earliest_conversation:
            earliest_date = _format_unix_date(
                wrapped.earliest_conversation.get("created_at_unix")
            )

        return render_template(
            "wrapped.html",
            wrapped=wrapped,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            earliest_date=earliest_date,
        )

    # ------------------------------------------------------------------
    # Continuity packet routes
    # ------------------------------------------------------------------

    @app.post("/intelligence/continuity/<int:conversation_id>")
    @require_license
    def intelligence_continuity_generate(conversation_id: int):
        from ..intelligence.continuity.service import generate_continuity_packet
        from ..intelligence.continuity.store import default_continuity_store_path
        from ..intelligence.provider import provider_from_config

        conversation = ImportedConversation.query.filter_by(id=conversation_id).first_or_404()
        provider = provider_from_config()
        if provider is None:
            abort(400)

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        store_path = default_continuity_store_path(_sqlite_path_from_uri(sqlite_uri))

        result = generate_continuity_packet(conversation, provider, store_path)
        if result.error:
            logger.error(
                "continuity_generate failed for conversation_id=%s: %s",
                conversation_id,
                result.error,
            )
            abort(500)

        return redirect(url_for("intelligence_continuity_view", conversation_id=conversation_id))

    @app.get("/intelligence/continuity/<int:conversation_id>")
    def intelligence_continuity_view(conversation_id: int):
        from ..intelligence.continuity.store import (
            default_continuity_store_path,
            list_artifacts_for_conversation,
        )
        from ..intelligence.provider import is_llm_configured

        conversation = ImportedConversation.query.filter_by(id=conversation_id).first_or_404()
        configured = is_llm_configured()

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        store_path = default_continuity_store_path(_sqlite_path_from_uri(sqlite_uri))
        stable_id = f"imported_conversation:{conversation_id}"

        all_artifacts = list_artifacts_for_conversation(store_path, stable_id)

        # Group by type
        artifacts_by_type = {}
        for a in all_artifacts:
            atype = a.get("artifact_type", "")
            if atype not in artifacts_by_type:
                artifacts_by_type[atype] = a

        # Build copy payload
        copy_lines = []
        if "summary" in artifacts_by_type:
            copy_lines.append("## Summary\n" + artifacts_by_type["summary"]["content_text"])
        if "decisions" in artifacts_by_type:
            copy_lines.append("## Decisions\n" + artifacts_by_type["decisions"]["content_text"])
        if "open_loops" in artifacts_by_type:
            copy_lines.append("## Open Loops\n" + artifacts_by_type["open_loops"]["content_text"])
        if "entity_map" in artifacts_by_type:
            copy_lines.append("## Entity Map\n" + artifacts_by_type["entity_map"]["content_text"])
        copy_payload = "\n\n".join(copy_lines) if copy_lines else ""

        return render_template(
            "continuity_detail.html",
            conversation=conversation,
            artifacts=artifacts_by_type,
            copy_payload=copy_payload,
            llm_configured=configured,
        )

    @app.get("/continuity/open-loops")
    def continuity_open_loops():
        from ..intelligence.continuity.store import (
            default_continuity_store_path,
            list_artifacts,
        )

        db_path = _sqlite_path_from_uri(app.config["SQLALCHEMY_DATABASE_URI"])
        store_path = default_continuity_store_path(db_path)
        # Filter after reading to avoid list_artifacts_by_type's pre-filter cap.
        all_artifacts = list_artifacts(store_path, limit=1_000_000)
        artifacts = [a for a in all_artifacts if a.get("artifact_type") == "open_loops"]

        rows = []
        for artifact in artifacts:
            loop_texts = _extract_loop_texts(artifact)
            source_ids = artifact.get("source_conversation_ids", [])
            conv_info = _resolve_open_loop_conversation(source_ids)
            for loop_text in loop_texts:
                rows.append({
                    "artifact_id": artifact.get("artifact_id", ""),
                    "loop_text": loop_text,
                    "generation_timestamp": artifact.get("generation_timestamp", ""),
                    "llm_provider_used": artifact.get("llm_provider_used", ""),
                    "conversation_id": conv_info["id"],
                    "conversation_title": conv_info["title"],
                    "conversation_source": conv_info["source"],
                    "explorer_url": conv_info["explorer_url"],
                    "continuity_url": conv_info["continuity_url"],
                })

        return render_template("open_loops.html", rows=rows)

    # ------------------------------------------------------------------
    # Multi-conversation distillation routes
    # ------------------------------------------------------------------

    @app.route("/distill", methods=["GET", "POST"])
    @require_license
    def distill():
        from ..intelligence.provider import provider_from_config

        provider = provider_from_config()

        if request.method == "GET":
            from ..intelligence.threads import suggest_threads

            conversations = (
                ImportedConversation.query
                .order_by(ImportedConversation.id.desc())
                .all()
            )
            threads = suggest_threads(conversations) if conversations else []
            return render_template(
                "distill.html",
                conversations=conversations,
                threads=threads,
                llm_configured=provider is not None,
                result=None,
            )

        # POST: run distillation on selected conversations
        if provider is None:
            abort(400)

        selected_ids = request.form.getlist("conversation_ids", type=int)
        if not selected_ids:
            from ..intelligence.threads import suggest_threads

            conversations = (
                ImportedConversation.query
                .order_by(ImportedConversation.id.desc())
                .limit(20)
                .all()
            )
            threads = suggest_threads(conversations) if conversations else []
            return render_template(
                "distill.html",
                conversations=conversations,
                threads=threads,
                llm_configured=True,
                result=None,
                error_message="Select at least one conversation to distill.",
            )

        from ..intelligence.distill import distill_conversations
        from ..intelligence.store import (
            append_distillation,
            default_distillation_store_path,
        )

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        sqlite_path = _sqlite_path_from_uri(sqlite_uri)

        conversations = ImportedConversation.query.filter(
            ImportedConversation.id.in_(selected_ids)
        ).all()

        if not conversations:
            abort(404)

        result = distill_conversations(conversations, provider)
        append_distillation(
            default_distillation_store_path(sqlite_path), result
        )

        # Build source metadata for the result page header
        from ..intelligence.threads import _format_date, _date_range_str

        source_timestamps = [
            c.created_at_unix or c.updated_at_unix for c in conversations
        ]
        source_meta = {
            "date_range": _date_range_str(source_timestamps),
            "conversations": [
                {"id": c.id, "title": c.title or "Untitled", "source": c.source}
                for c in conversations
            ],
        }

        handoff_briefing = format_handoff_briefing(
            result.distilled_text,
            result.conversation_count,
            source_meta.get("date_range"),
        )

        return render_template(
            "distill_result.html",
            result=result,
            source_meta=source_meta,
            handoff_briefing=handoff_briefing,
        )

    @app.get("/imported/scan-claude-code")
    def scan_claude_code():
        from ..importers.claude_code_discovery import (
            default_claude_projects_dir,
            discover_sessions,
            normalize_projects_path,
        )
        error_message = session.pop("scan_error", None)
        raw_path = request.args.get("path", "").strip()
        if raw_path:
            try:
                projects_dir = normalize_projects_path(raw_path)
            except (ValueError, OSError):
                session["scan_error"] = "Projects path must be under your home directory."
                return redirect(url_for("scan_claude_code"))
        else:
            projects_dir = default_claude_projects_dir()

        discovered = discover_sessions(projects_dir)
        projects: dict[str, dict] = {}
        for s in discovered:
            key = s.project_dir_name
            if key not in projects:
                projects[key] = {
                    "dir_name": s.project_dir_name,
                    "path_display": s.project_path or s.project_dir_name,
                    "sessions": [],
                }
            projects[key]["sessions"].append(s)

        return render_template(
            "scan_claude_code.html",
            projects=list(projects.values()),
            projects_dir=str(projects_dir),
            session_count=len(discovered),
            error_message=error_message,
        )

    @app.post("/imported/scan-claude-code")
    def scan_claude_code_import():
        from ..importers.claude_code_discovery import (
            default_claude_projects_dir,
            discover_sessions,
            import_selected_sessions,
        )

        run_provider: str | None = "claude_code"
        run_filename: str | None = "scan-claude-code"
        run_imported = 0
        run_messages_imported = 0
        run_skipped = 0
        run_failed = 0
        run_error_message: str | None = None
        run_reached_importer = False

        try:
            selected_ids = set(request.form.getlist("session_ids"))
            if not selected_ids:
                session["scan_error"] = "No sessions selected."
                run_error_message = "No sessions selected."
                return redirect(url_for("scan_claude_code"))

            sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            db_path = _sqlite_path_from_uri(sqlite_uri)
            raw_projects_dir = request.form.get("projects_dir", "").strip()
            if raw_projects_dir:
                home = Path.home()
                try:
                    from ..importers.claude_code_discovery import normalize_projects_path
                    candidate = normalize_projects_path(raw_projects_dir)
                    candidate.relative_to(home.resolve())
                    projects_dir = candidate
                except (ValueError, OSError):
                    session["scan_error"] = "Projects path must be under your home directory."
                    run_error_message = "Projects path must be under your home directory."
                    return redirect(url_for("scan_claude_code"))
            else:
                projects_dir = default_claude_projects_dir()

            discovered = discover_sessions(projects_dir)
            to_import = [s for s in discovered if s.session_id in selected_ids]
            run_filename = f"scan-claude-code:{len(to_import)}-sessions"

            if not to_import:
                session["scan_error"] = "Selected sessions no longer exist on disk."
                run_error_message = "Selected sessions no longer exist on disk."
                return redirect(url_for("scan_claude_code"))

            import sqlite3 as _sqlite3
            _c = _sqlite3.connect(str(db_path))
            try:
                msg_before = _c.execute("SELECT COUNT(*) FROM imported_message").fetchone()[0]
            finally:
                _c.close()

            result = import_selected_sessions(to_import, db_path)
            run_reached_importer = True
            run_imported = len(result.imported)
            run_skipped = len(result.skipped_duplicate)
            run_failed = len(result.failed)
            if result.failed:
                run_error_message = "; ".join(f"{sid}: {msg}" for sid, msg in result.failed)

            _c = _sqlite3.connect(str(db_path))
            try:
                msg_after = _c.execute("SELECT COUNT(*) FROM imported_message").fetchone()[0]
            finally:
                _c.close()
            run_messages_imported = max(0, msg_after - msg_before)

            session["scan_result"] = {
                "imported": result.imported,
                "skipped_duplicate": result.skipped_duplicate,
                "failed": [
                    {"session_id": sid, "error": msg}
                    for sid, msg in result.failed
                ],
            }
            return redirect(url_for("scan_claude_code_results"))
        finally:
            status = classify_import_outcome(
                run_imported, run_skipped, run_failed,
                reached_importer=run_reached_importer,
            )
            record_import_run(
                provider=run_provider,
                filename=run_filename,
                status=status,
                conversations_imported=run_imported,
                messages_imported=run_messages_imported,
                conversations_skipped=run_skipped,
                conversations_failed=run_failed,
                error_message=run_error_message,
            )

    @app.get("/imported/scan-claude-code/results")
    def scan_claude_code_results():
        scan_result = session.pop("scan_result", None)
        if scan_result is None:
            return redirect(url_for("scan_claude_code"))
        return render_template("scan_claude_code_results.html", result=scan_result)

    return app
