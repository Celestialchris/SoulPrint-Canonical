"""Content hash recipe v1 and supporting serialization helpers.

``canonical_json`` is frozen alongside recipe v1. Any change to its
serialization rules (``sort_keys``, ``separators``, ``ensure_ascii``) requires
a future schema migration that adds a ``raw_payload_hash_recipe_version``
column to the capture table, mirroring ``content_hash_recipe_version``. Do not
modify ``canonical_json``'s parameters in this module without that migration
in place.

Likewise, any change to the ``content_hash`` recipe requires bumping
``CONTENT_HASH_RECIPE_VERSION`` to 2 and never reusing v1 hashes.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import unicodedata
from typing import Any

CONTENT_HASH_RECIPE_VERSION = 1


def sha256_hex(data: str | bytes) -> str:
    """Return the hex SHA-256 digest of ``data`` (str input is UTF-8 encoded)."""

    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    """Serialize ``obj`` to deterministic JSON, frozen alongside recipe v1.

    Dataclass instances are converted via ``dataclasses.asdict`` first. Keys
    are sorted and separators are compact, so the output is identical
    regardless of input key order.
    """

    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        obj = dataclasses.asdict(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(
    adapter_id: str,
    payload_kind: str,
    body_text: str,
    source_url: str | None,
    captured_at_unix: float,
) -> str:
    """Compute the recipe-v1 content hash for a capture envelope.

    Stability properties: ``captured_at_unix`` is truncated to a minute
    boundary, ``body_text`` is NFC-normalized and right-stripped, and a
    ``source_url`` of ``None`` hashes identically to an empty string.
    """

    minute_truncated = (int(captured_at_unix) // 60) * 60
    normalized_body = unicodedata.normalize("NFC", body_text).rstrip()

    parts = [
        adapter_id,
        payload_kind,
        normalized_body,
        source_url or "",
        str(minute_truncated),
    ]
    payload = "\x00".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
