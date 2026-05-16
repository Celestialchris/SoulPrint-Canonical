"""GET /inbox: the keyboard-driven capture inbox cockpit.

Renders the pending capture queue for the local operator. The three action
routes (promote, reject, quarantine) and the same-origin guard land in B3's
U4 cluster.
"""

from __future__ import annotations

from flask import Blueprint, render_template

from ..models import Capture

inbox_bp = Blueprint("inbox", __name__)


@inbox_bp.get("/inbox")
def show_inbox():
    """Render every pending capture, newest first."""

    captures = (
        Capture.query.filter_by(status="pending")
        .order_by(Capture.received_at_unix.desc())
        .all()
    )
    return render_template("inbox.html", captures=captures)
