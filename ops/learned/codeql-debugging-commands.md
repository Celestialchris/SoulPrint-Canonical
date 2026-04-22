## CodeQL and Dependabot debugging commands

**From:** April 22, 2026 (CodeQL sanitizer saga)

Paste-ready commands for diagnosing security alerts. All assume `gh` CLI authenticated and `$REPO = Celestialchris/SoulPrint-Canonical` (substitute as needed).

### List open alerts

```bash
gh api repos/$REPO/code-scanning/alerts?state=open | python -c "import json,sys; d=json.load(sys.stdin); print(len(d), 'open alerts'); [print(a['number'], a['rule']['id'], a['most_recent_instance']['location']['path']) for a in d]"
```

### Detail a specific alert (line, message, state)

```bash
gh api repos/$REPO/code-scanning/alerts/<N> | python -c "import json,sys; a=json.load(sys.stdin); i=a['most_recent_instance']; print('line:', i['location']['start_line']); print('msg:', i['message']['text']); print('state:', a['state'])"
```

Full alert JSON (for dataflow trace):

```bash
gh api repos/$REPO/code-scanning/alerts/<N> > alert_<N>.json
```

### Check scan workflow status

```bash
gh run list --limit 10
gh run watch
```

Default-setup CodeQL (no workflow file, configured via UI):

```bash
gh api repos/$REPO/code-scanning/default-setup
```

### Dismiss a CodeQL alert

```bash
gh api --method PATCH repos/$REPO/code-scanning/alerts/<N> \
  -f state=dismissed \
  -f dismissed_reason=<reason> \
  -f dismissed_comment="<comment with commit ref>"
```

Valid `dismissed_reason` for CodeQL: `false positive`, `won't fix`, `used in tests`.

### Dismiss a Dependabot alert

Different enum than CodeQL.

```bash
gh api --method PATCH repos/$REPO/dependabot/alerts/<N> \
  -f state=dismissed \
  -f dismissed_reason=<reason> \
  -f dismissed_comment="<comment with commit ref>"
```

Valid `dismissed_reason` for Dependabot: `fix_started`, `inaccurate`, `no_bandwidth`, `not_used`, `tolerable_risk`.

Rule of thumb: `not_used` when the vulnerable manifest no longer exists in the repo. `tolerable_risk` when the code path is unreachable or behind a trust boundary. `inaccurate` when the alert itself is wrong about applicability.

### After merging a security fix, verify closure

```bash
# Wait ~2-3 min for CodeQL rescan to complete after push to main
gh run list --limit 5

# Re-check open alerts
gh api repos/$REPO/code-scanning/alerts?state=open | python -c "import json,sys; d=json.load(sys.stdin); print(len(d), 'open')"
```

If count dropped, the shape matched. If new alert numbers appear with the same rule ID, the shape is still wrong; reconverge toward canonical.