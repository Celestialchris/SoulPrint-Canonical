# Privacy

SoulPrint collects no data. There is no analytics, no telemetry, no
tracking, no error reporting, and no background sync.

The core archive is local. Import, browse, search, notes, exports,
Memory Passport, and the answer-trace browser run with no network
calls beyond loopback. Your conversation archive lives in a local
SQLite file on your disk.

Network activity occurs only when you explicitly trigger an
intelligence feature such as Ask, Distill, Recurring Themes, or
Continuity Packet. In that case, conversation excerpts are sent to
the LLM provider you have configured. Supported paths include a local
OpenAI-compatible endpoint such as Ollama, OpenAI with your API key,
or Anthropic with your API key.

The MCP server speaks to a local MCP client over stdio and does not
open a network port.

For the full security model, including the threat model, attachment
custody, and known caveats, see [SECURITY.md](SECURITY.md).
