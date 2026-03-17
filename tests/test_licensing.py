"""Tests for src/app/licensing — local license file validation."""

import os
from pathlib import Path

import pytest


def _write_key(directory: str, content: str) -> Path:
    """Helper: write a license.key file in the given directory."""
    key_path = Path(directory) / "license.key"
    key_path.write_text(content, encoding="utf-8")
    return key_path


class TestIsLicensed:
    """is_licensed() returns True only when a valid SP- key file exists."""

    def test_returns_false_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOULPRINT_LICENSE_OVERRIDE", "false")
        from src.app.licensing import is_licensed

        assert is_licensed(instance_dir=str(tmp_path)) is False

    def test_returns_false_when_file_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOULPRINT_LICENSE_OVERRIDE", "false")
        _write_key(str(tmp_path), "")
        from src.app.licensing import is_licensed

        assert is_licensed(instance_dir=str(tmp_path)) is False

    def test_returns_false_when_invalid_prefix(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOULPRINT_LICENSE_OVERRIDE", "false")
        _write_key(str(tmp_path), "INVALID-KEY-1234")
        from src.app.licensing import is_licensed

        assert is_licensed(instance_dir=str(tmp_path)) is False

    def test_returns_true_when_valid_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOULPRINT_LICENSE_OVERRIDE", "false")
        _write_key(str(tmp_path), "SP-abc-123-valid")
        from src.app.licensing import is_licensed

        assert is_licensed(instance_dir=str(tmp_path)) is True

    def test_override_env_bypasses_check(self, tmp_path, monkeypatch):
        """SOULPRINT_LICENSE_OVERRIDE=true makes is_licensed() return True
        even when no key file exists."""
        from src.app.licensing import is_licensed

        monkeypatch.setenv("SOULPRINT_LICENSE_OVERRIDE", "true")
        assert is_licensed(instance_dir=str(tmp_path)) is True


class TestGetLicenseStatus:
    """get_license_status() returns a dict with licensed bool and tier string."""

    def test_free_tier_when_unlicensed(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOULPRINT_LICENSE_OVERRIDE", "false")
        from src.app.licensing import get_license_status

        status = get_license_status(instance_dir=str(tmp_path))
        assert status["licensed"] is False
        assert status["tier"] == "free"

    def test_pro_tier_when_licensed(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SOULPRINT_LICENSE_OVERRIDE", "false")
        _write_key(str(tmp_path), "SP-pro-key-xyz")
        from src.app.licensing import get_license_status

        status = get_license_status(instance_dir=str(tmp_path))
        assert status["licensed"] is True
        assert status["tier"] == "pro"
