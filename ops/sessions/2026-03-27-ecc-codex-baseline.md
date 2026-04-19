# Session: Phase 2 Baseline

## What changed
- Installed ECC baseline locally
- Added project-local rules
- Added project-local Codex config
- Added selected skills
- Fixed search-first path
- Entered Phase 2 adaptation

## What worked
- Baseline copied successfully
- Skills directory populated
- Codex scaffold present

## What failed
- `search-first` was not present under `tools/ecc/.agents/skills/`
- corrected by copying from `tools/ecc/skills/search-first`

## Decisions
- keep setup project-local
- keep MCP count low
- delay hooks
- use Claude as primary harness, Codex as secondary harness

## Next steps
- trim `.codex/config.toml` to the lean MCP baseline
- test one real feature workflow in Claude
- test one role-driven workflow in Codex
- only then add the first Claude hook