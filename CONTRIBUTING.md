# Contributing to SoulPrint

## Getting started

See [docs/getting-started.md](docs/getting-started.md) for setup instructions.

## Running tests

All tests must pass before submitting a PR:

```bash
python -m pytest tests/ -v
```

## Rules

### Test coverage
- Every route needs tests
- Every importer needs tests (adapter, detector, fixture, registry entry)
- No route without tests, no import without duplicate guards

### PR discipline
- One bounded task per PR — reviewable and self-contained
- No route sprawl, no dashboard bloat
- Derived layers must never mutate canonical records
- Keep lanes separate — compose federated retrieval read-only, never merge structurally

### Code style
- Smallest working implementation over speculative architecture
- Preserve existing behavior unless the task explicitly changes it
- Flag uncertainty instead of inventing hidden structure

## Out of bounds

The following are explicitly out of scope for contributions:

- Portability/USB/capsule framing or language
- mem0 activation (adapter exists but is gated off by design)
- Desktop packaging (Tauri, Electron, etc.)
- Mobile apps
- Cloud/hosted deployment

## Reporting issues

Use the [GitHub issue templates](.github/ISSUE_TEMPLATE/) for bug reports and feature requests.
