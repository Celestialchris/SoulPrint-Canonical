# Learned Patterns

Reusable patterns extracted from corrections and successful approaches during development sessions. These complement `.claude/rules/` (which stores hard constraints) with softer guidance that improves output quality over time.

## When to Add

When the user corrects an approach and the correction generalizes beyond the specific task. The soul.md feedback loop (step 2) proposes additions here or to `.claude/rules/` depending on whether the pattern is a hard constraint or a soft preference.

## Format

```markdown
## [Pattern name]
**From:** [date or session reference]
**Pattern:** [1-3 sentences describing what to do]
**Why:** [what went wrong without it, or what improved with it]
```

## Distinction from `.claude/rules/`

- `.claude/rules/` = hard constraints. "Never do X." "Always do Y before Z."
- `ops/learned/` = soft patterns. "When doing X, approach Y tends to work better because Z."
