# Security

## How SoulPrint Handles Your Data

SoulPrint is local-first by design.

- All data stays on your machine in a single SQLite file (`instance/soulprint.db`)
- No analytics, telemetry, or phone-home behavior
- No cloud sync, no hosted storage, no accounts
- Network calls happen only when you explicitly configure a BYOK LLM provider for intelligence features — and those calls go directly to the provider API you chose (OpenAI or Anthropic), not through SoulPrint infrastructure
- The Memory Passport export produces local files you control

## Reporting a Vulnerability

If you find a security issue, please open a GitHub issue or contact the maintainer directly. For sensitive disclosures, use GitHub's private vulnerability reporting feature on this repository.

## Scope

SoulPrint does not handle authentication, payment processing, or remote data storage. The primary security surface is the local Flask web server (bound to `127.0.0.1` by default) and the file import pipeline.
