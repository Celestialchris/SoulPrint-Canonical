"""Import run history: classification, persistence, and retrieval.

Each import POST creates exactly one ImportRun row regardless of outcome.
Mirrors the service-module shape of src/app/tags.py.
"""

from __future__ import annotations

import time

from src.app.models import ImportRun
from src.app.models.db import db
from src.importers.contracts import PROVIDER_DISPLAY_NAMES


VALID_STATUSES: frozenset[str] = frozenset({
    "success", "duplicate_only", "partial", "failed",
})


def classify_import_outcome(
    imported: int,
    skipped: int,
    failed: int,
    reached_importer: bool,
) -> str:
    """Classify one import attempt into a status string.

    Rules (evaluated in order):
      1. not reached_importer               → "failed"
      2. failed > 0 and (imported + skipped) > 0  → "partial"
      3. failed > 0 and imported == 0 and skipped == 0  → "failed"
      4. imported > 0                       → "success"
      5. imported == 0 and skipped > 0      → "duplicate_only"
      6. all zero (empty/zero-conv file)    → "failed"

    Pure function. No DB access.
    """
    if not reached_importer:
        return "failed"
    if failed > 0 and (imported + skipped) > 0:
        return "partial"
    if failed > 0:
        return "failed"
    if imported > 0:
        return "success"
    if skipped > 0:
        return "duplicate_only"
    return "failed"


def record_import_run(
    *,
    provider: str | None,
    filename: str | None,
    status: str,
    conversations_imported: int,
    messages_imported: int,
    conversations_skipped: int,
    conversations_failed: int,
    error_message: str | None,
) -> ImportRun:
    """Insert one ImportRun row and commit. Truncates error_message to 500 chars.

    Caller must supply status computed via classify_import_outcome.
    Requires a Flask app context.
    """
    row = ImportRun(
        provider=provider,
        filename=filename,
        imported_at=time.time(),
        status=status,
        conversations_imported=conversations_imported,
        messages_imported=messages_imported,
        conversations_skipped=conversations_skipped,
        conversations_failed=conversations_failed,
        error_message=error_message[:500] if error_message else None,
    )
    db.session.add(row)
    db.session.commit()
    return row


def latest_import_runs(limit: int = 10) -> list[ImportRun]:
    """Return the most recent ImportRun rows, newest first. Flask context required."""
    return ImportRun.query.order_by(ImportRun.imported_at.desc()).limit(limit).all()


def last_import_run_per_provider() -> dict[str, "ImportRun | None"]:
    """Return the most-recent ImportRun row per provider, keyed by provider ID.

    All five provider keys from PROVIDER_DISPLAY_NAMES are always present.
    Providers with no import history have value None.
    Rows with provider=None are excluded.
    """
    result: dict[str, ImportRun | None] = {pid: None for pid in PROVIDER_DISPLAY_NAMES}
    rows = (
        ImportRun.query
        .filter(ImportRun.provider.isnot(None))
        .order_by(ImportRun.imported_at.desc())
        .all()
    )
    for row in rows:
        if row.provider in result and result[row.provider] is None:
            result[row.provider] = row
    return result
