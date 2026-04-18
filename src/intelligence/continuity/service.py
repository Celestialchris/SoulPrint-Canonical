"""Continuity packet generation service — derives typed artifacts from canonical conversations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..provider import LLMProvider
from .models import ContinuityArtifact, make_artifact_id, make_timestamp
from .store import append_artifact


PROMPT_TEMPLATE_VERSION = "v1"

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContinuityPacketResult:
    """Outcome of one continuity packet generation run."""

    conversation_stable_id: str
    artifacts: list[ContinuityArtifact]
    error: str | None = None


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a continuity extraction engine. Given a conversation transcript, "
    "produce a structured JSON object with exactly four keys:\n"
    "\n"
    '  "summary": a concise paragraph capturing the core discussion,\n'
    '  "decisions": a list of strings — concrete decisions or conclusions reached,\n'
    '  "open_loops": a list of strings — unresolved questions, deferred items, or threads left open,\n'
    '  "entity_map": a list of strings — key people, projects, tools, or concepts referenced.\n'
    "\n"
    "Rules:\n"
    "- Be factual and grounded. Do not invent information not present in the transcript.\n"
    "- If a section has no entries, return an empty list.\n"
    "- Return ONLY the JSON object. No markdown, no commentary.\n"
)


def _build_transcript(conversation) -> str:
    """Format conversation messages into a compact transcript string.

    ``conversation`` must expose ``.messages`` (each with ``.role``,
    ``.content``, ``.sequence_index``).
    """
    sorted_messages = sorted(conversation.messages, key=lambda m: m.sequence_index)
    lines = [f"[{m.role}]: {m.content}" for m in sorted_messages]
    return "\n".join(lines)


def _parse_provider_response(raw: str) -> dict:
    """Extract the JSON object from the provider response.

    Tolerates leading/trailing whitespace and optional markdown fencing.
    """
    text = raw.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove first line (```json or ```) and last line (```)
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return json.loads(text)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate_continuity_packet(
    conversation,
    provider: LLMProvider | None,
    store_path: str | Path,
    prompt_version: str = PROMPT_TEMPLATE_VERSION,
) -> ContinuityPacketResult:
    """Generate continuity artifacts from one canonical conversation.

    ``conversation`` must expose ``.id``, ``.title``, and ``.messages``
    (each with ``.role``, ``.content``, ``.sequence_index``).

    Returns a ``ContinuityPacketResult`` with either artifacts or an error.
    Artifacts are persisted to ``store_path`` on success.
    """
    stable_id = f"imported_conversation:{conversation.id}"

    if provider is None:
        return ContinuityPacketResult(
            conversation_stable_id=stable_id,
            artifacts=[],
            error="No LLM provider configured. Set SOULPRINT_LLM_PROVIDER to enable continuity generation.",
        )

    transcript = _build_transcript(conversation)
    user_message = f"--- Transcript ---\n{transcript}"

    try:
        raw_response = provider.complete(_SYSTEM_PROMPT, user_message)
    except Exception as exc:
        return ContinuityPacketResult(
            conversation_stable_id=stable_id,
            artifacts=[],
            error=f"Provider call failed: {exc}",
        )

    try:
        parsed = _parse_provider_response(raw_response)
    except (json.JSONDecodeError, ValueError) as exc:
        return ContinuityPacketResult(
            conversation_stable_id=stable_id,
            artifacts=[],
            error=f"Failed to parse provider response as JSON: {exc}",
        )

    timestamp = make_timestamp()
    source_ids = [stable_id]
    provider_name = provider.provider_name
    artifacts: list[ContinuityArtifact] = []

    # -- summary --
    summary_text = parsed.get("summary", "")
    if summary_text:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="summary",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text=summary_text,
        ))

    # -- decisions --
    decisions = parsed.get("decisions", [])
    if decisions:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="decisions",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text="\n".join(f"- {d}" for d in decisions),
            content_json={"decisions": decisions},
        ))

    # -- open_loops --
    open_loops = parsed.get("open_loops", [])
    if open_loops:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="open_loops",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text="\n".join(f"- {o}" for o in open_loops),
            content_json={"open_loops": open_loops},
        ))

    # -- entity_map --
    entity_map = parsed.get("entity_map", [])
    if entity_map:
        artifacts.append(ContinuityArtifact(
            artifact_id=make_artifact_id(),
            artifact_type="entity_map",
            source_conversation_ids=source_ids,
            generation_timestamp=timestamp,
            llm_provider_used=provider_name,
            prompt_template_version=prompt_version,
            content_text=", ".join(entity_map),
            content_json={"entity_map": entity_map},
        ))

    # Persist all artifacts
    path = Path(store_path)
    for artifact in artifacts:
        append_artifact(path, artifact)

    return ContinuityPacketResult(
        conversation_stable_id=stable_id,
        artifacts=artifacts,
    )
