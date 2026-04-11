# -*- mode: python ; coding: utf-8 -*-
import sys
import tomllib
from pathlib import Path

project_root = Path(SPECPATH).resolve().parent

# Single source of truth for version
with open(project_root / "pyproject.toml", "rb") as f:
    VERSION = tomllib.load(f)["project"]["version"]

datas = [
    (str(project_root / "src" / "app" / "templates"), "src/app/templates"),
    (str(project_root / "src" / "app" / "static"), "src/app/static"),
    (str(project_root / "sample_data"), "sample_data"),
]

hiddenimports = [
    # -- Frameworks --
    "flask",
    "flask_sqlalchemy",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    # -- Optional deps (installed via [full]) --
    "dotenv",
    "cryptography",
    # -- src top-level --
    "src",
    "src.config",
    "src.runtime",
    "src.main",
    # -- src.app --
    "src.app",
    "src.app.citation_handoff",
    "src.app.imported_explorer",
    "src.app.licensing",
    "src.app.models",
    "src.app.models.db",
    "src.app.utils.encryption",
    "src.app.viewmodels",
    "src.app.viewmodels.workspace",
    "src.app.viewmodels.wrapped",
    # -- src.importers --
    "src.importers",
    "src.importers.chatgpt",
    "src.importers.claude",
    "src.importers.cli",
    "src.importers.contracts",
    "src.importers.errors",
    "src.importers.gemini",
    "src.importers.persistence",
    "src.importers.query",
    "src.importers.query_cli",
    "src.importers.registry",
    # -- src.retrieval --
    "src.retrieval",
    "src.retrieval.cli",
    "src.retrieval.federated",
    "src.retrieval.fts",
    "src.retrieval.mem0_adapter",
    # -- src.answering --
    "src.answering",
    "src.answering.cli",
    "src.answering.local",
    "src.answering.trace",
    # -- src.intelligence --
    "src.intelligence",
    "src.intelligence.digest",
    "src.intelligence.distill",
    "src.intelligence.provider",
    "src.intelligence.store",
    "src.intelligence.summarizer",
    "src.intelligence.threads",
    "src.intelligence.topics",
    "src.intelligence.continuity",
    "src.intelligence.continuity.bridge",
    "src.intelligence.continuity.lineage",
    "src.intelligence.continuity.models",
    "src.intelligence.continuity.service",
    "src.intelligence.continuity.store",
    # -- src.obsidian --
    "src.obsidian",
    "src.obsidian.cli",
    "src.obsidian.config",
    "src.obsidian.exporter",
    "src.obsidian.renderer",
    # -- src.passport --
    "src.passport",
    "src.passport.cli",
    "src.passport.export",
    "src.passport.validator",
    # -- src.tools --
    "src.tools.memory_query",
    "src.tools.tag_validator",
]

a = Analysis(
    [str(project_root / "src" / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

# --- Platform-specific icon ---
icon_file = None
if sys.platform == "win32":
    ico = project_root / "scripts" / "soulprint.ico"
    if ico.exists():
        icon_file = str(ico)
elif sys.platform == "darwin":
    icns = project_root / "scripts" / "soulprint.icns"
    if icns.exists():
        icon_file = str(icns)
# Linux: no icon needed for the binary

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SoulPrint",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SoulPrint",
)

# --- macOS .app bundle ---
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="SoulPrint.app",
        icon=icon_file,
        bundle_identifier="dev.soulprint.app",
        info_plist={
            "CFBundleShortVersionString": VERSION,
            "CFBundleName": "SoulPrint",
            "NSHighResolutionCapable": True,
        },
    )
