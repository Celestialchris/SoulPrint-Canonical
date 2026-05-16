"""The record_capture persistence service for the capture ledger.

``record_capture`` is a library function. B1 ships it with no in-app caller;
the HTTP receiver that calls it lands in B3. Callers must wrap the call in an
active Flask application context.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass

from src.app.models import Capture
from src.app.models.db import db
from src.capture.content_hash import (
    CONTENT_HASH_RECIPE_VERSION,
    canonical_json,
    content_hash,
    sha256_hex,
)
from src.capture.paths import ensure_inbox_layout, new_dir, tmp_dir
from src.capture.registry import validate_envelope


@dataclass(slots=True, frozen=True)
class CaptureEnvelope:
    """An inbound capture payload, before it reaches the ledger.

    ``metadata`` and ``hints`` use ``None`` (not ``{}``) for "absent" so that
    omitted-vs-empty stays unambiguous in the canonical JSON document.
    """

    adapter_id: str
    adapter_version: str
    payload_kind: str
    body_text: str
    body_html: str | None
    source_url: str | None
    source_title: str | None
    metadata: dict | None
    hints: dict | None
    captured_at_unix: float


@dataclass(slots=True, frozen=True)
class CaptureResult:
    """The outcome of a record_capture call.

    ``existed`` is True when the envelope deduplicated against a stored row;
    ``filesystem_path`` is surfaced on both the new and the dedup path.
    """

    capture_id: int
    content_hash: str
    raw_payload_hash: str
    existed: bool
    filesystem_path: str | None


def _optional_json(value: dict | None) -> str | None:
    """Serialize an optional dict to canonical JSON; ``None`` stays ``None``."""

    if value is None:
        return None
    return canonical_json(value)


def record_capture(envelope: CaptureEnvelope) -> CaptureResult:
    """Persist a capture envelope to the ledger plus a durable filesystem mirror.

    Behavior, in order:
      1. Compute content_hash via the recipe-v1 helper.
      2. Compute raw_payload_hash = sha256_hex(canonical_json(envelope)).
      3. Dedup: if a Capture row with the same content_hash exists, return a
         CaptureResult(existed=True, ...) carrying that row's id and stored
         filesystem_path. No filesystem write, no DB commit.
      4. Validate the envelope against its adapter contract.
      5. Ensure the inbox layout, write canonical JSON to inbox/tmp/<uuid>.json,
         then os.replace() it to inbox/new/<uuid>.json.
      6. Insert a Capture row with status='pending' and filesystem_path stored
         relative to inbox_root() ("new/<uuid>.json").
      7. Commit once.
      8. Return CaptureResult(existed=False, ...).

    Lifecycle columns (triaged_at_unix onward) are left NULL; B2 writes them.

    Caller responsibility: an active Flask application context must wrap the
    call.
    """

    content_hash_value = content_hash(
        envelope.adapter_id,
        envelope.payload_kind,
        envelope.body_text,
        envelope.source_url,
        envelope.captured_at_unix,
    )
    document = canonical_json(envelope)
    raw_payload_hash = sha256_hex(document)

    existing = Capture.query.filter_by(content_hash=content_hash_value).first()
    if existing is not None:
        return CaptureResult(
            capture_id=existing.id,
            content_hash=content_hash_value,
            raw_payload_hash=raw_payload_hash,
            existed=True,
            filesystem_path=existing.filesystem_path,
        )

    validate_envelope(envelope)

    ensure_inbox_layout()
    filename = f"{uuid.uuid4().hex}.json"
    tmp_path = tmp_dir() / filename
    new_path = new_dir() / filename
    tmp_path.write_text(document, encoding="utf-8")
    os.replace(tmp_path, new_path)
    relative_path = f"new/{filename}"

    row = Capture(
        adapter_id=envelope.adapter_id,
        adapter_version=envelope.adapter_version,
        payload_kind=envelope.payload_kind,
        body_text=envelope.body_text,
        body_html=envelope.body_html,
        source_url=envelope.source_url,
        source_title=envelope.source_title,
        metadata_json=_optional_json(envelope.metadata),
        hints_json=_optional_json(envelope.hints),
        content_hash=content_hash_value,
        content_hash_recipe_version=CONTENT_HASH_RECIPE_VERSION,
        raw_payload_hash=raw_payload_hash,
        captured_at_unix=envelope.captured_at_unix,
        received_at_unix=time.time(),
        status="pending",
        filesystem_path=relative_path,
    )
    db.session.add(row)
    db.session.flush()
    capture_id = row.id
    db.session.commit()

    return CaptureResult(
        capture_id=capture_id,
        content_hash=content_hash_value,
        raw_payload_hash=raw_payload_hash,
        existed=False,
        filesystem_path=relative_path,
    )
