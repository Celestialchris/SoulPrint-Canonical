"""Capture lifecycle state machine: the explicit transition matrix.

``record_capture`` (Campaign 03 B1) creates every capture row as ``pending``.
From there a row moves through five states:

    pending      -> triaged | promoted | rejected | quarantined
    triaged      -> promoted | rejected | quarantined
    quarantined  -> triaged  | rejected
    promoted     -> (terminal)
    rejected     -> (terminal)

``promoted`` and ``rejected`` are terminal: no transition leaves them. A
repeated transition into a state a row already holds (``pending -> pending``,
``promoted -> promoted``, ...) is an error, never a silent no-op; the matrix
contains no self-loops. ``quarantined`` recovers only through ``triaged``;
there is no direct ``quarantined -> promoted`` edge.

This module is pure: it has no database, Flask, or runtime import. The service
layer (``src/capture/service.py``) calls ``transition`` as a pre-flight check
and then enforces the matrix again at write time with a compare-and-swap
conditional UPDATE, so concurrency safety does not depend on this module.
"""

from __future__ import annotations

VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending":     frozenset({"triaged", "promoted", "rejected", "quarantined"}),
    "triaged":     frozenset({"promoted", "rejected", "quarantined"}),
    "quarantined": frozenset({"triaged", "rejected"}),
    "promoted":    frozenset(),   # terminal
    "rejected":    frozenset(),   # terminal
}

TERMINAL_STATES: frozenset[str] = frozenset({"promoted", "rejected"})

VALID_STATUSES: frozenset[str] = frozenset(VALID_TRANSITIONS.keys())


class InvalidTransitionError(ValueError):
    """Raised when a state transition is not permitted by VALID_TRANSITIONS."""


def transition(from_status: str, to_status: str) -> None:
    """Validate that from_status -> to_status is permitted.

    Raises:
        InvalidTransitionError if from_status is unknown, to_status is
        unknown, or the transition is not in VALID_TRANSITIONS[from_status].
    """

    if from_status not in VALID_TRANSITIONS:
        raise InvalidTransitionError(f"Unknown source status: {from_status!r}")
    if to_status not in VALID_STATUSES:
        raise InvalidTransitionError(f"Unknown target status: {to_status!r}")
    if to_status not in VALID_TRANSITIONS[from_status]:
        raise InvalidTransitionError(
            f"Transition {from_status!r} -> {to_status!r} is not permitted"
        )
