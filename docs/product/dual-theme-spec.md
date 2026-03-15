# SoulPrint — Dual Theme Specification

## The Principle

Two modes, one product. The dark mode is the Torchlit Vault — the original, the soul.
The light mode is the Parchment Observatory — the same product seen in daylight.
Both are SoulPrint. Neither is generic.

The user picks. The product remembers. Default: dark (it's the signature).

---

## Dark Mode — "Torchlit Vault" (default)

These are the exact values from app-mock.html. Do not modify them.

```css
[data-theme="dark"], :root {
  --bg: #0e0d0b;
  --surface: #161513;
  --raised: #1d1b18;
  --wine: #6b3a3a;
  --wine-soft: #8a5050;
  --gold: #c9a84c;
  --gold-dim: #a08848;
  --t1: rgba(210, 200, 185, 0.90);
  --t2: rgba(210, 200, 185, 0.55);
  --t3: rgba(210, 200, 185, 0.30);
  --t4: rgba(210, 200, 185, 0.12);
  --line: rgba(210, 200, 185, 0.06);
  --lane-chatgpt: #5a8a6a;
  --lane-claude: #a08848;
  --lane-gemini: #5a7a9a;
  --lane-native: #5a7a9a;
  --selection: rgba(107, 58, 58, 0.30);
  --input-focus: var(--gold-dim);
  --cta-border: var(--wine);
  --cta-text: var(--wine-soft);
  --cta-hover-bg: var(--wine);
  --cta-hover-text: var(--t1);
  --sidebar-bg: linear-gradient(180deg, rgba(22,21,19,0.72) 0%, rgba(14,13,11,0.90) 100%);
  --sidebar-brand: var(--gold-dim);
  --grain-opacity: 0.018;
  --vignette: linear-gradient(180deg, rgba(0,0,0,0.16) 0%, transparent 18%, transparent 82%, rgba(0,0,0,0.22) 100%);
}
```

Body atmosphere (dark only):
```css
body[data-theme="dark"] {
  background:
    radial-gradient(ellipse at 20% 14%, rgba(201,168,76,0.020) 0%, transparent 46%),
    radial-gradient(ellipse at 78% 22%, rgba(107,58,58,0.015) 0%, transparent 42%),
    radial-gradient(ellipse at 62% 70%, rgba(30,28,24,0.58) 0%, transparent 68%),
    radial-gradient(ellipse at 32% 84%, rgba(107,74,58,0.030) 0%, transparent 34%),
    var(--bg);
}
```

Hero wordmark text-shadow (dark only — see brand.md "Embers in Velvet Darkness"):
```css
[data-theme="dark"] .hero-wordmark {
  color: var(--t1);                              /* warm white, NOT gold */
  font-family: var(--font-display);              /* Forum */
  text-shadow:
    0 0 7px rgba(220, 140, 70, 0.50),            /* white-hot edge */
    0 0 20px rgba(210, 120, 60, 0.35),           /* close ember bloom */
    0 0 50px rgba(200, 100, 50, 0.18),           /* medium atmospheric */
    0 0 100px rgba(180, 80, 40, 0.07),           /* ambient warmth */
    0 2px 4px rgba(0, 0, 0, 0.4);                /* typographic anchor */
}
```

---

## Light Mode — "Parchment Observatory"

Same variable names. Different values. Same SoulPrint.

The light mode draws from the original 30-Day Vision palette
(parchment #f2f0e9, blue-grey #3f5f73) but keeps the wine/gold accents
so the product identity survives the switch.

```css
[data-theme="light"] {
  --bg: #f2f0e9;
  --surface: #eae7df;
  --raised: #ffffff;
  --wine: #6b3a3a;
  --wine-soft: #7a4444;
  --gold: #8a7030;
  --gold-dim: #7a6328;
  --t1: rgba(31, 41, 51, 0.92);
  --t2: rgba(31, 41, 51, 0.55);
  --t3: rgba(31, 41, 51, 0.32);
  --t4: rgba(31, 41, 51, 0.12);
  --line: rgba(31, 41, 51, 0.07);
  --lane-chatgpt: #4a7a5a;
  --lane-claude: #7a6328;
  --lane-gemini: #3f5f73;
  --lane-native: #3f5f73;
  --selection: rgba(107, 58, 58, 0.15);
  --input-focus: var(--gold-dim);
  --cta-border: var(--wine);
  --cta-text: var(--wine);
  --cta-hover-bg: var(--wine);
  --cta-hover-text: #f2f0e9;
  --sidebar-bg: linear-gradient(180deg, rgba(235,232,224,0.95) 0%, rgba(242,240,233,1) 100%);
  --sidebar-brand: var(--gold-dim);
  --grain-opacity: 0.012;
  --vignette: none;
}
```

Body atmosphere (light):
```css
body[data-theme="light"] {
  background:
    radial-gradient(ellipse at 20% 14%, rgba(138,112,48,0.018) 0%, transparent 46%),
    radial-gradient(ellipse at 78% 22%, rgba(107,58,58,0.010) 0%, transparent 42%),
    var(--bg);
}
```

Hero wordmark (light — no fire glow, just gold weight):
```css
[data-theme="light"] .hero-wordmark {
  color: #1f2933;
  text-shadow: none;
}
```

Light-mode page headings use --gold (which is now #8a7030 — a darker
warm gold that reads well on parchment). The Forum font carries authority
through letterform, not through luminance.

---

## What Stays Identical Across Both Modes

- Font families: Forum, Cormorant Garamond, JetBrains Mono
- Font sizes: all rem/px values unchanged
- Spacing: all padding, margin, gap values unchanged
- Layout: sidebar width, main margin, grid columns unchanged
- Component structure: conversation rows, citations, provenance blocks, stats grid
- Accent logic: wine for CTAs/actions, gold for headings/provenance
- Lane stripe pattern: 2px vertical stripe per provider
- Typography hierarchy: t1/t2/t3/t4 opacity scale
- No cards, no badges, no shadows rule (both modes)
- Selection highlight uses --selection variable

The entire UI is variable-driven. The toggle changes ~25 values. Everything else inherits.

---

## Toggle Implementation

Toggle lives in the sidebar footer, next to the version string.

```html
<button class="theme-toggle" type="button" aria-label="Toggle theme">
  <!-- Simple text: "light" or "dark" in JetBrains Mono, t3 -->
</button>
```

Behavior:
- Click toggles data-theme attribute on <html> (or <body>)
- Preference saved to localStorage under key "soulprint-theme"
- On load: check localStorage, apply saved preference, default to "dark"
- Transition: all color properties transition over 300ms ease
- No icon. No emoji. Just the word in mono: "light" / "dark"

---

## Landing Page: Dark Only

The landing page uses the Torchlit Vault (dark) exclusively.
It is the brand's signature surface. No toggle on the landing page.
The dark treatment sells the dream. The light mode is for daily use inside the app.

## Wrapped/Summary Page: Dark Only

The Wrapped page is the strongest glow surface. It stays dark regardless
of the user's app theme preference. This is the screenshot moment —
it must always look cinematic.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Default to dark | It's the signature. First impression matters. |
| Light mode is parchment, not white | White feels clinical. Parchment (#f2f0e9) feels like SoulPrint in daylight. |
| Wine and gold survive both modes | Product identity must persist across themes. |
| No fire glow in light mode | The text-shadow glow only works on dark backgrounds. Light mode earns authority through typography weight alone. |
| Landing and Wrapped stay dark always | These are brand surfaces, not utility surfaces. |
| Toggle is text, not icon | Consistent with the "no icons" rule from the design system. |
| localStorage for persistence | Simplest possible state. No server, no cookie. |
| 300ms transition on switch | Fast enough to feel responsive, slow enough to feel intentional. |
