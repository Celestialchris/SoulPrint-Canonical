# Codex Local Guide - SoulPrint

This file supplements the root `AGENTS.md` for Codex sessions. It is a
Codex-local boot guide, not a second project constitution.

## Authority Order

1. Obey the repo root `AGENTS.md` first.
2. Treat `AGENTS.md`, `CLAUDE.md`, and the current task prompt as the public project context that constrains work. Private operating doctrine and checkpoints are maintained outside the public distribution tree.
3. Treat `.codex/config.toml` as a description of available Codex tooling
   and defaults. It does not outrank repo law, user scope locks, or current
   task instructions.
4. Treat chat memory and tool memory as orientation only. Verify current
   facts against files before using them as implementation authority.

## Codex Layer

The project-local `.codex/config.toml` currently sets:

- `approval_policy = "on-request"`
- `sandbox_mode = "workspace-write"`
- `web_search = "live"`
- `features.multi_agent = true`

Confirmed Codex MCP servers in `.codex/config.toml`:

- `github`
- `context7`
- `playwright`
- `sequential-thinking`

Do not assume any other Codex MCP server exists unless it is present in
`.codex/config.toml`.

## Skills and Agents

Codex agents under `.codex/agents/`:

- `docs-researcher.toml`
- `explorer.toml`
- `reviewer.toml`

These are role presets for bounded work. They are not autonomous authority
and do not override `AGENTS.md`, `CLAUDE.md`, or the current prompt.

Codex-local skills under `.codex/skills/`:

- `openspec-apply-change`
- `openspec-archive-change`
- `openspec-explore`
- `openspec-propose`

Shared repo skills under `.agents/skills/`:

- `api-design`
- `backend-patterns`
- `coding-standards`
- `e2e-testing`
- `frontend-patterns`
- `search-first`
- `security-review`
- `soulprint-ui-doctrine`
- `strategic-compact`
- `tdd-workflow`
- `verification-loop`

Use relevant skills when the task calls for them, but skills are tools, not
scripture. If a skill conflicts with repo law, the user's scope lock, or the
current task, follow the higher authority.

## Current Project Radar

Use the current task prompt and fresh git state as the live radar. Do not assume private checkpoint files exist in this repository.

## Guardrails

- Do not edit `.claude/`, `.agents/`, or `.github/` from a Codex harness-doc sync unless explicitly scoped.
- Do not modify `.codex/config.toml`, `.codex/agents/`, or `.codex/skills/`
  when the task is only documentation alignment.
- Do not add new agents, new skills, new MCP servers, or new workflows from
  this guide.
- Do not treat parked doctrine work, old ECC notes, or stale inventories as
  instructions to execute.
