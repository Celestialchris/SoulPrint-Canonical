## FTS timestamp sort stability

**From:** 2026-04-21, PR #136 (fix/cp5-archaeology-followups)

**Pattern:** When sorting FTS results by timestamp in ascending order in Python, use `"9999-12-31T23:59:59Z"` as the `or` fallback so empty-timestamp rows sort LAST, not first. Descending sort does not need the sentinel — DESC lexicographic ordering already demotes empty strings correctly.

**Why:** SoulPrint's FTS schema stores timestamps as strings, not NULLs. `_format_unix_ts(None)` returns `""`, so any imported message missing `created_at_unix` produces an FTS row with `timestamp=""`. In ASC sort, `"" < "2024-..."` lexicographically, so without a sentinel an undated row surfaces as "earliest." That directly contradicts archaeology mode's emotional promise ("your first conversation about this was..."). The callout block in `src/app/__init__.py::federated_browser` (added in PR #134) used the sentinel correctly from the start. CP5's Python-side merge sort in `src/retrieval/fts.py` (PR #135) missed the pattern and shipped the bug.

**Where this applies:** Any Python-side sort on the `timestamp` field of FTS result dicts with `or` fallback. Grep pattern: `lambda.*timestamp.*or\s*""` flags the bug shape.

**Survey (run 2026-04-21):**
```
src/app/__init__.py:1266:  min(..., key=lambda r: r.get("timestamp") or "9999-12-31T23:59:59Z")  ← CORRECT (sentinel)
src/retrieval/fts.py:443:  sort(key=lambda r: r.get("timestamp") or "", reverse=True)             ← CORRECT (DESC, demotes "" last naturally)
src/retrieval/fts.py:445:  sort(key=lambda r: r.get("timestamp") or "9999-12-31T23:59:59Z")       ← CORRECT (sentinel, fixed in PR #136)
```

**Detection:** Any Python sort on `r["timestamp"]` or `r.get("timestamp")` with `or ""` fallback AND ascending order: verify the fallback is `"9999-12-31T23:59:59Z"`. DESC sort with `or ""` is acceptable but deserves an inline comment.

**Related doctrine:** Pattern relies on `_format_unix_ts` using empty strings rather than NULL for missing timestamps. If that changes, these sentinel guards can be removed.
