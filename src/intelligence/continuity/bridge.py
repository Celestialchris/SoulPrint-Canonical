"""Bridge assembly for next-chat handoff — compact operational continuity.

Assembles a bounded handoff payload from continuity artifacts (and optionally
parent artifacts), producing a "bridge" artifact that is derived, provenance-
aware, and compact enough to paste into a fresh chat (~1k-3k tokens).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import ContinuityArtifact, make_artifact_id, make_timestamp
from .store import append_artifact


# ---------------------------------------------------------------------------
# Budget: ~1k-3k tokens ≈ 4k-12k chars.  Hard cap at 12k chars.
# ---------------------------------------------------------------------------
MAX_BRIDGE_CHARS = 12_000

BRIDGE_PROMPT_VERSION = "bridge-v1"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BridgeResult:
    """Outcome of one bridge assembly run."""

    bridge_text: str
    artifact: ContinuityArtifact | None
    source_conversation_ids: list[str]
    parent_packet_ids: list[str]
    error: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _latest_by_type(artifacts: list[dict], artifact_type: str) -> dict | None:
    """Return the first (newest) artifact matching *artifact_type*."""
    for a in artifacts:
        if a.get("artifact_type") == artifact_type:
            return a
    return None


def _section(heading: str, body: str) -> str:
    """Format one bridge section.  Returns empty string when body is blank."""
    stripped = body.strip()
    if not stripped:
        return ""
    return f"## {heading}\n{stripped}\n"


def _truncate(text: str, max_chars: int) -> str:
    """Truncate to *max_chars*, breaking at a line boundary when possible."""
    if len(text) <= max_chars:
        return text
    suffix = "\n[truncated]"
    budget = max_chars - len(suffix)
    cut = text[:budget]
    last_nl = cut.rfind("\n")
    if last_nl > budget * 0.5:
        cut = cut[:last_nl]
    return cut.rstrip() + suffix


def _next_step_seed(open_loops_artifact: dict | None) -> str:
    """Derive a suggested next-step prompt seed from open loops."""
    if open_loops_artifact is None:
        return ""
    cj = open_loops_artifact.get("content_json") or {}
    items = cj.get("open_loops", [])
    if not items:
        # Fall back to content_text if no structured JSON
        raw = open_loops_artifact.get("content_text", "").strip()
        if raw:
            return f"Continue from these open threads:\n{raw}"
        return ""
    lines = ["Continue from these open threads:"]
    for item in items[:5]:
        lines.append(f"- {item}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def assemble_bridge_text(
    artifacts: list[dict],
    parent_artifacts: list[dict] | None = None,
    conversation_title: str = "",
) -> str:
    """Build a compact handoff string from continuity + optional parent artifacts.

    Sections produced:
      - Prior Objective  (from summary)
      - Prior Context    (from parent summary, if parents given)
      - Key Decisions    (from decisions)
      - Open Loops       (from open_loops)
      - Key Entities     (from entity_map)
      - Suggested Next Step  (derived from open_loops)

    The output is capped at ``MAX_BRIDGE_CHARS``.
    """
    parent_artifacts = parent_artifacts or []

    summary = _latest_by_type(artifacts, "summary")
    decisions = _latest_by_type(artifacts, "decisions")
    open_loops = _latest_by_type(artifacts, "open_loops")
    entity_map = _latest_by_type(artifacts, "entity_map")

    parts: list[str] = []

    # -- header --
    header = "# Continuity Bridge"
    if conversation_title:
        header += f": {conversation_title}"
    parts.append(header)
    parts.append("*Derived handoff — not canonical.*\n")

    # -- prior objective --
    if summary:
        parts.append(_section("Prior Objective", summary.get("content_text", "")))

    # -- parent context --
    if parent_artifacts:
        parent_summary = _latest_by_type(parent_artifacts, "summary")
        parent_decisions = _latest_by_type(parent_artifacts, "decisions")
        parent_parts: list[str] = []
        if parent_summary:
            parent_parts.append(parent_summary.get("content_text", ""))
        if parent_decisions:
            parent_parts.append(parent_decisions.get("content_text", ""))
        combined = "\n\n".join(p for p in parent_parts if p.strip())
        if combined:
            parts.append(_section("Prior Context (from parent)", combined))

    # -- key decisions --
    if decisions:
        parts.append(_section("Key Decisions", decisions.get("content_text", "")))

    # -- open loops --
    if open_loops:
        parts.append(_section("Open Loops", open_loops.get("content_text", "")))

    # -- entities / constraints --
    if entity_map:
        parts.append(_section("Key Entities", entity_map.get("content_text", "")))

    # -- next-step seed --
    seed = _next_step_seed(open_loops)
    if seed:
        parts.append(_section("Suggested Next Step", seed))

    bridge = "\n".join(p for p in parts if p)
    return _truncate(bridge, MAX_BRIDGE_CHARS)


def assemble_bridge(
    conversation_stable_id: str,
    artifacts: list[dict],
    parent_artifacts: list[dict] | None = None,
    conversation_title: str = "",
    store_path: str | Path | None = None,
) -> BridgeResult:
    """Assemble a bridge artifact and optionally persist it.

    Parameters
    ----------
    conversation_stable_id:
        Stable ID of the primary conversation (e.g. ``imported_conversation:42``).
    artifacts:
        Continuity artifacts for the primary conversation (newest-first dicts).
    parent_artifacts:
        Optional continuity artifacts from one or two parent conversations.
    conversation_title:
        Human-readable title for the bridge header.
    store_path:
        If given, the bridge artifact is appended to this JSONL store.

    Returns a ``BridgeResult`` with the assembled text and metadata.
    """
    parent_artifacts = parent_artifacts or []

    if not artifacts:
        return BridgeResult(
            bridge_text="",
            artifact=None,
            source_conversation_ids=[conversation_stable_id],
            parent_packet_ids=[],
            error="No continuity artifacts available for bridge assembly.",
        )

    bridge_text = assemble_bridge_text(
        artifacts, parent_artifacts, conversation_title,
    )

    # Collect provenance
    source_ids: set[str] = set()
    for a in artifacts + parent_artifacts:
        for sid in a.get("source_conversation_ids", []):
            source_ids.add(sid)
    source_ids.add(conversation_stable_id)

    parent_ids = [
        a["artifact_id"]
        for a in parent_artifacts
        if a.get("artifact_id")
    ]

    artifact = ContinuityArtifact(
        artifact_id=make_artifact_id(),
        artifact_type="bridge",
        source_conversation_ids=sorted(source_ids),
        generation_timestamp=make_timestamp(),
        llm_provider_used="bridge_assembler",
        prompt_template_version=BRIDGE_PROMPT_VERSION,
        content_text=bridge_text,
        parent_packet_ids=parent_ids,
    )

    if store_path is not None:
        append_artifact(Path(store_path), artifact)

    return BridgeResult(
        bridge_text=bridge_text,
        artifact=artifact,
        source_conversation_ids=sorted(source_ids),
        parent_packet_ids=parent_ids,
    )
