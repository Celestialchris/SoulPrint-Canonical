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

## CodeQL's path-injection sanitizer is realpath+startswith, not relative_to

**From:** April 20, 2026 (CodeQL session, `ops/sessions/april-20-2026-3.md`)
**Pattern:** For any user-supplied path validation, use `os.path.realpath(str(path))` followed by `str.startswith(base + os.sep)` as the boundary check. `Path.relative_to()` is functionally correct but invisible to CodeQL's taint model, and retrofitting it later costs multiple PRs.
**Why:** Three PRs (#126, #128, #130) were spent learning this. The first two used `relative_to`, which closed one alert but left others open. The third tried to add the sanitizer at the sink and broke tests. The correct pattern from the start would have closed everything in one PR.

## Windows CI runs workspace on D:\ and home on C:\

**From:** April 20, 2026 (PR #130 revert, `ops/sessions/april-20-2026-3.md`)
**Pattern:** Any test or runtime check that compares paths against `Path.home()` will fail on GitHub Actions Windows runners where `D:\a\<repo>\<repo>` is the checkout path and `C:\Users\runneradmin` is home. Tests that use `make_test_temp_dir` create paths under the workspace, which on Windows CI is outside home.
**Why:** PR #130 added a home-boundary check inside `discover_sessions` and passed locally (repo under home) but failed every Windows CI run. Any `path.relative_to(Path.home())` or `startswith(home + os.sep)` inside a function also called by tests needs to account for this.
