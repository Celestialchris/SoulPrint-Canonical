import os
from pathlib import Path

from .runtime import default_instance_dir, default_upload_dir

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def normalize_sqlite_uri(uri: str) -> str:
    """Normalize SQLite file URIs so absolute paths work consistently."""

    prefix = "sqlite:///"
    if not uri.startswith(prefix):
        return uri

    raw_path = uri.removeprefix(prefix)
    if raw_path == ":memory:":
        return uri

    return f"{prefix}{Path(raw_path).resolve().as_posix()}"


def sqlite_uri_from_path(path: str | Path) -> str:
    """Build a normalized SQLite file URI from a filesystem path."""

    return normalize_sqlite_uri(f"sqlite:///{Path(path).resolve().as_posix()}")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = sqlite_uri_from_path(
        default_instance_dir() / "soulprint.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(default_upload_dir())
    SOULPRINT_EXPORT_DIR = os.environ.get("SOULPRINT_EXPORT_DIR", "")
