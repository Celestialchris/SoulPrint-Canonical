"""Importer package for external conversation exports."""

from .chatgpt import ChatGPTImporter, parse_chatgpt_export, parse_chatgpt_export_file
from .claude import ClaudeImporter, parse_claude_export, parse_claude_export_file
from .contracts import (
    PROVIDER_CHATGPT,
    PROVIDER_CLAUDE,
    PROVIDER_GEMINI,
    ConversationImporter,
    NormalizedConversation,
    NormalizedMessage,
    validate_provider_id,
)
from .persistence import persist_normalized_conversations
from .query import get_imported_conversation, list_imported_conversations

__all__ = [
    "PROVIDER_CHATGPT",
    "PROVIDER_CLAUDE",
    "PROVIDER_GEMINI",
    "ConversationImporter",
    "NormalizedConversation",
    "NormalizedMessage",
    "validate_provider_id",
    "ChatGPTImporter",
    "ClaudeImporter",
    "parse_chatgpt_export",
    "parse_chatgpt_export_file",
    "parse_claude_export",
    "parse_claude_export_file",
    "persist_normalized_conversations",
    "list_imported_conversations",
    "get_imported_conversation",
]
