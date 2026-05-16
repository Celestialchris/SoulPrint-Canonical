"""The /inbox capture cockpit: the read view and the three action routes.

GET /inbox renders the queue of captures awaiting a decision. POST
/inbox/<id>/promote, .../reject, and .../quarantine drive the B2 lifecycle
service and are guarded by a same-origin check.

src.capture.service is imported inside each action handler, not at module
scope: it imports src.app.models, which runs the app factory that registers
this blueprint, so a module-level import would cycle.
"""

from __future__ import annotations

import logging
from functools import wraps
from urllib.parse import urlparse

from flask import Blueprint, abort, redirect, render_template, request, url_for

from src.capture.lifecycle import InvalidTransitionError

from ..models import Capture
from ..models.db import db

logger = logging.getLogger(__name__)

inbox_bp = Blueprint("inbox", __name__)


@inbox_bp.get("/inbox")
def show_inbox():
    """Render every capture awaiting a decision, newest first."""

    # pending and triaged both await a terminal decision and support the
    # promote/reject/quarantine actions; promoted, rejected, and quarantined
    # are excluded from the cockpit.
    captures = (
        Capture.query.filter(Capture.status.in_(("pending", "triaged")))
        .order_by(Capture.received_at_unix.desc())
        .all()
    )
    return render_template("inbox.html", captures=captures)


def same_origin_required(view):
    """Reject cross-origin and Origin-less POSTs to a mutating route.

    The browser sets Origin on every cross-origin and same-origin POST and a
    page script cannot forge it. A missing Origin fails closed: a genuine
    /inbox form submit always carries one, and the non-browser capture clients
    post to /api/capture, never to these action routes.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        origin = request.headers.get("Origin")
        if not origin:
            abort(403)
        if urlparse(origin).netloc != request.host:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@inbox_bp.post("/inbox/<int:capture_id>/promote")
@same_origin_required
def promote(capture_id: int):
    """Promote a pending or triaged capture into a canonical MemoryEntry."""

    from src.capture.service import CaptureNotFoundError, promote_capture

    try:
        result = promote_capture(capture_id, decided_by="operator", tags=None)
    except CaptureNotFoundError:
        abort(404)
    except InvalidTransitionError:
        abort(409)

    # FTS indexing is post-commit and best-effort, mirroring /save and
    # /api/clip: promote_capture has already committed the canonical
    # promotion, so an index failure logs a warning and the route still
    # returns 303 rather than implying the promotion failed.
    try:
        from src.retrieval.fts import index_new_note

        index_new_note(db.engine.url.database, result.memory_entry_id)
    except Exception:
        logger.warning("FTS indexing failed", exc_info=True)

    return redirect(url_for("inbox.show_inbox"), code=303)


@inbox_bp.post("/inbox/<int:capture_id>/reject")
@same_origin_required
def reject(capture_id: int):
    """Reject a capture, recording the operator's reason."""

    reason = request.form.get("reason", "").strip()
    if not reason:
        abort(400)

    from src.capture.service import CaptureNotFoundError, reject_capture

    try:
        reject_capture(capture_id, reason, decided_by="operator")
    except CaptureNotFoundError:
        abort(404)
    except InvalidTransitionError:
        abort(409)

    return redirect(url_for("inbox.show_inbox"), code=303)


@inbox_bp.post("/inbox/<int:capture_id>/quarantine")
@same_origin_required
def quarantine(capture_id: int):
    """Quarantine a capture, recording the operator's reason."""

    reason = request.form.get("reason", "").strip()
    if not reason:
        abort(400)

    from src.capture.service import CaptureNotFoundError, quarantine_capture

    try:
        quarantine_capture(capture_id, reason, decided_by="operator")
    except CaptureNotFoundError:
        abort(404)
    except InvalidTransitionError:
        abort(409)

    return redirect(url_for("inbox.show_inbox"), code=303)
