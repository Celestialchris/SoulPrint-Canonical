from dataclasses import asdict
from flask import Flask, abort, render_template, request, jsonify, url_for
from datetime import datetime, timezone
import os
import tempfile
from pathlib import Path

from .imported_explorer import anchor_for_message, build_prompt_toc, format_timestamp
from .models.db import db
from ..config import Config, normalize_sqlite_uri
from .models import ImportedConversation, ImportedMessage, MemoryEntry
from .citation_handoff import build_answer_trace_citation_view
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
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_sqlite_uri(
        app.config.get("SQLALCHEMY_DATABASE_URI", "")
    )

    db_path = os.path.abspath(os.path.join(app.root_path, "..", "..", "instance"))
    os.makedirs(db_path, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def home():
        from ..answering.trace import default_trace_store_path

        sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        trace_store = default_trace_store_path(_sqlite_path_from_uri(sqlite_uri))
        workspace = build_workspace_summary(trace_store_path=trace_store)

        return render_template("index.html", workspace=workspace)

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
                "CLI surface. This web page is not currently inspecting a specific "
                "passport artifact path."
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
        conversation = ImportedConversation.query.filter_by(id=conversation_id).first_or_404()

        messages = sorted(conversation.messages, key=lambda m: m.sequence_index)
        toc_entries = build_prompt_toc(messages)

        return render_template(
            "imported_explorer.html",
            conversation=conversation,
            messages=messages,
            toc_entries=toc_entries,
            format_timestamp=format_timestamp,
            anchor_for_message=anchor_for_message,
        )

    @app.get("/imported")
    def imported_conversations():
        keyword = request.args.get("q", "").strip()

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

        rows = rows_query.order_by(ImportedConversation.id.desc()).limit(100).all()
        return render_template(
            "imported_list.html",
            rows=rows,
            keyword=keyword,
            format_timestamp=format_timestamp,
        )

    @app.route("/import", methods=["GET", "POST"])
    def import_conversations():
        error_message = None
        result = None

        if request.method == "POST":
            upload = request.files.get("export_file")
            if upload is None or upload.filename == "":
                error_message = "Choose an export JSON file before importing."
            else:
                temp_path: Path | None = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="wb",
                        suffix=".json",
                        delete=False,
                    ) as handle:
                        upload.save(handle)
                        temp_path = Path(handle.name)

                    sqlite_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
                    sqlite_path = _sqlite_path_from_uri(sqlite_uri)
                    import_result = import_conversation_export_to_sqlite(temp_path, sqlite_path)
                    result = {
                        "provider_id": import_result.provider_id,
                        "imported_conversations": import_result.imported_conversations,
                        "skipped_conversations": import_result.skipped_conversations,
                        "imported_messages": import_result.imported_messages,
                        "warnings": import_result.warnings,
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

    return app
