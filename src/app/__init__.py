from flask import Flask, abort, render_template, request, jsonify
from datetime import datetime
import os

from .imported_explorer import anchor_for_message, build_prompt_toc, format_timestamp
from .models.db import db
from ..config import Config
from .models import ImportedConversation, ImportedMessage, MemoryEntry
from sqlalchemy import func


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db_path = os.path.abspath(os.path.join(app.root_path, "..", "..", "instance"))
    os.makedirs(db_path, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.get("/")
    def home():
        return render_template("index.html")

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
                func.count().label("message_count"),
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

    @app.get("/chats")
    def chats():
        tag = request.args.get("tag", "").strip()
        q = MemoryEntry.query.order_by(MemoryEntry.timestamp.desc())
        if tag:
            q = q.filter(MemoryEntry.tags.contains(tag))
        entries = q.limit(100).all()
        return render_template("view.html", entries=entries)

    return app
