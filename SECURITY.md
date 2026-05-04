# Security Policy

SoulPrint is a local-first archive for AI conversation history. The security posture follows from that shape: canonical data lives on your machine, the application makes no outbound network calls in core mode, and trust boundaries are explicit and inspectable. See [docs/privacy.md](docs/privacy.md) for the user-facing privacy posture; this document focuses on the security model.

## Supported versions

| Version | Status |
|---------|--------|
| `0.7.x` (current alpha, source) | Active. Security fixes land here first. |
| `0.6.0` (last packaged release) | Best-effort backports for high-severity issues. |
| Older | Unsupported. Upgrade to current source. |

## Reporting a vulnerability

Report security issues privately via [GitHub Security Advisories](https://github.com/Celestialchris/SoulPrint-Canonical/security/advisories/new). Please do not open a public issue for security vulnerabilities.

If you believe an issue is being actively exploited, mark the advisory as such; otherwise expect an acknowledgement within a reasonable window and a coordinated fix before public disclosure.

## Security model

SoulPrint is a single-user local application. It is not a hosted service and it does not manage accounts for multiple users.

This security policy focuses on the risks SoulPrint can reasonably control:

- Malicious or malformed provider exports.
- Unsafe redirects or crafted form inputs.
- Accidental network calls from the core archive.
- Accidental exposure of local services to other machines on the network.
- Unsafe attachment names or export paths trying to escape their intended folder.

Some risks are outside what SoulPrint can protect against:

- If someone already controls your computer or your operating-system account, they can access anything your user account can access.
- SoulPrint does not provide multi-user login, permissions, or team access controls.
- SoulPrint cannot protect against a cloud LLM provider misusing data after you explicitly configure that provider and send data to it.

The security model assumes the machine running SoulPrint is owned and trusted by the user, and that the instance directory and database file are protected by normal operating-system file permissions.

## Network behavior

The core archive is local. Import, browse, search, notes, exports, passport, MCP, and the answer-trace browser run with no network calls beyond loopback.

The only outbound network calls are:

- Optional intelligence features (Ask, Distill, Recurring Themes, Continuity Packet), which contact the LLM provider you have explicitly configured, and only when you trigger them.
- The MCP server, which speaks to a local MCP client (Claude Code, Cursor, or any MCP-compatible tool) over `stdio`. The MCP server does not open a network port.

There is no analytics endpoint, no telemetry, no update check, no error reporting, and no background sync.

## LLM provider behavior

Intelligence features require a configured provider. SoulPrint supports three:

- **Ollama or any OpenAI-compatible local endpoint.** Fully local. No API key required for keyless local servers. No data leaves the machine.
- **OpenAI** (cloud). Requires a user-supplied API key. Conversation chunks are sent to OpenAI when you trigger an intelligence feature.
- **Anthropic** (cloud). Requires a user-supplied API key. Conversation chunks are sent to Anthropic when you trigger an intelligence feature.

Cloud providers are bring-your-own-key. SoulPrint does not proxy keys, broker calls, or share keys between users.

## Import parser attack surface

Provider exports are untrusted input. SoulPrint parses files in five formats:

- ChatGPT `.zip`, which is unpacked to read JSON entries and never executed.
- Claude `.json`.
- Claude Code `.jsonl`.
- Gemini Takeout `MyActivity.json`, with HTML-to-text extraction via lxml and beautifulsoup4.
- Grok `.json`, including BSON `$numberLong`, ISO `$date` wrapper, raw ISO, and raw epoch timestamp variants.

Hardening posture:

- Parsers reject malformed payloads with typed errors (`ImportProviderDetectionError`, `MalformedImportFileError`, `UnsupportedImportFormatError`) instead of swallowing exceptions.
- Detector functions return `False` for unrecognized payloads rather than raising.
- The Gemini parser uses lxml; the project pins `lxml>=6.1.0` to pull in CVE fixes (Dependabot tracks regressions).
- Imports run in the user's Python process. There is no shell, no template rendering of imported content, and no eval of imported strings.
- Every import attempt records an `ImportRun` row classified as `success`, `duplicate_only`, `partial`, or `failed`, including pre-importer validation failures and unexpected exceptions.

If you find a parser path that crashes the app, hangs, or escapes the intended scope, please report it via Security Advisories.

## Attachments and file custody

Attachments explicitly added to a conversation or message in SoulPrint are written to the filesystem under the instance directory. SoulPrint records SHA-256, original filename, MIME type, size, and the owning conversation/message relationship in the ledger.

Risks to be aware of:

- An attached file is opaque content. Opening it is the user's responsibility; SoulPrint does not sandbox or scan attachment content.
- Filename normalization rejects path traversal at write time; absolute paths and parent-relative segments are stripped before the filename hits disk.
- Exports preserve attachments verbatim. An attachment-aware export bundle contains exactly the bytes that were explicitly attached in SoulPrint.
- Multi-select export keeps per-conversation `<stem>.assets/` subtrees isolated; there is no cross-contamination between conversations in a single zip.

## SQLite and archive protection

The canonical ledger is a SQLite file (default: `instance/soulprint.db`). Treat it the way you treat other personal data on your disk:

- Keep the instance directory in your user profile, not a shared location.
- Back up the file with whatever tool you trust; the SQLite format is portable across platforms.
- The file is unencrypted at rest. If you need encryption, place the instance directory inside an encrypted volume (FileVault, BitLocker, LUKS, VeraCrypt, or equivalent).

Derived artifacts (summaries, distillations, traces, continuity packets) are also stored locally, in JSONL files alongside the database. They are reproducible from canonical data; the canonical ledger is the only artifact whose loss is irrecoverable.

The `soulprint verify` CLI subcommand and the `/archive/health` page run deterministic checks (DB existence, SQLite integrity, core tables, FTS tables, orphan messages) so you can audit the ledger at any time.

## MCP and local server exposure

SoulPrint runs two local services when launched:

- **Flask web app** on `http://127.0.0.1:5678`, bound to loopback by default.
- **MCP server** over `stdio`, speaking to a local MCP client process. It does not open a network port.

Both are designed for single-user local use. Do not expose either service to other machines:

- Do not bind the Flask app to `0.0.0.0` or a public IP.
- Do not place the Flask app behind a public reverse proxy.
- Do not run SoulPrint inside a container that publishes the port to a shared network.
- Do not configure a remote MCP client to reach a SoulPrint host you do not control.

If you need remote access for personal use, run SoulPrint inside an SSH tunnel scoped to your own session; do not publish the port.

## Best practices

- Update to the current source tree for security fixes; the active branch is `main`.
- Configure intelligence features only when you intend to use them.
- For fully offline intelligence, use Ollama; do not configure cloud API keys you do not need.
- Keep the instance directory and the database file out of version control and out of synced folders unless you explicitly intend to back them up that way.
- Treat exports the way you treat any document containing personal AI conversation data; review before sharing.
- If you redistribute a Memory Passport, remember it contains the full transcripts; the export contract preserves provenance, not privacy.

## Out of scope

- Hosted SoulPrint. There is no SoulPrint cloud service, account system, or sync layer. If you find a service branded as such, it is not affiliated with this project.
- Multi-user authentication, role-based access, or sharing controls.
- Sandboxing or scanning of attachment content.
- Compromise of a configured LLM provider, or of the network path between SoulPrint and that provider once you have explicitly enabled cloud intelligence.
- Compromise of the local user account or the underlying operating system.
