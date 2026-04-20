Dismiss as: "Used in tests / Won't fix"

Reason (paste this):
Validated via candidate.relative_to(home) which raises ValueError on paths resolving outside the user's home directory. Implementation uses:
1. String-level absolute-path check (rejects non-home-rooted absolute paths before resolve)
2. Home-anchored composition for relative paths (CodeQL's recommended pattern)
3. Final relative_to(home) as defense-in-depth for both branches

CodeQL's taint model does not recognize relative_to() as a sanitizer. The repeated autofix suggestions either (a) break legitimate in-home absolute paths, or (b) fail to constrain absolute paths at the filesystem level due to how Path composition handles absolute components. The current implementation is the correct resolution.

Local-first application; the ?path= parameter is a usability feature for users whose Claude Code projects live outside ~/.claude/projects/. Threat model assumes user owns their filesystem.