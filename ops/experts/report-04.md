# Expert Report 04: chore/claude-review-skip-bots

Date: 2026-04-30
Branch: chore/claude-review-skip-bots
PR: (pending)
Template H prompt: inline (skip claude-review job on bot-authored PRs)

## Routing

Section A expert: Test Engineer
Section B stance: Senior Engineer

## Reads consumed during drafting

- `context/experts.md` (project canon): Test Engineer stanza — owns GitHub Actions CI configuration and reliability.
- `.github/workflows/claude-code-review.yml` (read-to-verify): confirmed trigger events, no existing job-level `if:`, commented-out filter block at lines 15-19.
- `.github/workflows/claude.yml` (read-to-verify): confirmed scope — `@claude` mention workflow, not triggered by `pull_request: opened` for all PRs. Stays untouched.
- `.github/dependabot.yml` (read-to-verify): confirmed Dependabot configured for pip, weekly interval.
- `ops/experts/report-02.md` (pattern mirror): report format reference.

## Reads consumed during execution by Claude Code

- `.github/workflows/claude-code-review.yml` (read, edited): added `if: github.event.pull_request.user.type != 'Bot'` at line 20.
- `context/experts.md` (read): report format reference.
- `ops/sessions/april-30-2026-claude-review-skip-bots.md` (created): branch session log.
- `ops/learned/github-actions-bot-pr-gating.md` (created): new learned pattern doc.
- `ops/experts/report-04.md` (this file).

## Outcome

- Tests: N/A — no Python touched, no test suite run.
- New deps: none.
- Behavior change: `claude-review` job is skipped (neutral "Skipped" status) on any PR where `pull_request.user.type == 'Bot'`. Human-authored PRs are unaffected. Fixes recurring red-failure check on every Dependabot PR.

## Observations

This was a tight, clean Test Engineer + Senior Engineer pairing. The Test Engineer's ownership of GitHub Actions CI is the natural routing: the failure mode was a CI workflow misbehaving on bot PRs, not a Python or Flask concern. Senior Engineer supplied the instinct to prefer `user.type` (general-purpose, self-maintaining) over a hardcoded login allowlist (point-in-time, needs manual updates).

The Template H assumption verification step was load-bearing. Branch protection status was unknown at prompt time; the `gh api` check was the go/no-go gate for whether job-level skipping was safe. It returned 404 (not protected), so the fix was clean. Had it returned protected-with-required-checks, the fix shape would have needed to change before touching any file.

One structural note: `report-03.md` does not yet exist in `ops/experts/`. The Template H prompt explicitly named this report-04; the numbering gap implies a third routed branch whose report was not written or whose branch is in flight. No action taken on this gap — it is an observation, not a blocker.
