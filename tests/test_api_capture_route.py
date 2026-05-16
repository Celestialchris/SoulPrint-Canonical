"""Tests for the POST /api/capture receiver route (Campaign 03, B3)."""

from __future__ import annotations

import json
import unittest

from src.app import create_app
from src.app.models import Capture
from src.app.models.db import db
from src.config import Config
from tests.temp_helpers import (
    make_test_temp_dir,
    release_app_db_handles,
    temp_soulprint_home,
)

_CAPTURE_TOKEN = "test-capture-token"


class ApiCaptureRouteTest(unittest.TestCase):
    """Full-app tests for the POST /api/capture receiver."""

    def setUp(self):
        self.home = temp_soulprint_home(self, "api-capture-home")
        self.workdir = make_test_temp_dir(self, "api-capture-db")
        self.db_path = str(self.workdir / "api-capture.db")
        self._old_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path}"
        self.app = create_app()
        self.app.config["SOULPRINT_CAPTURE_TOKEN"] = _CAPTURE_TOKEN
        self.addCleanup(release_app_db_handles, self.app, drop_all=True)
        self.addCleanup(self._restore_uri)
        self.client = self.app.test_client()

    def _restore_uri(self):
        Config.SQLALCHEMY_DATABASE_URI = self._old_uri

    def _envelope(self, **overrides):
        """Build a valid soulprint-cli envelope dict; overrides replace fields."""

        payload = {
            "adapter_id": "soulprint-cli",
            "adapter_version": "1",
            "payload_kind": "paste",
            "body_text": "hello from the capture cli",
            "captured_at_unix": 1747227615.5,
        }
        payload.update(overrides)
        return payload

    def _capture_count(self):
        with self.app.app_context():
            return db.session.query(Capture).count()

    def test_post_valid_cli_envelope_returns_201(self):
        response = self.client.post(
            "/api/capture",
            json=self._envelope(),
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertFalse(payload["existed"])
        self.assertIsInstance(payload["capture_id"], int)
        with self.app.app_context():
            row = db.session.get(Capture, payload["capture_id"])
            self.assertIsNotNone(row)
            self.assertEqual(row.status, "pending")

    def test_post_valid_save_envelope_without_token_returns_201(self):
        # soulprint-app-save has requires_token=False: no Authorization header
        # is needed even though the receiver itself is configured with a token.
        response = self.client.post(
            "/api/capture",
            json=self._envelope(adapter_id="soulprint-app-save"),
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.get_json()["existed"])

    def test_post_duplicate_envelope_returns_200_existed(self):
        envelope = self._envelope()
        headers = {"Authorization": f"Bearer {_CAPTURE_TOKEN}"}

        first = self.client.post("/api/capture", json=envelope, headers=headers)
        second = self.client.post("/api/capture", json=envelope, headers=headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(first.get_json()["existed"])
        self.assertTrue(second.get_json()["existed"])
        self.assertEqual(
            first.get_json()["capture_id"], second.get_json()["capture_id"]
        )
        self.assertEqual(self._capture_count(), 1)

    def test_post_with_token_unconfigured_returns_503(self):
        self.app.config["SOULPRINT_CAPTURE_TOKEN"] = ""

        response = self.client.post(
            "/api/capture",
            json=self._envelope(),
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["error"], "capture_disabled")
        self.assertEqual(self._capture_count(), 0)

    def test_post_cli_without_authorization_returns_401(self):
        response = self.client.post("/api/capture", json=self._envelope())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "unauthorized")
        self.assertEqual(self._capture_count(), 0)

    def test_post_cli_with_wrong_token_returns_401(self):
        response = self.client.post(
            "/api/capture",
            json=self._envelope(),
            headers={"Authorization": "Bearer not-the-real-token"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "unauthorized")

    def test_post_non_object_body_returns_400_invalid_json(self):
        # A JSON array parses successfully but is not a JSON object.
        response = self.client.post(
            "/api/capture",
            json=["not", "an", "object"],
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_json")

    def test_post_unparseable_body_returns_400_invalid_json(self):
        response = self.client.post(
            "/api/capture",
            data="{not valid json",
            content_type="application/json",
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_json")

    def test_post_missing_required_field_returns_400_invalid_envelope(self):
        envelope = self._envelope()
        del envelope["body_text"]

        response = self.client.post(
            "/api/capture",
            json=envelope,
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_envelope")

    def test_post_nan_captured_at_returns_400_invalid_envelope(self):
        # json.dumps writes a bare NaN token that the JSON parser accepts, so
        # the non-finite value reaches the route and must be rejected there.
        raw_body = json.dumps(self._envelope(captured_at_unix=float("nan")))

        response = self.client.post(
            "/api/capture",
            data=raw_body,
            content_type="application/json",
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_envelope")
        self.assertEqual(self._capture_count(), 0)

    def test_post_infinite_captured_at_returns_400_invalid_envelope(self):
        raw_body = json.dumps(self._envelope(captured_at_unix=float("inf")))

        response = self.client.post(
            "/api/capture",
            data=raw_body,
            content_type="application/json",
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_envelope")
        self.assertEqual(self._capture_count(), 0)

    def test_post_unknown_adapter_returns_400(self):
        response = self.client.post(
            "/api/capture",
            json=self._envelope(adapter_id="adapter-does-not-exist"),
            headers={"Authorization": f"Bearer {_CAPTURE_TOKEN}"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "unknown_adapter")

    def test_post_disallowed_payload_kind_returns_400(self):
        # soulprint-app-clip permits only the "clip-from-message" payload kind.
        response = self.client.post(
            "/api/capture",
            json=self._envelope(
                adapter_id="soulprint-app-clip", payload_kind="paste"
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_payload_kind")

    def test_post_oversize_body_returns_413(self):
        # soulprint-app-save caps the body at 64 KiB.
        response = self.client.post(
            "/api/capture",
            json=self._envelope(
                adapter_id="soulprint-app-save",
                body_text="a" * (64 * 1024 + 1),
            ),
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.get_json()["error"], "body_too_large")
        self.assertEqual(self._capture_count(), 0)

    def test_get_capture_returns_405(self):
        response = self.client.get("/api/capture")

        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
