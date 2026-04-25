---
date: 2026-04-25
status: resolved
area: intelligence
surface: continuity
provider: ollama
model: gemma3:4b
prs: [162, 165, 166]
tags:
  - continuity
  - ollama
  - json-mode
  - transcript-budget
  - silent-abort
  - debugging-campaign
---

# Campaign: continuity packet generation on Ollama / Gemma3:4b

## Symptom

`POST /intelligence/continuity/85` returned 500 with no diagnostic context in PowerShell. Werkzeug's WSGI access log printed only `POST /intelligence/continuity/85 HTTP/1.1 500 -` with no traceback and no error message. Conversation 85 (`Dream Summit Discovery`, 278 messages) was the reproducible failure case. The continuity surface was non-functional for any conversation long enough to matter, and the failure was opaque — there was no observable signal saying *why* it was failing.

## Investigation trace

The campaign ran as three small PRs across one afternoon. Each PR changed exactly one variable: visibility, then prompt size, then output syntax. The phase ordering was forced by the evidence available — we couldn't reason about prompt-size or output-syntax problems until logging exposed which one was firing first. The temptation to ship a single hardening patch covering all three concerns was real (ChatGPT had drafted exactly that prompt), but a bundled fix would have left us unable to attribute which layer was load-bearing if the next regression hit. The diagnostic blade kept causality clean.

## Phase trace

### Phase 1: Visibility (PR #162)

The hypothesis was that the 500 had a real cause that Werkzeug was hiding. The route at `intelligence_continuity_generate` was reading `result.error` from `generate_continuity_packet` and then calling `abort(500)`, which raises `werkzeug.exceptions.InternalServerError` immediately and discards everything in scope. The error string was being captured into a local variable and then thrown away.

The fix was a single `logger.error` call before `abort(500)`, using lazy `%s` formatting consistent with the file's existing `app.logger.warning` patterns. One route test was added covering the malformed-JSON path via `assertLogs("src.app", level="ERROR")`.

The first retry of conversation 85 logged: `Failed to parse provider response as JSON: Expecting value: line 1 column 1 (char 0)`. The `(char 0)` was the diagnostic key — the JSON parser hit position zero and found nothing parseable, meaning the model had returned an empty or non-JSON-prefixed response. Cross-referencing Ollama's GIN log showed `truncating input prompt limit=65536 prompt=75164 keep=4 new=65536`, with `keep=4` confirming the runner had front-truncated the prompt down to four leading tokens of context. The system prompt's "return JSON" instruction was being amputated by Ollama before the model saw it. Phase 2 was now obvious.

See `ops/sessions/april-25-2026-1.md` for the per-PR detail.

### Phase 2: Transcript budget (PR #165)

The hypothesis was that SoulPrint needed to enforce its own prompt size before sending, so the system prompt and recent messages always fit in Ollama's 64K-token context. The first attempt set `MAX_TRANSCRIPT_CHARS = 150_000` based on a 4-chars/token English-prose estimate, with a `_truncate_messages_to_budget` helper that dropped oldest messages while preserving at least the most-recent one and prepended a marker line.

The retry produced two new signals. First, `continuity transcript: dropped 121 oldest messages to fit budget (150000 chars)` confirmed the budget was active. Second, Ollama still logged `truncating input prompt limit=65536 prompt=75363 keep=4`. The 150K char budget was rendering to ~75K tokens — the actual Gemma/Ollama tokenizer density was ~2 chars/token for production conversation content, twice as dense as the English-prose estimate.

A second pass lowered the constant to `MAX_TRANSCRIPT_CHARS = 80_000`. At observed density that yields ~40K input tokens, plus 16K reserved for response and ~500 tokens of overhead, totaling ~56.5K tokens with ~9K of headroom in the 65K context. Tests required no modification because they referenced `MAX_TRANSCRIPT_CHARS` by import rather than hardcoding the value.

