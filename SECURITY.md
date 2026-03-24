# Security Policy

## Architecture

SoulPrint is a local-first application. All data stays on your machine. The canonical SQLite ledger, derived artifacts, and exported passports are stored locally in `instance/` and `exports/`.

There are no outbound network calls from the core application. No analytics, no telemetry, no tracking.

## BYOK (Bring Your Own Key)

Intelligence features (summaries, topics, digests, ask, continuity) require a user-configured LLM API key. When configured, conversation chunks are sent to the configured provider (OpenAI or Anthropic). This is the only case where data leaves your machine, and it is entirely opt-in.

## Reporting a Vulnerability

If you discover a security issue, please report it privately via [GitHub Security Advisories](https://github.com/Celestialchris/SoulPrint-Canonical/security/advisories) or email the maintainer directly. Do not open a public issue for security vulnerabilities.
