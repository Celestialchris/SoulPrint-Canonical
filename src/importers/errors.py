"""Importer runtime errors with explicit user-facing diagnostics."""

from __future__ import annotations


class ImporterError(ValueError):
    """Base class for importer runtime errors."""


class ImportProviderDetectionError(ImporterError):
    """Raised when importer provider cannot be detected safely."""


class UnsupportedImportFormatError(ImporterError):
    """Raised when a provider is recognized but not yet supported."""


class MalformedImportFileError(ImporterError):
    """Raised when a supported provider payload is malformed."""
