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

## `git reset --hard origin/<branch>` is the safe sync pattern

**From:** April 20, 2026 evening (P7 Phase 1 branch rescue, `ops/sessions/april-20-2026-4.md`)
**Pattern:** When local branch is ahead of origin for any wrong reason (accidental commit, wrong branch, stale state), reset by remote name: `git reset --hard origin/<branch>`. Never use `HEAD^` if there is any chance of running the command twice.
**Why:** `HEAD^` requires counting commits. Running it twice compounds the error by one extra rewind. Today local main dropped PR #131's merge because a second `git reset --hard HEAD^` ran after the first successful sync. `git reset --hard origin/main` is idempotent and always hits the known-good state.

## Verify branch with `git branch --show-current` before `git commit`

**From:** April 20, 2026 evening (P7 Phase 1 accidental main commit, `ops/sessions/april-20-2026-4.md`)
**Pattern:** After `git checkout -b <new-branch>`, and again immediately before any `git add`/`git commit`, run `git branch --show-current` and visually confirm the output matches the intended feature branch.
**Why:** Claude Code ran `git checkout -b feat/p7-phase1-cli-dispatch` at session start. The commit still landed on `main`. Root cause not traced (possibly intermediate checkout dropping context, possibly rtk wrapper interaction). Adding one verification line before commit catches this class of error before the wrong-branch commit exists. Cheap check, high value.

## Standalone file index

- [FTS timestamp sort stability](./fts-timestamp-sort-stability.md) — empty-string timestamps need sentinel `"9999-12-31T23:59:59Z"` in ASC sort; DESC is safe without it.
- [Redirect-after-action safety](./redirect-after-action-safety.md) — `_safe_next()` pattern for validating a user-supplied `next` redirect param; template `session.pop()` for scope-locked routes.
