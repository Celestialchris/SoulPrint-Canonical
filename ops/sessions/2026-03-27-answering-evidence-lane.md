# Session: Answering Evidence Lane

## Goal
Improve the answering layer without changing the canonical ledger or breaking retrieval determinism.

## Chosen direction
Start with retrieval-quality improvements before UX polish.

## Why
- imported retrieval is conversation-level at output time
- matched message evidence is not carried forward strongly enough
- better evidence should come before prettier answers

## Planned order
1. improve imported-lane ordering
2. add additive evidence fields
3. consume evidence_text in answering
4. add citation excerpts
5. later: optional LLM synthesis
6. later: trace filtering

## Full-suite result after Phase A
- Targeted retrieval and answering tests passed
- Full pytest surfaced 4 existing workspace-home test failures
- Failures are assertion drift against current workspace UI, not evidence-lane regressions

## Next task
- Align tests/test_workspace_home.py with current workspace truth