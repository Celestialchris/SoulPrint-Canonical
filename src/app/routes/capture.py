"""POST /api/capture: the HTTP capture receiver blueprint.

Accepts capture envelopes from local adapters (the CLI sender, the future
browser extension, the app's own save and clip surfaces), gates the endpoint
on the local capture secret, validates each envelope against the adapter
registry, and delegates persistence to ``record_capture``. The whole endpoint
is disabled with 503 until ``SOULPRINT_CAPTURE_TOKEN`` is configured.
"""

from __future__ import annotations

import hmac

from flask import Blueprint, current_app, jsonify, request

from src.capture.registry import CAPTURE_ADAPTERS, CaptureContractError

capture_bp = Blueprint("capture", __name__)


def _parse_envelope_fields(body: dict) -> dict | None:
    """Extract and type-check the ten CaptureEnvelope fields from a JSON body.

    Returns a dict of constructor arguments, or ``None`` when a required field
    is missing or any field has the wrong type. The adapter registry and
    ``record_capture`` enforce the contract beyond shape; this only guards
    construction so a malformed body becomes a clean 400 rather than a 500.
    """

    fields: dict = {}

    for name in ("adapter_id", "adapter_version", "payload_kind", "body_text"):
        value = body.get(name)
        if not isinstance(value, str):
            return None
        fields[name] = value

    captured_at = body.get("captured_at_unix")
    # bool is an int subclass; reject it explicitly so True/False is not a time.
    if isinstance(captured_at, bool) or not isinstance(captured_at, (int, float)):
        return None
    fields["captured_at_unix"] = float(captured_at)

    for name in ("body_html", "source_url", "source_title"):
        value = body.get(name)
        if value is not None and not isinstance(value, str):
            return None
        fields[name] = value

    for name in ("metadata", "hints"):
        value = body.get(name)
        if value is not None and not isinstance(value, dict):
            return None
        fields[name] = value

    return fields


@capture_bp.post("/api/capture")
def api_capture():
    """Receive a capture envelope, gate it, validate it, and persist it.

    503 when the receiver is unconfigured, 401 on a bad token, 413 on an
    oversize body, 400 on any other envelope error, 201 on a newly stored
    capture, 200 when the envelope deduplicated against a stored row.
    """

    # 1-2. The local capture secret gates the whole endpoint. Read per request
    # (never cached) and checked before the body is parsed, so a misconfigured
    # install fails fast and an oversize body pays no parsing cost.
    configured_token = current_app.config.get("SOULPRINT_CAPTURE_TOKEN", "")
    if not configured_token:
        return (
            jsonify(
                {
                    "error": "capture_disabled",
                    "message": "SOULPRINT_CAPTURE_TOKEN is not configured.",
                }
            ),
            503,
        )

    # 3. The body must parse as a JSON object.
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body must be a JSON object.",
                }
            ),
            400,
        )

    # 4. The adapter must be registered.
    adapter_id = body.get("adapter_id")
    contract = (
        CAPTURE_ADAPTERS.get(adapter_id) if isinstance(adapter_id, str) else None
    )
    if contract is None:
        return (
            jsonify(
                {
                    "error": "unknown_adapter",
                    "message": f"Unknown capture adapter: {adapter_id!r}",
                }
            ),
            400,
        )

    # 5. Token-gated adapters need a matching bearer token. compare_digest is
    # constant-time; a plain == would leak the token through response timing.
    # An absent or malformed Authorization header yields an empty candidate,
    # which fails the comparison and 401s like any mismatch.
    if contract.requires_token:
        auth_header = request.headers.get("Authorization", "")
        candidate = (
            auth_header[len("Bearer ") :].strip()
            if auth_header.startswith("Bearer ")
            else ""
        )
        if not hmac.compare_digest(
            candidate.encode("utf-8"), configured_token.encode("utf-8")
        ):
            return (
                jsonify(
                    {
                        "error": "unauthorized",
                        "message": "A valid capture token is required for this adapter.",
                    }
                ),
                401,
            )

    # 6. The required envelope fields must be present and well-typed.
    fields = _parse_envelope_fields(body)
    if fields is None:
        return (
            jsonify(
                {
                    "error": "invalid_envelope",
                    "message": (
                        "The capture envelope is missing required fields or "
                        "has fields of the wrong type."
                    ),
                }
            ),
            400,
        )

    # 7. The payload kind must be one the adapter is allowed to submit.
    if fields["payload_kind"] not in contract.payload_kinds_allowed:
        return (
            jsonify(
                {
                    "error": "invalid_payload_kind",
                    "message": (
                        f"Payload kind {fields['payload_kind']!r} is not allowed "
                        f"for adapter {fields['adapter_id']!r}."
                    ),
                }
            ),
            400,
        )

    # 8. Oversize bodies are rejected before record_capture pays the SHA-256
    # cost (PA9: validation precedes compute).
    body_size = len(fields["body_text"].encode("utf-8"))
    if body_size > contract.body_size_limit_bytes:
        return (
            jsonify(
                {
                    "error": "body_too_large",
                    "message": (
                        f"Body size {body_size} bytes exceeds the "
                        f"{contract.body_size_limit_bytes}-byte limit for "
                        f"adapter {fields['adapter_id']!r}."
                    ),
                }
            ),
            413,
        )

    # 9. Delegate to the persistence service. The import is function-local:
    # src.capture.service imports src.app.models, so a module-level import here
    # would cycle through the app factory that registers this blueprint.
    from src.capture.service import CaptureEnvelope, record_capture

    try:
        result = record_capture(CaptureEnvelope(**fields))
    except CaptureContractError as exc:
        # Defense in depth: steps 4-8 should have caught every contract error.
        return (
            jsonify({"error": "contract_violation", "message": str(exc)}),
            400,
        )

    # 10. 201 for a freshly stored capture, 200 for a dedup hit.
    return (
        jsonify({"capture_id": result.capture_id, "existed": result.existed}),
        200 if result.existed else 201,
    )
