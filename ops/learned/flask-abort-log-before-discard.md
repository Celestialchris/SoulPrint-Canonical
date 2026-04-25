## Log result errors before abort()

**From:** April 25, 2026 — fix/continuity-route-log-before-abort

---

### Pattern: log the error string before calling `abort(N)`

When a Flask route receives a result object that carries an error string — rather than raising an exception directly — the route must log that string before calling `abort()`. The reason is that `abort()` raises a `werkzeug.exceptions.HTTPException` immediately, discarding all local variables. Whatever was in `result.error` is gone. Werkzeug's WSGI access log only records the HTTP status line (`POST /path/to/route HTTP/1.1 500 -`), so from the PowerShell console it looks like the server silently failed.

The fix is a single `logger.error(...)` call using lazy `%s` formatting, placed directly before `abort()`:

```python
result = generate_continuity_packet(conversation, provider, store_path)
if result.error:
    logger.error(
        "continuity_generate failed for conversation_id=%s: %s",
        conversation_id,
        result.error,
    )
    abort(500)
```

The two-argument lazy form means no string interpolation happens unless the ERROR level is actually enabled, which matches the idiomatic Python logging contract and mirrors how the rest of `src/app/__init__.py` calls `app.logger.warning`.

### Where this applies

Any route that reads a service or result-object error field and then calls `abort()`. The pattern is distinct from exception handling: if the route is inside a `try/except`, use `logger.exception(...)` (which captures the traceback automatically). If the route reads a typed result with a plain `str | None` error, use `logger.error(...)` with the string. The distinction matters because `logger.exception` only works when an exception is currently in scope — using it outside a `try/except` will log `NoneType: None` instead of the real message.

### Test shape

Testing that the log line fires requires `self.assertLogs("src.app", level="ERROR")` as a context manager wrapping the POST call. The logger namespace must match the module where `logger = logging.getLogger(__name__)` is defined — in SoulPrint that is `src.app`. The captured `cm.output` list contains strings in `"LEVEL:logger.name:message"` format, so joining them and asserting substrings is the right check.

### The broader rule

Any route that reads a result-object error string before calling `abort(N)` must log the string first. `abort` discards all in-scope context. One line of logging turns an opaque 500 into a traceable failure.
