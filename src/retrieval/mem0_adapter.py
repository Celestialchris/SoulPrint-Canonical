"""Optional mem0 adapter boundary.

This module intentionally provides a minimal, dependency-free boundary so
future mem0 integration can be added without changing canonical storage flows.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .federated import FederatedReadResult


@dataclass(frozen=True)
class IngestReport:
    """Result summary for best-effort mem0 ingest attempts."""

    enabled: bool
    attempted: int
    accepted: int
    skipped: int
    failed: int


@dataclass(frozen=True)
class Mem0Hit:
    """Placeholder hit shape for future mem0 query integration."""

    pointer: dict[str, Any]
    score: float | None = None


@dataclass(frozen=True)
class HydratedResult:
    """Placeholder hydrated shape for future canonical rehydration."""

    hit: Mem0Hit
    hydrated: bool
    canonical: "FederatedReadResult" | None


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def mem0_enabled() -> bool:
    """Return whether the optional mem0 boundary is enabled."""

    return _env_flag("SOULPRINT_MEM0_ENABLED", default=False)


def mem0_write_mode() -> str:
    """Return adapter write mode with a safe best-effort default."""

    return os.getenv("SOULPRINT_MEM0_WRITE_MODE", "best_effort").strip().lower()


def mem0_timeout_ms() -> int:
    """Return bounded timeout configuration for future mem0 calls."""

    raw = os.getenv("SOULPRINT_MEM0_TIMEOUT_MS", "250")
    try:
        value = int(raw)
    except ValueError:
        return 250
    return max(1, value)


def _canonical_pointer_payload(item: "FederatedReadResult") -> dict[str, Any]:
    """Build the canonical pointer payload required by the mem0 boundary memo."""

    return {
        "canonical": {
            "source_lane": item.source_lane,
            "stable_id": item.stable_id,
            "timestamp_unix": item.timestamp_unix,
            "source_metadata": dict(item.source_metadata),
        }
    }


def ingest_federated_items(items: list["FederatedReadResult"]) -> IngestReport:
    """Best-effort ingest entrypoint.

    Current implementation is a safe no-op that validates canonical pointer
    requirements and prepares payloads without external side effects.
    """

    if not mem0_enabled():
        return IngestReport(enabled=False, attempted=0, accepted=0, skipped=len(items), failed=0)

    accepted = 0
    failed = 0
    for item in items:
        if not item.source_lane or not item.stable_id:
            failed += 1
            continue
        _canonical_pointer_payload(item)
        accepted += 1

    return IngestReport(
        enabled=True,
        attempted=len(items),
        accepted=accepted,
        skipped=0,
        failed=failed,
    )


def query_mem0(*_: Any, **__: Any) -> list[Mem0Hit]:
    """Placeholder mem0 query boundary (no-op until dependency is added)."""

    if not mem0_enabled():
        return []
    return []


def hydrate_mem0_hits(hits: list[Mem0Hit]) -> list[HydratedResult]:
    """Placeholder hydration boundary.

    Future versions should resolve canonical pointers through lane readers.
    """

    if not mem0_enabled():
        return []

    return [HydratedResult(hit=hit, hydrated=False, canonical=None) for hit in hits]
