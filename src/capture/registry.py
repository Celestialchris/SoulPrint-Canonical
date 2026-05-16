"""Capture adapter registry and envelope contract validation.

The registry is the v1 allow-list of capture sources. Each adapter declares
its latest version, the payload kinds it may submit, a UTF-8 body size limit,
and whether it requires a token. ``requires_token`` is stored for the HTTP
receiver (B3) but is not enforced here in B1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.capture.service import CaptureEnvelope


class CaptureContractError(ValueError):
    """Raised when a capture envelope violates its adapter contract."""


@dataclass(slots=True, frozen=True)
class AdapterContract:
    """Frozen v1 contract for a single capture adapter."""

    latest_version: str
    payload_kinds_allowed: tuple[str, ...]
    body_size_limit_bytes: int
    requires_token: bool


CAPTURE_ADAPTERS: dict[str, AdapterContract] = {
    "soulprint-app-save": AdapterContract(
        latest_version="1",
        payload_kinds_allowed=("paste", "markdown"),
        body_size_limit_bytes=64 * 1024,
        requires_token=False,
    ),
    "soulprint-app-clip": AdapterContract(
        latest_version="1",
        payload_kinds_allowed=("clip-from-message",),
        body_size_limit_bytes=64 * 1024,
        requires_token=False,
    ),
    "soulprint-cli": AdapterContract(
        latest_version="1",
        payload_kinds_allowed=("paste", "markdown", "text"),
        body_size_limit_bytes=256 * 1024,
        requires_token=True,
    ),
}


def validate_envelope(envelope: CaptureEnvelope) -> None:
    """Validate a capture envelope against its adapter contract.

    Raises:
        CaptureContractError: if the adapter id is not registered, the payload
            kind is not allowed for that adapter, or the UTF-8 body exceeds the
            adapter's size limit.
    """

    contract = CAPTURE_ADAPTERS.get(envelope.adapter_id)
    if contract is None:
        raise CaptureContractError(
            f"Unknown capture adapter: {envelope.adapter_id!r}"
        )

    if envelope.payload_kind not in contract.payload_kinds_allowed:
        raise CaptureContractError(
            f"Payload kind {envelope.payload_kind!r} is not allowed for "
            f"adapter {envelope.adapter_id!r}"
        )

    body_size = len(envelope.body_text.encode("utf-8"))
    if body_size > contract.body_size_limit_bytes:
        raise CaptureContractError(
            f"Body size {body_size} bytes exceeds the "
            f"{contract.body_size_limit_bytes}-byte limit for adapter "
            f"{envelope.adapter_id!r}"
        )
