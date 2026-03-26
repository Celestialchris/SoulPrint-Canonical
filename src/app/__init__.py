from dataclasses import asdict
from flask import Flask, abort, redirect, render_template, request, jsonify, url_for
from datetime import datetime, timezone
import os
import tempfile
from pathlib import Path

from .imported_explorer import anchor_for_message, build_prompt_toc, format_timestamp
from .models.db import db
from ..config import Config, normalize_sqlite_uri
from ..runtime import default_instance_dir, static_dir, templates_dir
from .models import ImportedConversation, ImportedMessage, MemoryEntry
from .citation_handoff import build_answer_trace_citation_view
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


def federated_search(*args, **kwargs):
    """Lazy import wrapper to avoid retrieval/app circular imports."""

    from ..retrieval.federated import federated_search as _federated_search

    return _federated_search(*args, **kwargs)


def _memory_timestamp_to_unix(entry: MemoryEntry) -> float | None:
    """Normalize native memory timestamps for UI display."""

    if entry.timestamp is None:
        return None

    timestamp = entry.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return timestamp.timestamp()


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

    @app.get("/")
    def home():
        from ..answering.trace import default_trace_store_path

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        trace_store = default_trace_store_path(_sqlite_path_from_uri(sqlite_uri))
        workspace = build_workspace_summary(trace_store_path=trace_store)

        license_status = get_license_status(instance_dir=app.instance_path)
        return render_template("index.html", workspace=workspace, license_status=license_status)

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

        return render_template(
            "passport.html",
            capability=capability,
            status=status,
        )

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

        return jsonify({"ok": True, "id": entry.id})



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

    @app.get("/imported")
    def imported_conversations():
        PER_PAGE = 50
        keyword = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        if page < 1:
            page = 1

        rows_query = (
            db.session.query(
                ImportedConversation,
                func.count(ImportedMessage.id).label("message_count"),
            )
            .outerjoin(ImportedConversation.messages)
            .group_by(ImportedConversation.id)
        )

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

        return render_template(
            "imported_list.html",
            rows=rows,
            keyword=keyword,
            format_timestamp=format_timestamp,
            page=page,
            total_pages=total_pages,
            total=total,
        )

    @app.route("/import", methods=["GET", "POST"])
    def import_conversations():
        error_message = None
        result = None

        if request.method == "POST":
            # Capture count before import for first-import redirect
            count_before = ImportedConversation.query.count()

            upload = request.files.get("export_file")
            if upload is None or upload.filename == "":
                error_message = "Choose an export JSON file before importing."
            else:
                temp_path: Path | None = None
                try:
                    suffix = Path(upload.filename).suffix or ".json"
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

                    # First import: redirect to summary page
                    if count_before == 0 and import_result.imported_conversations > 0:
                        return redirect(url_for("summary"))

                    result = {
                        "provider_id": import_result.provider_id,
                        "imported_conversations": import_result.imported_conversations,
                        "skipped_conversations": import_result.skipped_conversations,
                        "imported_messages": import_result.imported_messages,
                        "warnings": import_result.warnings,
                        "show_summary_link": import_result.imported_conversations > 0,
                    }
                except ImportProviderDetectionError:
                    error_message = (
                        "We could not recognize this export format. Supported imports are ChatGPT, Claude, and Gemini conversation exports."
                    )
                except UnsupportedImportFormatError as exc:
                    error_message = f"This export format is not supported yet: {exc}"
                except MalformedImportFileError as exc:
                    error_message = str(exc)
                finally:
                    if temp_path is not None and temp_path.exists():
                        temp_path.unlink()

        return render_template(
            "import.html",
            error_message=error_message,
            result=result,
        )

    @app.get("/chats")
    def chats():
        tag = request.args.get("tag", "").strip()
        q = MemoryEntry.query.order_by(MemoryEntry.timestamp.desc())
        if tag:
            q = q.filter(MemoryEntry.tags.contains(tag))
        entries = q.limit(100).all()
        return render_template("view.html", entries=entries)

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
            format_timestamp=format_timestamp,
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
    def ask():
        from ..answering.local import answer_from_federated_hits, retrieval_keyword_from_question
        from ..answering.trace import (
            append_answer_trace,
            create_answer_trace,
            default_trace_store_path,
            list_answer_traces,
        )

        if not is_licensed(instance_dir=app.instance_path):
            if request.method == "POST":
                abort(403)
            return render_template("upgrade.html")

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
    def intelligence_summarize(conversation_id: int):
        if not is_licensed(instance_dir=app.instance_path):
            abort(403)

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
    def intelligence_scan_topics():
        if not is_licensed(instance_dir=app.instance_path):
            abort(403)

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
    def intelligence_digest(topic_index: int):
        if not is_licensed(instance_dir=app.instance_path):
            abort(403)

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

        return render_template(
            "wrapped.html",
            wrapped=wrapped,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
        )

    # ------------------------------------------------------------------
    # Continuity packet routes
    # ------------------------------------------------------------------

    @app.post("/intelligence/continuity/<int:conversation_id>")
    def intelligence_continuity_generate(conversation_id: int):
        if not is_licensed(instance_dir=app.instance_path):
            abort(403)

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

    # ------------------------------------------------------------------
    # Multi-conversation distillation routes
    # ------------------------------------------------------------------

    @app.route("/distill", methods=["GET", "POST"])
    def distill():
        if not is_licensed(instance_dir=app.instance_path):
            return render_template("upgrade.html"), 200

        from ..intelligence.provider import provider_from_config

        provider = provider_from_config()

        if request.method == "GET":
            conversations = (
                ImportedConversation.query
                .order_by(ImportedConversation.id.desc())
                .all()
            )
            return render_template(
                "distill.html",
                conversations=conversations,
                llm_configured=provider is not None,
                result=None,
            )

        # POST: run distillation on selected conversations
        if provider is None:
            abort(400)

        selected_ids = request.form.getlist("conversation_ids", type=int)
        if not selected_ids:
            conversations = (
                ImportedConversation.query
                .order_by(ImportedConversation.id.desc())
                .all()
            )
            return render_template(
                "distill.html",
                conversations=conversations,
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

        return render_template(
            "distill_result.html",
            result=result,
        )

    return app
