---
date: YYYY-MM-DD
status: in-progress | resolved | abandoned
area: <subsystem — intelligence | importers | retrieval | passport | etc>
surface: <user-facing route or feature>
provider: <when relevant — ollama | anthropic | openai>
model: <when relevant — gemma3:4b | claude-sonnet-4 | etc>
prs: [N, N, N]
tags:
  - <campaign-specific tags>
---

# Campaign: <short title>

> **Template note.** Copy this file to `ops/campaigns/YYYY-MM-DD-short-description.md` and fill in. Delete this blockquote and the section guidance italics on your way through. Underscore prefix on this template ensures it sorts first and is visually distinct from real campaigns.

## When to write a campaign doc

Not every multi-PR sequence is a campaign. Three small PRs that all ship clean first try are just three PRs. The signal that something is a campaign is *we hypothesized and were wrong, and the wrongness produced new information.* Campaigns are about the arc of investigation, not the count of commits.

Write the campaign doc lazily, at the end, when you know the whole arc. Contemporaneous-write doubles your documentation friction per PR and you'll skip it. The narrative is also cleaner when you know the arc is complete. The risk of lazy-write is forgetting; the mitigation is making "did this become a campaign?" the last question of every multi-PR arc — if yes, the next 30 minutes goes to the campaign doc before context decays.

## Operating principle

> When debugging opaque failures, isolate one variable per PR whenever practical. Prefer a diagnostic blade over a bundled fix-everything patch unless production urgency requires a hotfix.

The temptation in the moment is always to ship the complete fix. The discipline that pays off later is the diagnostic blade: each PR changes one thing, the new logs reveal the next variable, and at the end you know exactly which fix did which work. A bundled patch that resolves three failure modes at once obscures causality, and the next regression in adjacent territory is twice as expensive to debug because you don't know which layer was load-bearing.

## Symptom

*One paragraph. The user-visible thing that started the campaign. What was broken, what the surface looked like, what wasn't working. Keep this concrete and reproducible — what command, what URL, what error.*

## Investigation trace

*One paragraph. The diagnostic approach in summary. Why you chose to break it into phases the way you did. What hypothesis ordering made sense given the evidence at hand.*

## Phase trace

### Phase 1: <name> (PR #N)

*Hypothesis at the start of this phase. What you expected the fix to be and why. What the action was — what code changed. What the new evidence revealed once shipped. What the result told you about the next phase. Cross-reference the session log for the per-PR detail.*

### Phase 2: <name> (PR #N)

*Same shape. Each phase is a small story: hypothesis-action-result.*

### Phase 3: <name> (PR #N)

*Continue for as many phases as the campaign had.*

## Resolution

*One paragraph. What end-state proves the campaign closed. The concrete evidence — the 302 redirect, the green test run, the PowerShell line that no longer appears. Be specific enough that future-you can re-verify by reading this section alone.*

## What was ruled in

*Empirical claims that survived the campaign and are now load-bearing facts about the stack. These are claims someone could rely on without re-running the investigation. Phrase them as positive assertions, not "we think" or "probably."*

## What was ruled out

*Claims that the campaign disproved, or paths considered and abandoned with reason. This section saves future-you from reopening the same corpse. If a contributor six months from now considers approach X, this section is what tells them "we tried X-shaped thinking, here's why we didn't go that way."*

## Meta-lessons

*Patterns that aren't about this specific campaign but were extracted from it. Prose, not a numbered list. Each meta-lesson should either point to a standalone file in `ops/learned/` (link by path) or note that the lesson is too narrow to deserve its own learned doc and lives only in this campaign.*

## Links

- **PRs:** [#N](url), [#N](url), [#N](url)
- **Session logs:** `ops/sessions/YYYY-MM-DD-N.md`, …
- **Learned docs:** `ops/learned/<file>.md`, …
- **Related campaigns** (when relevant): `ops/campaigns/<file>.md`

---

## Future improvement (not yet implemented)

A future context-layer improvement could have CLAUDE.md instruct the agent to read relevant campaign docs when working in the same area, or when a recent session log points to one. Not currently configured. Reading every campaign on every session start would bloat context; the right access pattern is on-demand by area, triggered by either the agent or the human noticing relevance.
