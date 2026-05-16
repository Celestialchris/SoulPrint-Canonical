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

from sqlalchemy.exc import IntegrityError

from src.app.models import Capture
from src.app.models.db import db
from src.capture.content_hash import (
    CONTENT_HASH_RECIPE_VERSION,
    canonical_json,
    content_hash,
    sha256_hex,
)
from src.capture.lifecycle import InvalidTransitionError, transition
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


def _existing_capture_result(existing: Capture) -> CaptureResult:
    """Build the existed=True CaptureResult for an already-stored capture."""

    return CaptureResult(
        capture_id=existing.id,
        content_hash=existing.content_hash,
        raw_payload_hash=existing.raw_payload_hash,
        existed=True,
        filesystem_path=existing.filesystem_path,
    )


def record_capture(envelope: CaptureEnvelope) -> CaptureResult:
    """Persist a capture envelope to the ledger plus a durable filesystem mirror.

    Behavior, in order:
      1. Validate the envelope against its adapter contract.
      2. Compute content_hash via the recipe-v1 helper.
      3. Compute raw_payload_hash = sha256_hex(canonical_json(envelope)).
      4. Dedup pre-check: if a Capture row with the same content_hash already
         exists, return a CaptureResult(existed=True, ...) describing that
         stored row. No filesystem write, no DB commit.
      5. Ensure the inbox layout, write canonical JSON to inbox/tmp/<uuid>.json,
         then os.replace() it to inbox/new/<uuid>.json.
      6. Insert a Capture row with status='pending' and filesystem_path stored
         relative to inbox_root() ("new/<uuid>.json").
      7. Commit once.
      8. Return CaptureResult(existed=False, ...).

    Validation is step 1 by design: an envelope that violates its adapter
    contract (oversized body, unknown adapter, disallowed payload kind) is
    rejected before any hashing, canonicalization, or dedup work runs.

    Dedup is atomic. Step 4 is only a fast path; the authority is the unique
    index on capture.content_hash. If a concurrent capture commits the same
    content_hash after step 4, the step 6 insert raises IntegrityError; the
    filesystem mirror from step 5 is removed, the transaction is rolled back,
    and the stored winner is returned as a CaptureResult(existed=True, ...),
    the same outcome as step 4.

    Every existed=True CaptureResult describes the stored row, never the
    rejected incoming envelope. A content_hash match can still differ on
    raw_payload_hash: the recipe-v1 content hash excludes adapter_version,
    body_html, source_title, metadata, hints, sub-minute timestamp precision,
    and trailing body whitespace, while raw_payload_hash covers all of them.

    Lifecycle columns (triaged_at_unix onward) are left NULL; B2 writes them.

    Caller responsibility: an active Flask application context must wrap the
    call.
    """

    validate_envelope(envelope)

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
        return _existing_capture_result(existing)

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
    try:
        db.session.flush()
    except IntegrityError:
        # A concurrent capture committed the same content_hash between the
        # step 3 pre-check and this insert; the unique index rejected ours.
        # Undo our partial work and return the stored winner.
        db.session.rollback()
        new_path.unlink(missing_ok=True)
        existing = Capture.query.filter_by(content_hash=content_hash_value).first()
        if existing is None:
            raise
        return _existing_capture_result(existing)
    capture_id = row.id
    db.session.commit()

    return CaptureResult(
        capture_id=capture_id,
        content_hash=content_hash_value,
        raw_payload_hash=raw_payload_hash,
        existed=False,
        filesystem_path=relative_path,
    )


class CaptureNotFoundError(LookupError):
    """Raised when a capture_id does not match any row."""


@dataclass(slots=True, frozen=True)
class LifecycleResult:
    """The outcome of a capture lifecycle transition.

    For terminal transitions (reject, quarantine), ``decided_at_unix`` and
    ``decided_by`` are set. For the intermediate triage transition both are
    None, because triage is not a decision outcome and writes neither column.
    """

    capture_id: int
    from_status: str
    to_status: str
    decided_at_unix: float | None
    decided_by: str | None