The retry of conversation 85 with the 80K budget produced a different JSON error: `Failed to parse provider response as JSON: Extra data: line 1 column 10 (char 9)`. Reading the Ollama log carefully showed two `/v1/chat/completions` calls in that test window — the first at 11:55:58 hit truncation at 75363 tokens (likely a different surface that doesn't enforce the budget), and the second at 11:57:09 was the continuity call, took only 11.3 seconds (consistent with a small prompt), and triggered no truncation warning. The budget was working. The remaining failure was downstream of context loss.

The exact error message was reproducible in Python: `json.loads('"summary": "test"')` raises `Extra data: line 1 column 10 (char 9)`. The model was emitting top-level key-value pairs without enclosing braces. Model-intrinsic JSON malformation, not a context problem.

See `ops/sessions/april-25-2026-3.md`. The calibration note appended to `ops/learned/transcript-budget-before-provider.md` documents the empirical 2 chars/token density.

### Phase 3: Grammar-constrained output (PR #166)

The hypothesis was that small instruction-tuned models (Gemma3:4B class) are unreliable at strict JSON via prompt instruction alone, and the structural fix is grammar-constrained sampling via Ollama's OpenAI-compatible `response_format` parameter. The model would no longer be able to emit invalid JSON syntax because the runner only samples tokens that keep the output parseable.

The change threaded a keyword-only `response_format: dict | None = None` parameter through the `LLMProvider` Protocol and all four implementations. `OpenAIProvider.complete` builds a `kwargs` dict and conditionally adds `response_format` and `temperature=0` before calling `client.chat.completions.create(**kwargs)` — the dict pattern is more defensive than passing `response_format=None` directly because some OpenAI SDK versions treat None differently from absent. `StubProvider` and `AnthropicProvider` accept and ignore the parameter (Anthropic JSON mode is out of scope). The continuity call site requests `response_format={"type": "json_object"}`. Three new tests covered the new code paths.

Conversation 85 retried clean: `POST 302` redirect to `GET 200` serving a populated continuity packet. Summary, decisions, open loops, and entity map all contained substantive content extracted from the actual conversation, not the syntactically-valid-but-empty output the worst case had predicted.

See `ops/sessions/april-25-2026-4.md`.

## Resolution

End-to-end working continuity surface on conversation 85, confirmed by `POST /intelligence/continuity/85 → 302` followed by `GET /intelligence/continuity/85 → 200` serving a real continuity packet. The packet's content is semantically meaningful — the model identified specific decisions, open loops, and entities from the conversation, not just emitted a structurally-valid placeholder. Test suite at 1049 passing.

A small artifact noted but not fixed: the model rendered filenames inside JSON string fields using markdown link syntax (`[keywords.md](http://keywords.md)`). This is the model deciding to be helpful in a context where helpfulness is wrong, not a pipeline defect. One sentence in `_SYSTEM_PROMPT` would suppress it ("Do not use Markdown link syntax in field values; use plain text"). Deferred until it visibly bothers the UI.

## What was ruled in

Gemma3:4B is capable of producing semantically meaningful structured extraction on continuity-shaped tasks when given grammar-constrained sampling. The model was never the bottleneck for this task; the bottleneck was the brittleness of asking a small model to do long-context reasoning, strict JSON output, and instruction-following all simultaneously without rails.

The "rails own the model" thesis: small local models can serve in production when the application enforces the parts the model can't be trusted to handle (context budgeting, output grammar, parse failure logging). The model is a swap-in component; the discipline is the product. This applies beyond continuity — every intelligence feature in SoulPrint that calls a local LLM benefits from the same pattern.

`logger.error` before `abort(N)` is the canonical pattern for any Flask route that reads a result-object error string before aborting. Documented in `ops/learned/flask-abort-log-before-discard.md`. The `abort` call discards all in-scope context; one log line turns an opaque 500 into a traceable failure.

The 80K char transcript budget at observed ~2 chars/token Gemma/Ollama density is safe for a 65K-token context with `max_tokens=16384` reserved for response. Empirical, not theoretical. Documented in `ops/learned/transcript-budget-before-provider.md`.

## What was ruled out

A model upgrade was not strictly necessary for the continuity task to work. Gemma3:4B with rails produces useful packets. A larger model (12B, 27B) would likely make the rails less critical and reduce the failure surface, but the campaign proved the small-model-with-rails configuration is viable.

Prompt-instruction-alone for strict JSON output is not reliable on small models in the 3B-4B parameter class. The system prompt repeatedly demanded JSON; the model emitted JSON-shaped text with structural errors (missing braces, invalid escapes, key-value pairs without object delimiters). This is a sampling-layer problem, not a comprehension problem; no amount of prompt tuning fixes it. Grammar enforcement does.

A bundled hardening prompt that fixed all three layers in one PR would have worked but obscured causality. We considered it (ChatGPT drafted exactly that prompt) and explicitly chose three sequential PRs instead. The choice paid off in Phase 2, where the first 150K budget didn't fully solve the problem and the new evidence redirected the work — that redirect would have been invisible inside a bundled patch.

Ollama's prompt-side truncation with `keep=4` is silent from the calling app's perspective. The runner logs a WARN line, but the OpenAI-compatible chat completion still returns a 200. The system-prompt-loss-by-truncation failure mode is invisible to anything reading only the HTTP response. SoulPrint must enforce its own context discipline rather than relying on the provider to fail loudly.

## Meta-lessons

The diagnostic blade principle that frames this template was forged on this campaign. Each phase's evidence redirected the next phase's hypothesis in ways a bundled patch could not have surfaced. Worth re-reading the operating principle in `ops/campaigns/_template.md` before starting the next multi-PR debugging sequence.

Two patterns earned standalone learned docs: `ops/learned/flask-abort-log-before-discard.md` (visibility before recovery) and `ops/learned/transcript-budget-before-provider.md` (with the JSON-mode addendum appended in Phase 3). Both are reusable beyond continuity — the abort-log pattern applies to any Flask route that reads a typed result before aborting, and the budget pattern applies to any call into a finite-context provider.

A pattern that did NOT earn a standalone learned doc but is worth noting in this campaign: when interpreting Ollama logs during multi-call test windows, read the GIN timestamps and durations carefully. A truncation warning attached to a 45-second call is not the same event as the 11-second call that immediately followed. Misreading the log timing nearly produced a wrong conclusion in Phase 2.

## Links

- **PRs:** [#162](https://github.com/Celestialchris/SoulPrint-Canonical/pull/162), [#165](https://github.com/Celestialchris/SoulPrint-Canonical/pull/165), [#166](https://github.com/Celestialchris/SoulPrint-Canonical/pull/166)
- **Session logs:** `ops/sessions/april-25-2026-1.md`, `ops/sessions/april-25-2026-3.md`, `ops/sessions/april-25-2026-4.md`
- **Learned docs:** `ops/learned/flask-abort-log-before-discard.md`, `ops/learned/transcript-budget-before-provider.md`
