"""Environment-configurable paths for the Reader backend.

`READER_HOME` is the root of the VoiceForge tree. Setting it alone moves
both refs and output together. Setting `READER_REFS_DIR` or
`READER_OUTPUT_DIR` explicitly overrides the derived path.
"""
from __future__ import annotations

import os

READER_HOME = os.environ.get("READER_HOME", r"D:\VoiceForge")
READER_REFS_DIR = os.environ.get(
    "READER_REFS_DIR", os.path.join(READER_HOME, "refs")
)
READER_OUTPUT_DIR = os.environ.get(
    "READER_OUTPUT_DIR", os.path.join(READER_HOME, "output")
)

CORS_ALLOWED_ORIGIN = os.environ.get(
    "READER_CORS_ORIGIN", "http://127.0.0.1:5173"
)
