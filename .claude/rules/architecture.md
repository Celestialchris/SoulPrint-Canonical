# Architecture Rules
- Four layers: Truth (SQLite) → Legibility (browse/search) → Intelligence (derived) → Distribution
- Canonical ledger is authoritative. Derived never impersonates canonical.
- Native and imported lanes stay explicit. Compose read-only, never merge.
- Every derived artifact stores: source conversation stable IDs, generation timestamp, LLM provider, prompt template version.
- mem0 is optional, downstream, non-authoritative, gated off by default.
