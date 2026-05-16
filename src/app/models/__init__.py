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
    conversation_assets = db.relationship(
        "ConversationAsset",
        backref="conversation",
        cascade="all, delete-orphan",
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

    message_assets = db.relationship(
        "MessageAsset",
        backref="message",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stable_id = db.Column(db.String(128), nullable=False, unique=True, index=True)
    sha256 = db.Column(db.String(64), nullable=False, unique=True, index=True)
    original_filename = db.Column(db.Text, nullable=False)
    stored_filename = db.Column(db.Text, nullable=False)
    mime_type = db.Column(db.String(255), nullable=True)
    extension = db.Column(db.String(32), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False)
    storage_path = db.Column(db.Text, nullable=False)
    uploaded_at_unix = db.Column(db.Float, nullable=False, index=True)
    source = db.Column(db.String(64), nullable=False, default="manual")
    parse_status = db.Column(db.String(32), nullable=False, default="unparsed")
    parse_error = db.Column(db.Text, nullable=True)

    conversation_assets = db.relationship("ConversationAsset", back_populates="asset", lazy=True)
    message_assets = db.relationship("MessageAsset", back_populates="asset", lazy=True)


class ConversationAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("imported_conversation.id"), nullable=False, index=True
    )
    asset_id = db.Column(db.Integer, db.ForeignKey("asset.id"), nullable=False, index=True)
    role = db.Column(db.String(64), nullable=False, default="context")
    note = db.Column(db.Text, nullable=False, default="")
    attached_at_unix = db.Column(db.Float, nullable=False, index=True)

    asset = db.relationship("Asset", back_populates="conversation_assets")

    __table_args__ = (
        db.UniqueConstraint("conversation_id", "asset_id", name="uq_conversation_asset"),
    )


class MessageAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(
        db.Integer, db.ForeignKey("imported_message.id"), nullable=False, index=True
    )
    asset_id = db.Column(db.Integer, db.ForeignKey("asset.id"), nullable=False, index=True)
    placement = db.Column(db.String(64), nullable=False, default="after_message_content")
    caption = db.Column(db.Text, nullable=False, default="")
    attached_at_unix = db.Column(db.Float, nullable=False, index=True)

    asset = db.relationship("Asset", back_populates="message_assets")

    __table_args__ = (
        db.UniqueConstraint("message_id", "asset_id", name="uq_message_asset"),
    )


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


class Capture(db.Model):
    """Raw captured payload awaiting triage; the Campaign 03 capture ledger."""

    __tablename__ = "capture"

    id = db.Column(db.Integer, primary_key=True)
    adapter_id = db.Column(db.Text, nullable=False)
    adapter_version = db.Column(db.Text, nullable=False)
    payload_kind = db.Column(db.Text, nullable=False)
    body_text = db.Column(db.Text, nullable=False)
    body_html = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.Text, nullable=True)
    source_title = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    hints_json = db.Column(db.Text, nullable=True)
    content_hash = db.Column(db.String(64), nullable=False)
    content_hash_recipe_version = db.Column(db.Integer, nullable=False)
    raw_payload_hash = db.Column(db.String(64), nullable=False)
    captured_at_unix = db.Column(db.Float, nullable=False)
    received_at_unix = db.Column(db.Float, nullable=False)
    status = db.Column(
        db.Text,
        nullable=False,
        default="pending",
        server_default="pending",
    )
    triaged_at_unix = db.Column(db.Float, nullable=True)
    decided_at_unix = db.Column(db.Float, nullable=True)
    decided_by = db.Column(db.Text, nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)
    quarantine_reason = db.Column(db.Text, nullable=True)
    promoted_to_kind = db.Column(db.Text, nullable=True)
    promoted_to_id = db.Column(db.Integer, nullable=True)
    tags = db.Column(db.Text, nullable=True)
    filesystem_path = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending','triaged','promoted','rejected','quarantined')",
            name="capture_status_chk",
        ),
        db.Index("idx_capture_status", "status"),
        db.Index("idx_capture_content_hash", "content_hash", unique=True),
        db.Index("idx_capture_received_at", received_at_unix.desc()),
        db.Index("idx_capture_adapter", adapter_id, captured_at_unix.desc()),
        {"sqlite_autoincrement": True},
    )
