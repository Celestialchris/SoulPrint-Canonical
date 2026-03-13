# SoulPrint — Project Audit

*March 13, 2026 — Comprehensive review of project knowledge base and planning materials.*

---

## I. What Exists Right Now

### Project Knowledge Files (8 files, 127K)

| File | Purpose | Status |
|------|---------|--------|
| `SOULPRINT-30-DAY-VISION.md` | Product vision, 30-day shipping plan, revenue projections, competitive positioning | **Active. Canonical planning doc.** |
| `SOULPRINT-BRAND-PROMPTS.md` | 5 sequential Claude Code prompts for brand/landing/desktop/freemium/wrapped | **Active. Execution queue.** |
| `PROMPT-9-SURFACE-MOCK.md` | Detailed "Torchlit Vault" design system spec for 9-surface HTML mock | **Active. Design contract.** |
| `Hero_Thraenix_GateII_Cleansed.html` | Thraenix Gate II — card-based "Seven Sealed Keys" page. Georgia font, rounded cards, emoji icons. | **Stale. Design heritage only. Does not match current direction.** |
| `Hero_Thraenix_Orb_Phoenix_Cleaned_Glimpses.html` | Thraenix Gate I — Forum + Crimson Pro, dark gradient, phoenix orb SVG, law sections. 221 lines. | **Reference. Source of the Forum font DNA and glow treatment.** |
| `Hero_Thraenix_Orb_Phoenix_Cleaned_Glimpses_Final.html` | Same as Glimpses with minor refinements. 211 lines. Near-identical to the non-Final. | **Redundant. One of these should be removed.** |
| `Hero_Thraenix_Orb_Phoenix_Cleaned_GoldenGlow.html` | Minimal — 35 lines, Georgia font, gold text-shadow on #000 background. "The Flame Beckons." | **Stale. Superseded by the Torchlit Vault direction.** |
| `Hero_Thraenix_Orb_Phoenix_Cleaned_With_Occult_Statement.html` | Thraenix Gate I variant with expanded "Three Laws" content sections. 304 lines. | **Reference. Content heritage, not design reference.** |

### Uploaded Planning Documents (5 files)

| File | Purpose | Status |
|------|---------|--------|
| `Project_Manager.md` | Senior PM/design review. Hierarchy critique, nav grouping proposal, glow grammar, provenance component family, "austere cathedral" direction. | **Critical. Contains the best UX analysis in the stack.** |
| `Soulprint_Upgrade.md` | Continuity packet architecture. Session handoff, lineage model, bridge assembly, engine choice (existing intelligence boundary). | **Critical. Defines the next engineering milestone.** |
| `Design.md` | Marketability analysis. Two-personality brand split (public lucid / inner glow), "owned memory instrument" thesis, commercial corrections. | **Critical. Reconciles design soul with market viability.** |
| `SOULPRINT-30-DAY-VISION.md` | Duplicate of project file. | **Remove from uploads.** |
| `SOULPRINT-BRAND-PROMPTS.md` | Duplicate of project file. | **Remove from uploads.** |

---

## II. Where It's Messy

### Problem 1: No hierarchy between documents

All 8 project files sit at root level. There is no separation between:
- **Active roadmap** (what to build next)
- **Design contracts** (how it should look)
- **Design heritage** (where the aesthetic came from)
- **Frozen decisions** (what has been decided and should not be revisited)

A senior engineer opening this project would spend 20 minutes just figuring out which files are current.

### Problem 2: Five Thraenix HTML files with unclear roles

The five `Hero_Thraenix_*.html` files are design DNA — they're where Forum, the dark warm background, the gold/wine palette, and the glow treatment originally came from. But:

- Two are near-identical (`Glimpses` vs `Glimpses_Final`)
- One is superseded (`GoldenGlow` — 35 lines, Georgia font, predates the current direction)
- One is content heritage only (`GateII_Cleansed` — uses card layout that the current design system explicitly prohibits)
- None of them are labeled as "reference" vs "active"

This reads like a browser tabs graveyard, not a curated design library.

### Problem 3: Critical planning docs live only in uploads

The three most important strategic documents — `Project_Manager.md`, `Soulprint_Upgrade.md`, and `Design.md` — are uploaded files, not project knowledge. That means:
- They disappear between conversations
- They're not searchable in future sessions
- They're not organized relative to the other docs

### Problem 4: No single source of truth document

There is no README or INDEX that says: "Here is SoulPrint. Here is what exists. Here is what to build next. Here are the frozen decisions." The 30-Day Vision is close, but it's a planning document, not a project map.

### Problem 5: Overlapping scope between documents

- The 30-Day Vision covers brand, landing, desktop, freemium, and wrapped.
- The Brand Prompts cover the same five features as executable prompts.
- The Design doc covers brand direction and market positioning.
- The Project Manager doc covers brand direction and UX specifics.
- The Upgrade doc covers a completely different axis (continuity packets) that isn't mentioned in the Vision or Prompts.

