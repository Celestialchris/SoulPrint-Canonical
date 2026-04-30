## Path-injection sanitizer: realpath + startswith (CodeQL py/path-injection)

**Recognized shape:**
```python
import os

# 1. Resolve the base root to its real path.
base_real = os.path.realpath(str(base_dir))
# 2. Resolve the candidate path to its real path.
target_real = os.path.realpath(str(candidate_path))
# 3. Containment check — strip trailing sep to avoid doubled separators on root paths.
base_prefix = base_real.rstrip(os.sep) + os.sep
if not (target_real.startswith(base_prefix) or target_real == base_real):
    raise ValueError("Path must be under base directory")
# 4. Use the validated path at the sink.
abs_path.parent.mkdir(parents=True, exist_ok=True)
abs_path.write_bytes(data)
```

**Why `realpath` on both sides:** Follows symlinks and collapses traversal sequences before comparison. CodeQL recognizes this idiom. `is_relative_to()` and `relative_to()` are not recognized taint sanitizers.

**Must be inlined at the sink:** CodeQL does not follow the shape through a helper function. The full resolve-base → resolve-candidate → startswith sequence must appear in the same function body as the filesystem write call.

**Trailing-sep normalization:** `base_real.rstrip(os.sep) + os.sep` ensures exactly one separator before startswith, avoiding false rejections on root paths (`/`, `C:\`).

Live canonical sources in this repo:
- `src/importers/claude_code_discovery.py:42-53` — home-directory variant (`normalize_projects_path`)
- `src/app/assets.py:81-85` — storage-base variant, inlined at the write sink

**Dismiss for the `relative_to` early implementation (historical):**

Dismiss as: "Used in tests / Won't fix"

Reason (paste this):
Validated via candidate.relative_to(home) which raises ValueError on paths resolving outside the user's home directory. Implementation uses:
1. String-level absolute-path check (rejects non-home-rooted absolute paths before resolve)
2. Home-anchored composition for relative paths (CodeQL's recommended pattern)
3. Final relative_to(home) as defense-in-depth for both branches

CodeQL's taint model does not recognize relative_to() as a sanitizer. The repeated autofix suggestions either (a) break legitimate in-home absolute paths, or (b) fail to constrain absolute paths at the filesystem level due to how Path composition handles absolute components. The current implementation is the correct resolution.

Local-first application; the ?path= parameter is a usability feature for users whose Claude Code projects live outside ~/.claude/projects/. Threat model assumes user owns their filesystem.

---

## Open-redirect sanitizer: urlparse + backslash reject (CodeQL py/url-redirection)

**Recognized idiom:**
```python
from urllib.parse import urlparse

def _safe_next(fallback_endpoint: str) -> str:
    nxt = request.form.get("next", "")
    if "\\" in nxt:
        return url_for(fallback_endpoint)
    parsed = urlparse(nxt)
    if nxt and not parsed.netloc and not parsed.scheme:
        return nxt
    return url_for(fallback_endpoint)
```

`urlparse(nxt).netloc` and `urlparse(nxt).scheme` are the CodeQL-recognized taint sanitizers for py/url-redirection. The backslash pre-reject is a pre-filter, not a replacement.

**Why reject-on-backslash, not strip-then-validate:** Stripping `\` from `/\evil.com` gives `/evil.com` (same-origin path, passes `urlparse`). Stripping from `\\evil.com` gives `evil.com` (no netloc or scheme, passes `urlparse`). Both are wrong acceptances. No legitimate internal redirect URL contains a backslash, so rejecting is safe with zero false-positive cost.

**The real `/\evil.com` bypass:** Browsers normalize `\` to `/` in Location headers. A `startswith("/") and not startswith("//")` guard passes `/\evil.com`; the browser treats it as `//evil.com`, a protocol-relative external URL.

**Interprocedural blindspot**

`urlparse(x).netloc` and `urlparse(x).scheme` are recognized as taint sanitizers only when
co-located with the `redirect()` sink in the same function body. Factoring them into a helper
breaks recognition even when the logic is identical. Fix: inline the 4-line check at each call
site. Same lesson as the `relative_to(home)` case above — CodeQL requires the idiom to be
visible at the sink, not behind an abstraction.

**Inline-but-factored is also insufficient**

Inlining the check at the sink is necessary but not sufficient. CodeQL requires the exact
canonical shape from its own docs: `nxt.replace("\\", "")` mutation first, then
`not urlparse(nxt).netloc and not urlparse(nxt).scheme` called twice inline in the guard,
with an early-return pattern (not a ternary at the sink). Factoring through a `parsed =
urlparse(nxt)` intermediate variable, an `is_safe` boolean, or `redirect(nxt if is_safe else ...)`
all break recognition. Source of truth: CodeQL py/url-redirection canonical example.