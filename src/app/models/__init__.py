from .db import db


class MemoryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    role = db.Column(db.String(32), nullable=False)  # user / assistant / system
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text, nullable=True)
    is_starred = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
    )

    def __repr__(self):
        return f"<MemoryEntry {self.id} {self.timestamp} {self.role}>"


class ImportedConversation(db.Model):
    """Normalized imported conversation metadata."""

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(32), nullable=False)
    source_conversation_id = db.Column(db.String(128), nullable=False, index=True)
    title = db.Column(db.Text, nullable=False, default="Untitled Conversation")
    created_at_unix = db.Column(db.Float, nullable=True)
    updated_at_unix = db.Column(db.Float, nullable=True)
    is_archived = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
    )
    is_starred = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
    )
    tags = db.Column(
        db.String,
        nullable=False,
        server_default="",
        default="",
    )
    source_metadata_json = db.Column(db.Text, nullable=True)

    messages = db.relationship(
        "ImportedMessage",
        backref="conversation",
        cascade="all, delete-orphan",
        order_by="ImportedMessage.sequence_index",
        lazy=True,
    )


class ImportedMessage(db.Model):
    """Normalized imported conversation message."""

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("imported_conversation.id"),
        nullable=False,
        index=True,
    )
    source_message_id = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sequence_index = db.Column(db.Integer, nullable=False)
    created_at_unix = db.Column(db.Float, nullable=True)


class ImportRun(db.Model):
    """Durable history row for one import attempt at an import route handler."""

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(32), nullable=True)
    filename = db.Column(db.String(512), nullable=True)
    imported_at = db.Column(db.Float, nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, index=True)
    conversations_imported = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    messages_imported = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    conversations_skipped = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    conversations_failed = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    error_message = db.Column(db.String(500), nullable=True)