Nobody has reconciled these into one coherent "here is the actual plan."

### Problem 6: No decision log

Multiple decisions have been made across conversations:
- Design direction: Torchlit Vault (frozen)
- Lane 1 (continuity packets) before Lane 2 (lineage suggestions)
- Engine choice: existing intelligence boundary, not mem0
- Typography: Forum / Cormorant Garamond / JetBrains Mono
- Palette: dark warm bg, wine accent, gold for provenance
- Freemium split: import/browse/passport free, ask/intelligence paid

None of these are recorded in a single place. They live scattered across markdown files and conversation history.

---

## III. What a Senior Engineer Would Do

### Step 1: Establish a project README

One file at root that answers:
- What is SoulPrint?
- What is the current state?
- What are the frozen decisions?
- What is the next milestone?
- Where does each document live and why?

### Step 2: Reorganize into clear categories

```
/
├── README.md                          ← project map (new)
├── DECISIONS.md                       ← frozen decisions log (new)
├── ROADMAP.md                         ← sequenced build plan (new)
│
├── roadmap/
│   ├── 30-DAY-VISION.md              ← renamed from SOULPRINT-30-DAY-VISION.md
│   ├── UPGRADE-CONTINUITY.md         ← from Soulprint_Upgrade.md
│   └── BRAND-PROMPTS.md             ← renamed from SOULPRINT-BRAND-PROMPTS.md
│
├── design/
│   ├── TORCHLIT-VAULT-SPEC.md        ← renamed from PROMPT-9-SURFACE-MOCK.md
│   ├── DESIGN-MARKET-ANALYSIS.md     ← from Design.md
│   ├── UX-REVIEW.md                  ← from Project_Manager.md
│   └── heritage/
│       └── thraenix-reference.html   ← single consolidated reference file
│
└── (no other files at root)
```

### Step 3: Consolidate Thraenix files

Keep one. The `Glimpses_Final` variant is the most complete and contains the Forum + Crimson Pro + dark gradient + phoenix orb + glow treatment that the Torchlit Vault direction descends from. Archive or remove the other four.

### Step 4: Write the decision log

Every frozen decision gets one line with the date, the decision, and the rationale. No prose. No philosophy. Just facts.

### Step 5: Write the sequenced roadmap

One document that says: "Here is what to build, in what order, and why." It should reconcile the 30-Day Vision (distribution focus) with the Upgrade doc (continuity packets) and the user's explicit decision to do Lane 1 first, design frozen.

---

## IV. The Real Priority Sequence

Based on everything in the project files and uploads, and the user's explicit Lane 1 decision:

### Phase A: Continuity Packet MVP (Lane 1)
This is the next engineering work. Not design. Not landing page. Not desktop wrapper.

1. Define `DerivedContinuityPacket` schema
2. Add `src/intelligence/continuity.py` using existing provider boundary
3. Add persistence for continuity artifacts
4. Add endpoint: `POST /intelligence/continuity/<conversation_id>`
5. Add UI: "Generate Continuity Packet" button on conversation detail
6. Add UI: "Copy for New Chat" action on packet view
7. Tests for schema, generation, persistence, endpoint

### Phase B: Bridge Assembly
Build the minimal next-chat handoff from packet(s) + cited canonical snippets.

### Phase C: Lineage Suggestions (Lane 2)
Propose parent thread detection. Time + keywords + entities + tags. Always inspectable.

### Phase D: Distribution (30-Day Vision features)
Only after the continuity spine exists:
1. Brand identity + logo
2. Landing page
3. Desktop wrapper
4. Freemium gate
5. Wrapped summary page

This is the order that builds product value before product packaging.

---

## V. What Should Be in the Project Knowledge

After cleanup, the project knowledge should contain exactly these files:

| File | Role |
|------|------|
| `README.md` | Project map. What SoulPrint is, current state, file index. |
| `DECISIONS.md` | Frozen decisions with dates. |
| `ROADMAP.md` | Sequenced build plan. |
| `roadmap/30-DAY-VISION.md` | Full 30-day product vision (reference). |
| `roadmap/UPGRADE-CONTINUITY.md` | Continuity packet architecture (reference). |
| `roadmap/BRAND-PROMPTS.md` | Claude Code execution prompts (reference). |
| `design/TORCHLIT-VAULT-SPEC.md` | Canonical design system spec. |
| `design/DESIGN-MARKET-ANALYSIS.md` | Market positioning analysis (reference). |
| `design/UX-REVIEW.md` | Senior PM critique (reference). |
| `design/heritage/thraenix-reference.html` | Single Thraenix design DNA file (reference). |

Total: 10 files, clear hierarchy, no duplicates, no orphans.
