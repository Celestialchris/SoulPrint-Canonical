from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Enable license override so all existing tests pass without a key file.
os.environ.setdefault("SOULPRINT_LICENSE_OVERRIDE", "true")

# Force SOULPRINT_HOME to a repo-local test sandbox for the entire test session.
# This is direct assignment, not setdefault: an external SOULPRINT_HOME (set in
# the developer's shell, CI, or a parent process) would otherwise cause
# ensure_layout() to create directories inside that real path during tests.
# Individual tests opt out by mutating SOULPRINT_HOME themselves (typically via
# tests/temp_helpers.py::temp_soulprint_home).
os.environ["SOULPRINT_HOME"] = str(ROOT / ".tmp-tests" / "soulprint-home-session")
