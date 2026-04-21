## Redirect-after-action safety

**From:** April 21, 2026, CP1 starring (feat/starring-everywhere, prompt: CP1_Starring-conversations+notes.md.md)

---

### Pattern 1: `_safe_next()` — validating a user-supplied redirect target

**Pattern:** Any POST route that accepts a `next` form field must validate it before redirecting. Use this helper:

```python
def _safe_next(fallback_endpoint: str) -> str:
    nxt = request.form.get("next", "")
    if nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return url_for(fallback_endpoint)
```

**Why:** A raw `redirect(request.form.get("next"))` is an open redirect vulnerability. The two conditions catch distinct attack shapes: `http://evil.com` fails `startswith("/")`, `//evil.com` passes the first check but fails `not startswith("//")` (protocol-relative URL). Empty string also falls through to the safe fallback. The archive routes in SoulPrint hardcode their redirect endpoints, so they never needed this. Star routes return the user to their filtered view, which requires an untrusted `next` — hence the guard.

**Where it applies:** Any POST route that accepts a `next` redirect URL from a form or query param. Standard Django and Rails patterns use identical logic.

**Scope note:** The guard only needs to live in one place — define `_safe_next` once near the routes that use it, not as a module-level utility. It captures `request` from Flask's thread-local, so it works naturally inside `create_app()` closures.

---

### Pattern 2: `session.pop()` in Jinja2 templates for scope-locked routes

**Pattern:** When a route body cannot be modified (scope lock or ownership boundary), but you need to surface a flash notice on the page it renders, access the Flask session directly in the Jinja2 template:

```jinja2
{% set _notice = session.pop("export_notice", none) %}
{% if _notice %}
  <p class="metadata-line" role="status">{{ _notice }}</p>
{% endif %}
```

**Why:** Flask's `session` object is a Jinja2 global — templates can read and mutate it without a route doing the popping. This is valid and side-effect-free (popped once, gone). In CP1, the `/chats` route was scope-locked but `view.html` needed to show the star/unstar confirmation notice. Adding `session.pop()` to the template avoided touching the locked route entirely.

**Tradeoff:** Slightly harder to audit flash message flow (have to check templates, not just routes). Keep the pattern narrow: one `session.pop` at the top of the relevant `{% block content %}` block, never scattered through loops or partials.

**Where it applies:** When a route body is off-limits but its template needs to render a one-time session message. Don't use if the route body is editable — pop in the route, pass the value as a template variable.
