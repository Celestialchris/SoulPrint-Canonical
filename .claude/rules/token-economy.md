# Token Economy for Claude Code
- ALWAYS put file read lists in the primacy zone (top of prompt, before Objective).
- Use: "Do NOT spawn explore agents. Do NOT scan the codebase."
- Name every file Claude Code needs. Every named file = one fewer explored file.
- One module per prompt. Don't combine renderer + exporter + CLI in one prompt.
- Start fresh sessions between tasks. Don't accumulate context across unrelated work.
