# site

SvelteKit + TypeScript marketing-site foundation for soulprint.dev.

This is the future marketing-site foundation for soulprint.dev. It is not the SoulPrint app cockpit and does not read from the canonical ledger.

The live marketing surface at https://soulprint.dev is currently served by `landing/index.html` at the repo root. This directory is the in-progress SvelteKit rewrite and does not deploy yet.

## Local development

```bash
pnpm install
pnpm dev
pnpm build
pnpm preview
```

`pnpm check` runs the SvelteKit + TypeScript type check.
