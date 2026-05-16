"""Tests for the capture lifecycle state machine and the status validator."""

from __future__ import annotations

import unittest

from flask import Flask

from src.app.models import Capture
from src.app.models.db import db
from src.capture.lifecycle import (
    TERMINAL_STATES,
    VALID_STATUSES,
    VALID_TRANSITIONS,
    InvalidTransitionError,
    sources_for,
    transition,
)
from tests.temp_helpers import make_test_temp_dir, release_app_db_handles


class TransitionMatrixTest(unittest.TestCase):
    """Pure-function tests for the lifecycle transition matrix."""

    def test_valid_transitions_pending(self):
        # pending reaches all four non-pending states directly.
        for target in ("triaged", "promoted", "rejected", "quarantined"):
            self.assertIsNone(transition("pending", target))

    def test_valid_transitions_triaged(self):
        for target in ("promoted", "rejected", "quarantined"):
            self.assertIsNone(transition("triaged", target))

    def test_valid_transitions_quarantined(self):
        # quarantined recovers via triaged or is rejected outright.
        for target in ("triaged", "rejected"):
            self.assertIsNone(transition("quarantined", target))

    def test_invalid_transitions_from_terminal_promoted(self):
        for target in VALID_STATUSES:
            with self.assertRaises(InvalidTransitionError):
                transition("promoted", target)

    def test_invalid_transitions_from_terminal_rejected(self):
        for target in VALID_STATUSES:
            with self.assertRaises(InvalidTransitionError):
                transition("rejected", target)

    def test_invalid_transition_repeated_same_state(self):
        # The matrix has no self-loops: a repeated transition is an error.
        for state in VALID_STATUSES:
            with self.assertRaises(InvalidTransitionError):
                transition(state, state)

    def test_transition_unknown_source_raises(self):
        with self.assertRaises(InvalidTransitionError):
            transition("bogus", "pending")

    def test_transition_unknown_target_raises(self):
        with self.assertRaises(InvalidTransitionError):
            transition("pending", "bogus")

    def test_terminal_states_constant_is_correct(self):
        self.assertEqual(TERMINAL_STATES, frozenset({"promoted", "rejected"}))
        # A terminal state has no outgoing edges in the matrix.
        for state in TERMINAL_STATES:
            self.assertEqual(VALID_TRANSITIONS[state], frozenset())

    def test_valid_statuses_constant_is_correct(self):
        self.assertEqual(
            VALID_STATUSES,
            frozenset(
                {"pending", "triaged", "promoted", "rejected", "quarantined"}
            ),
        )

    def test_invalid_transition_error_is_value_error(self):
        self.assertTrue(issubclass(InvalidTransitionError, ValueError))


class SourcesForTest(unittest.TestCase):
    """Pure-function tests for the sources_for transition-matrix inverter."""

    def test_sources_for_returns_inverse_per_target(self):
        # sources_for(target) is the set of statuses with an edge into target.
        expected = {
            "triaged": frozenset({"pending", "quarantined"}),
            "promoted": frozenset({"pending", "triaged"}),
            "rejected": frozenset({"pending", "triaged", "quarantined"}),
            "quarantined": frozenset({"pending", "triaged"}),
            "pending": frozenset(),
        }
        for target, sources in expected.items():
            self.assertEqual(sources_for(target), sources)

    def test_sources_for_pending_returns_empty(self):
        # pending is a valid status with no inbound edge: empty, not an error.
        self.assertEqual(sources_for("pending"), frozenset())

    def test_sources_for_unknown_raises(self):
        with self.assertRaises(InvalidTransitionError):
            sources_for("bogus")

    def test_sources_for_is_true_inverse(self):
        # Every source sources_for yields must carry the target in its own
        # forward edge set: sources_for is a genuine inverse of the matrix.
        for target in VALID_STATUSES:
            for src in sources_for(target):
                self.assertIn(target, VALID_TRANSITIONS[src])


class CaptureStatusValidatorTest(unittest.TestCase):
    """Tests for the @validates("status") guard on the Capture model."""

    def setUp(self):
        self.workdir = make_test_temp_dir(self, "capture-lifecycle-validator")
        self.db_path = str(self.workdir / "validator.db")

        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)

    def test_capture_validates_status_rejects_unknown(self):
        with self.app.app_context():
            with self.assertRaises(ValueError):
                Capture(status="bogus")

    def test_capture_validates_status_accepts_all_valid(self):
        with self.app.app_context():
            for status in VALID_STATUSES:
                row = Capture(status=status)
                self.assertEqual(row.status, status)

    def test_capture_validates_status_rejects_on_reassignment(self):
        # The validator fires on assignment, not just construction.
        with self.app.app_context():
            row = Capture(status="pending")
            with self.assertRaises(ValueError):
                row.status = "not-a-status"


if __name__ == "__main__":
    unittest.main()
