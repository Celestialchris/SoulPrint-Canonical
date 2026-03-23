"""Obsidian vault configuration generator.

Creates .obsidian/ config and Templates/ on first export.
Never overwrites existing config — the user customizes freely after.
"""

from __future__ import annotations

import json
from pathlib import Path


def generate_config(vault_path: Path) -> bool:
    """Create .obsidian/ with JSON config files.

    Returns True if created, False if .obsidian/ already exists.
    """
    obsidian_dir = vault_path / ".obsidian"
    if obsidian_dir.exists():
        return False

    obsidian_dir.mkdir(parents=True, exist_ok=True)

    configs = {
        "app.json": {"attachmentFolderPath": "Attachments"},
        "daily-notes.json": {"folder": "Daily", "format": "YYYY-MM-DD"},
        "templates.json": {"folder": "Templates"},
        "appearance.json": {"baseFontSize": 16, "theme": "obsidian"},
        "community-plugins.json": [],
    }

    for filename, payload in configs.items():
        (obsidian_dir / filename).write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )

    return True


def generate_templates(vault_path: Path) -> None:
    """Create Templates/ with basic note templates."""
    templates_dir = vault_path / "Templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    templates = {
        "chat.md": (
            "---\n"
            "type: chat\n"
            "source: soulprint\n"
            "stable_id:\n"
            "provider:\n"
            "lane: imported\n"
            "title:\n"
            "created:\n"
            "---\n"
        ),
        "theme.md": (
            "---\n"
            "type: theme\n"
            "source: soulprint\n"
            "topic_label:\n"
            "confidence:\n"
            "---\n"
        ),
        "daily.md": (
            "---\n"
            "type: daily\n"
            "date:\n"
            "---\n"
        ),
    }

    for filename, content in templates.items():
        (templates_dir / filename).write_text(content, encoding="utf-8")
