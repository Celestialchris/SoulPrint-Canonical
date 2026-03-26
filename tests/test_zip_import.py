"""Tests for .zip file import handling in parse_import_file."""

import zipfile
from pathlib import Path

import pytest

from src.importers.registry import parse_import_file
from src.importers.errors import ImportProviderDetectionError, MalformedImportFileError


CHATGPT_FIXTURE = Path("sample_data/chatgpt_export_sample.json")
CLAUDE_FIXTURE = Path("sample_data/claude_export_sample.json")


class TestZipImportChatGPT:
    """ChatGPT .zip exports (contain conversations.json)."""

    def test_chatgpt_zip_autodetects(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "chatgpt_export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(CHATGPT_FIXTURE, "conversations.json")

        result = parse_import_file(zip_path)

        assert result.provider_id == "chatgpt"
        assert len(result.conversations) > 0

    def test_chatgpt_zip_nested_directory(self, tmp_path: Path) -> None:
        """ChatGPT zip with conversations.json inside a subdirectory."""
        zip_path = tmp_path / "chatgpt_nested.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(CHATGPT_FIXTURE, "export/conversations.json")

        result = parse_import_file(zip_path)

        assert result.provider_id == "chatgpt"
        assert len(result.conversations) > 0


class TestZipImportClaude:
    """Claude .zip exports."""

    def test_claude_zip_autodetects(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "claude_export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(CLAUDE_FIXTURE, "claude_export.json")

        result = parse_import_file(zip_path)

        assert result.provider_id == "claude"
        assert len(result.conversations) > 0


class TestZipImportEdgeCases:
    """Error paths and edge cases."""

    def test_zip_with_no_json_raises(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "no json here")

        with pytest.raises(MalformedImportFileError, match="does not contain any .json"):
            parse_import_file(zip_path)

    def test_zip_with_unrecognized_json_raises(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "junk.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("data.json", '{"not": "an export"}')

        with pytest.raises(ImportProviderDetectionError, match="No importable JSON found"):
            parse_import_file(zip_path)

    def test_provider_hint_respected_in_zip(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "chatgpt_hinted.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(CHATGPT_FIXTURE, "data.json")

        result = parse_import_file(zip_path, provider_hint="chatgpt")

        assert result.provider_id == "chatgpt"
        assert len(result.conversations) > 0
