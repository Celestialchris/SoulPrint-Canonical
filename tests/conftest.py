from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Enable license override so all existing tests pass without a key file.
os.environ.setdefault("SOULPRINT_LICENSE_OVERRIDE", "true")
