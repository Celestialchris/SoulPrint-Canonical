\# Netlify to Cloudflare Pivot



Date: 2026-04-30



\## Context



The project switched away from Netlify after repeated failing checks/tests and unresolved deployment friction.



\## Problem



Netlify became a major time sink. The failure loop did not produce enough useful signal to justify continued effort.



\## Decision



Move deployment direction to Cloudflare.



\## Rationale



\- Repeated Netlify failures consumed too much time.

\- The issue became infrastructure drag rather than product progress.

\- Cloudflare became the cleaner forward path.



\## Follow-up



\- Do not treat Netlify as the default deployment path unless reopened deliberately.

\- Any future deployment doctrine should account for this pivot.

