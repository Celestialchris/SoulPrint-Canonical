from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from .models import Asset, ConversationAsset, MessageAsset
from .models.db import db


def store_asset(
    file_stream,
    original_filename: str,
    mime_type: str | None = None,
    *,
    source: str = "manual",
    instance_root=None,
) -> Asset:
    """Persist bytes from file_stream to content-addressed storage.

    Deduplicates by SHA256: if the same bytes were stored before, returns the
    existing Asset row without creating a second physical file. Commits the new
    Asset row when one is created.
    """
    data = file_stream.read()
    sha256 = hashlib.sha256(data).hexdigest()

    existing = Asset.query.filter_by(sha256=sha256).first()
    if existing is not None:
        abs_path = asset_absolute_path(existing, instance_root=instance_root)
        if not abs_path.exists():
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_bytes(data)
        return existing

    safe_name = _sanitize_filename(original_filename)
    suffix = Path(safe_name).suffix
    extension: str | None = suffix.lstrip(".")[:32] or None
    stored_filename = f"{sha256}-{safe_name}"[:255]
    storage_path = f"assets/sha256/{sha256[:2]}/{stored_filename}"
    storage_base = _resolve_instance_root(instance_root)
    abs_path = storage_base / storage_path

    asset = Asset(
        stable_id=f"asset:sha256:{sha256}",
        sha256=sha256,
        original_filename=original_filename,
        stored_filename=stored_filename,
        mime_type=mime_type,
        extension=extension,
        size_bytes=len(data),
        storage_path=storage_path,
        uploaded_at_unix=time.time(),
        source=source,
        parse_status="unparsed",
        parse_error=None,
    )
    db.session.add(asset)

    try:
        # Flush first so IntegrityError is detected before we write to disk.
        # This prevents orphaned files when two uploads race on the same bytes.
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        recovered = Asset.query.filter_by(sha256=sha256).first()
        if recovered is None:
            raise
        recovered_path = asset_absolute_path(recovered, instance_root=instance_root)
        if not recovered_path.exists():
            recovered_path.parent.mkdir(parents=True, exist_ok=True)
            recovered_path.write_bytes(data)
        return recovered

    # CodeQL-recognized py/path-injection sanitizer: realpath + startswith.
    # Inlined at the sink because CodeQL does not follow helpers for this rule.
    base_real = os.path.realpath(str(storage_base))
    target_real = os.path.realpath(str(abs_path))
    base_prefix = base_real.rstrip(os.sep) + os.sep
    if not (target_real.startswith(base_prefix) or target_real == base_real):
        raise ValueError("Asset path must be under storage base")
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(data)
    db.session.commit()
    return asset


def attach_asset_to_conversation(
    conversation_id: int,
    asset_id: int,
    *,
    role: str = "context",
    note: str = "",
) -> ConversationAsset:
    """Create a ConversationAsset relationship row and commit it."""
    row = ConversationAsset(
        conversation_id=conversation_id,
        asset_id=asset_id,
        role=role,
        note=note,
        attached_at_unix=time.time(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def attach_asset_to_message(
    message_id: int,
    asset_id: int,
    *,
    placement: str = "after_message_content",
    caption: str = "",
) -> MessageAsset:
    """Create a MessageAsset relationship row and commit it."""
    row = MessageAsset(
        message_id=message_id,
        asset_id=asset_id,
        placement=placement,
        caption=caption,
        attached_at_unix=time.time(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def list_conversation_assets(conversation_id: int) -> list[ConversationAsset]:
    """Return all ConversationAsset rows for a given conversation."""
    return ConversationAsset.query.filter_by(conversation_id=conversation_id).all()


def list_message_assets(message_ids: list[int]) -> dict[int, list[MessageAsset]]:
    """Return MessageAsset rows keyed by message_id for a batch of message IDs."""
    if not message_ids:
        return {}
    rows = MessageAsset.query.filter(MessageAsset.message_id.in_(message_ids)).all()
    result: dict[int, list[MessageAsset]] = {mid: [] for mid in message_ids}
    for row in rows:
        result[row.message_id].append(row)
    return result


def asset_absolute_path(asset: Asset, *, instance_root=None) -> Path:
    """Resolve the absolute filesystem path for an asset.

    Raises ValueError if storage_path would escape the instance root.
    """
    root = _resolve_instance_root(instance_root).resolve()
    resolved = (root / Path(asset.storage_path)).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"storage_path escapes instance root: {asset.storage_path!r}")
    return resolved


def _resolve_instance_root(instance_root) -> Path:
    if instance_root is not None:
        return Path(instance_root)
    from src.runtime import default_instance_dir
    return default_instance_dir()


def _sanitize_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r"[^\w\-.]", "_", name)
    name = re.sub(r"_{2,}", "_", name)
    name = name.lstrip("._")
    name = name[:100]
    return name or "unnamed_file"
