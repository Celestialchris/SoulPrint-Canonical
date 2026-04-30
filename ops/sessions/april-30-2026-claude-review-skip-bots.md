## April 30, 2026 — Skip claude-review job on bot-authored PRs
**Branch:** chore/claude-review-skip-bots
**What:** Added a job-level `if: github.event.pull_request.user.type != 'Bot'` condition to `.github/workflows/claude-code-review.yml`. The `claude-code-action@v1` rejects bot-authored runs with a `Workflow initiated by non-human actor` error; the fix skips the job entirely on bot PRs rather than attempting to pass the action through.

**Decisions:**
- Job-level `if:` over `allowed_bots: '*'` action input. Skipping entirely surfaces as a neutral "Skipped" status on bot PRs, which accurately reflects that no review happened. Passing through would show "Passed" for runs that did no real work.
- `user.type != 'Bot'` over `user.login != 'dependabot[bot]'`. The type field is set by GitHub from the OAuth token category, not user input. Future bots (Renovate, Snyk) inherit the exclusion without a config change.
- Kept the commented-out filter examples at lines 15-19. They are documentation; removing them would reduce discoverability.
- Branch protection verified absent on `main` (`gh api` returned 404 "Branch not protected"). Skipping the job is safe: no required status check will block merge.

**Artifacts:**
- `.github/workflows/claude-code-review.yml`: one line added (line 20 in final file).
- `ops/learned/github-actions-bot-pr-gating.md`: new learned doc capturing the `user.type` pattern and the required-status-check caveat.
- `ops/experts/report-04.md`: routing report.

**Tests:** none required. No Python touched. Workflow YAML changes are verified empirically: the PR's own Checks tab confirms the human-authored path runs; the bot-skip path is verified the next time Dependabot opens or rebases a PR.

**Verification:** PR will self-test. The `Claude Code Review / claude-review` check should appear and run on this human-authored PR. On future Dependabot PRs, the check should show "Skipped" with a neutral icon, not a red failure.

**PRs affected:** #188, #189, #190 (currently open Dependabot PRs) will show no retroactive change; the fix applies only to future runs.
