# GitHub Actions: skip jobs on bot-authored PRs via user.type check

**Pattern.** Add a job-level `if:` condition to skip a workflow job entirely on bot-authored PRs:

```yaml
jobs:
  your-job:
    if: github.event.pull_request.user.type != 'Bot'
    runs-on: ubuntu-latest
```

**Why `user.type` instead of `user.login`.** `user.type` is set by GitHub based on OAuth token type, not a user-supplied string. Using `user.type != 'Bot'` future-proofs against any bot actor (Renovate, Snyk, etc.) without needing enumeration.

**Skipped vs. required status checks.** A skipped job shows a neutral gray "Skipped" status on the PR. This is safe only if the job is NOT listed as a required status check in branch protection. If the job is required, GitHub keeps it in "expected — waiting" state and blocks merge. Verify branch protection with `gh api repos/<owner>/<repo>/branches/main/protection` before applying this pattern.

**Context.** Applied in `chore/claude-review-skip-bots` (2026-04-30) to gate `claude-code-review.yml` against Dependabot PRs. The `claude-code-action@v1` rejects bot-authored runs with `Workflow initiated by non-human actor` unless `allowed_bots: '*'` is set — but that passes the action, whereas the desired UX was to skip entirely. Job-level `if:` was the right layer.
