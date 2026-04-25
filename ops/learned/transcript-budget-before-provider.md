## Enforce a transcript budget before any provider call

**From:** April 25, 2026 — fix/continuity-transcript-budget

---

### Pattern: cap the rendered transcript before sending to the provider

Local LLM providers with finite context windows (e.g., Ollama at 64K tokens) do not return a clear error when the input prompt exceeds their limit — they silently truncate the prompt from the front. In SoulPrint's continuity pipeline this means the `_SYSTEM_PROMPT` (which carries the strict four-key JSON-output contract) can be dropped before the model ever sees it. The model then emits empty or non-JSON output, the service raises `JSONDecodeError`, and the route returns 500.

The fix is to enforce a char budget on the rendered transcript **inside the SoulPrint process**, before `provider.complete()` is called. This is cheap, deterministic, and provider-agnostic.

```python
MAX_TRANSCRIPT_CHARS = 150_000  # ~37K tokens at ~4 chars/token

def _build_transcript(conversation) -> str:
    sorted_messages = sorted(conversation.messages, key=lambda m: m.sequence_index)
    kept, dropped = _truncate_messages_to_budget(sorted_messages, MAX_TRANSCRIPT_CHARS)
    lines = [_render_message_for_transcript(m) for m in kept]
    if dropped > 0:
        marker = f"[{dropped} earlier messages truncated to fit context]"
        return marker + "\n" + "\n".join(lines)
    return "\n".join(lines)
```

The budget constant (`150_000`) leaves headroom for the system prompt (~700 chars), the `--- Transcript ---` wrapper, and a long JSON response (`max_tokens=16384`) inside a 64K-context window. For a smaller-context provider, lower the constant.

### Drop strategy

Oldest messages are dropped first. The most-recent message is always preserved, so the model has the immediate conversational context and can at minimum produce a summary. If the most-recent message alone exceeds the budget (e.g., a single giant paste), its content is tail-truncated with a `[message truncated]` prefix rather than discarded.

### Where this applies

Any route or service that assembles a long text artifact from canonical conversation messages before calling a provider. The pattern is distinct from the `abort(500)` logging rule: that rule surfaces failures after they happen; this rule prevents the failure class entirely.

### Test shape

Three tests in `TranscriptBuildingTest` in `tests/test_continuity_service.py`:

1. Under-budget: assert no truncation markers and exact output.
2. Over-budget (many small messages): assert marker regex at start, assert last message is preserved, assert length is within budget + 100.
3. Single giant message: assert `[message truncated]` is present, assert tail content is present, assert length is within budget + 100.

### The broader rule

Before calling a finite-context provider, measure the assembled prompt. If it can exceed the context window for realistic inputs, add a pre-call budget cap with explicit truncation markers. Silent provider-side truncation is invisible to callers and produces unpredictable failures.
