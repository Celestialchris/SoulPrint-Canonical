# Session Logs

Claude writes a file here at the end of every session where code was committed or a decision was made. This is the project's working memory.

## Naming Convention

`month-day-year-sequence.md`. Examples: `april-19-2026-1.md`, `april-19-2026-2.md`. Lowercase month name so "what did we do in april" matches via grep.

## Entry Format

```markdown
## Month Day, Year — [short title]
**Branch:** [branch name]
**What:** [1-2 sentences on what was done]
**Decisions:** [choices made and reasoning, or "none"]
**Next:** [what's queued or unresolved]
```

## Rules

- Append-only. Do not edit past entries.
- Keep entries factual and brief. This is a log, not a journal.
- If older entries stop being useful, move them to `ops/sessions/archive/`.
- Claude reads the most recent 2-3 entries before starting work.
