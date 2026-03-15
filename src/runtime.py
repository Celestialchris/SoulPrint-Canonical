from __future__ import annotations
import os, sys
from pathlib import Path

APP_NAME = "SoulPrint"

def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))

def project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def bundle_root() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base)
    return project_root()

def resource_path(*parts: str) -> Path:
    return bundle_root().joinpath(*parts)

def default_app_home() -> Path:
    override = os.getenv("SOULPRINT_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen():
        if sys.platform == "win32":
            base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            return (base / APP_NAME).resolve()
        if sys.platform == "darwin":
            return (Path.home() / "Library" / "Application Support" / APP_NAME).resolve()
        return (Path.home() / ".local" / "share" / APP_NAME).resolve()
    return project_root()

def default_instance_dir() -> Path:
    path = default_app_home() / "instance"
    path.mkdir(parents=True, exist_ok=True)
    return path

def default_upload_dir() -> Path:
    path = default_app_home() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path

def templates_dir() -> Path:
    return resource_path("src", "app", "templates")

def static_dir() -> Path:
    return resource_path("src", "app", "static")