def _transition_capture(
    capture_id: int,
    *,
    target_status: str,
    allowed_sources: tuple[str, ...],
    values: dict[str, float | str],
) -> str:
    """Compare-and-swap a capture row to ``target_status``; return its prior status.

    Loads the row, validates the transition against the lifecycle matrix as a
    pre-flight check, then issues a conditional UPDATE whose WHERE clause names
    both the id and the permitted source statuses. A rowcount of 0 means a
    concurrent transition moved the row between the pre-flight read and the
    UPDATE: the loser rolls back and raises rather than overwriting the winner.

    Raises:
        CaptureNotFoundError: if no row has this capture_id.
        InvalidTransitionError: if the transition is illegal, or if it lost a
            concurrency race (the row is no longer in an allowed source state).
    """

    row = db.session.get(Capture, capture_id)
    if row is None:
        raise CaptureNotFoundError(f"No capture row with id {capture_id!r}")
    from_status = row.status
    transition(from_status, target_status)

    result = db.session.execute(
        db.update(Capture)
        .where(Capture.id == capture_id)
        .where(Capture.status.in_(allowed_sources))
        .values(status=target_status, **values)
    )
    if result.rowcount == 0:
        db.session.rollback()
        current = db.session.get(Capture, capture_id)
        if current is None:
            raise CaptureNotFoundError(f"No capture row with id {capture_id!r}")
        raise InvalidTransitionError(
            f"Cannot transition capture {capture_id} from {current.status!r} "
            f"to {target_status!r}"
        )
    db.session.commit()
    return from_status


def reject_capture(
    capture_id: int, reason: str, *, decided_by: str
) -> LifecycleResult:
    """Reject a capture, recording who decided and why.

    Valid from pending, triaged, or quarantined. ``decided_by`` is a required
    keyword-only argument so the audit trail is never silently unattributed.
    The inbox filesystem mirror is retained: a rejected payload is audit-trail
    evidence, not deleted.

    Caller responsibility: an active Flask application context must wrap the
    call.
    """

    now = time.time()
    from_status = _transition_capture(
        capture_id,
        target_status="rejected",
        # quarantined -> rejected is a valid matrix edge: a held capture may
        # be rejected outright. quarantine and promote do not accept it.
        allowed_sources=("pending", "triaged", "quarantined"),
        values={
            "decided_at_unix": now,
            "decided_by": decided_by,
            "reject_reason": reason,
        },
    )
    return LifecycleResult(
        capture_id=capture_id,
        from_status=from_status,
        to_status="rejected",
        decided_at_unix=now,
        decided_by=decided_by,
    )


def quarantine_capture(
    capture_id: int, reason: str, *, decided_by: str
) -> LifecycleResult:
    """Quarantine a capture, recording who decided and why.

    Valid from pending or triaged. ``decided_by`` is a required keyword-only
    argument. The inbox filesystem mirror is retained; quarantine has
    indefinite retention, and recovery is the quarantined -> triaged edge.

    Caller responsibility: an active Flask application context must wrap the
    call.
    """

    now = time.time()
    from_status = _transition_capture(
        capture_id,
        target_status="quarantined",
        allowed_sources=("pending", "triaged"),
        values={
            "decided_at_unix": now,
            "decided_by": decided_by,
            "quarantine_reason": reason,
        },
    )
    return LifecycleResult(
        capture_id=capture_id,
        from_status=from_status,
        to_status="quarantined",
        decided_at_unix=now,
        decided_by=decided_by,
    )


def triage_capture(capture_id: int) -> LifecycleResult:
    """Move a capture into the triaged state.

    Valid from pending or quarantined (the quarantine recovery edge). Triage
    is an intermediate transition, not a decision outcome: it writes only
    ``triaged_at_unix`` and leaves ``decided_at_unix`` and ``decided_by`` NULL
    until a terminal transition. It therefore takes no ``decided_by``.

    Caller responsibility: an active Flask application context must wrap the
    call.
    """

    now = time.time()
    from_status = _transition_capture(
        capture_id,
        target_status="triaged",
        allowed_sources=("pending", "quarantined"),
        values={"triaged_at_unix": now},
    )
    return LifecycleResult(
        capture_id=capture_id,
        from_status=from_status,
        to_status="triaged",
        decided_at_unix=None,
        decided_by=None,
    )
