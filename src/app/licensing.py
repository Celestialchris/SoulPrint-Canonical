"""Local-only license validation for SoulPrint freemium gate.

License file: ``instance/license.key``
Valid key prefix: ``SP-``
Dev overrides: ``SOULPRINT_DEV_MODE=1`` or ``SOULPRINT_LICENSE_OVERRIDE=true`` bypass the file check.
"""

import os
from pathlib import Path

from ..runtime import default_instance_dir


def is_licensed(*, instance_dir: str | None = None) -> bool:
    """Return True when a valid license key is present or a dev override is active."""
    if os.environ.get("SOULPRINT_DEV_MODE") == "1":
        return True
    if os.environ.get("SOULPRINT_LICENSE_OVERRIDE", "").lower() == "true":
        return True

    if instance_dir is None:
        instance_dir = str(default_instance_dir())

    key_path = Path(instance_dir) / "license.key"
    if not key_path.is_file():
        return False

    content = key_path.read_text(encoding="utf-8").strip()
    return content.startswith("SP-")


def get_license_status(*, instance_dir: str | None = None) -> dict:
    """Return ``{"licensed": bool, "tier": "free"|"pro"}``."""
    licensed = is_licensed(instance_dir=instance_dir)
    return {"licensed": licensed, "tier": "pro" if licensed else "free"}
