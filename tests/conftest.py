from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Enable license override so all existing tests pass without a key file.
os.environ.setdefault("SOULPRINT_LICENSE_OVERRIDE", "true")

# Isolate SOULPRINT_HOME for tests so ensure_layout() does not pollute the real
# user home. Tests that need per-case isolation use temp_soulprint_home().
os.environ.setdefault(
    "SOULPRINT_HOME",
    str(ROOT / ".tmp-tests" / "soulprint-home-session"),
)
