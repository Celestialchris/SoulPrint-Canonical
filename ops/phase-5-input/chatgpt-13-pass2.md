# chatgpt-13-pass2.md

Status note:

Pass 1 is process record only. It reviewed `experts.md` without `template-h.md` and over-recommended several additions.

Pass 2 is the live recommendation. It reviewed `experts.md` together with `template-h.md` and retracts or narrows most Pass 1 items.

Phase 5 should treat Pass 2 as the active agenda. Pass 1 remains only as audit trail.

---

-----------------------------------------------------------

Experts.md read without template-h:




The file is already strong where most systems are weak: it has **scope boundaries**, **one expert + one stance**, and a **report feedback loop**. The main weakness is sharper:

**It tells the agent what to do after routing, but it does not fully define how routing is chosen, challenged, verified, or retired.** 

That is what I would add.

## 1. Add a Router Gate before Section A

Right now, the doctrine says: pick one technical expert, one stance, read the linked context, then draft with Template H. Good. But it needs a **pre-routing decision block** so Claude/ChatGPT/Codex cannot casually choose the wrong expert.

Add a section before Section A:

```md
## Section 0: Router Gate

Before selecting a Section A expert, classify the task:

1. Is this product behavior, code hardening, data/storage, security, testing, UI surface, marketing site, importer work, or intelligence output?
2. Which files or directories are likely touched?
3. Which expert owns those files?
4. Which adjacent expert must NOT be used?
5. What would prove the routing choice wrong?

The selected expert must be named with one sentence:

"Chosen expert: X, because the task primarily changes Y. Not Z, because Z owns A/B/C but this branch does not."

If routing is ambiguous, split the task into separate prompts instead of merging experts.
```

This makes the system less mystical and more enforceable.

The real law should be:

**No routing without a reason. No reason without boundaries.**

## 2. Add a Verification Judge

This is the biggest missing entity.

You currently have Code Quality Engineer, Security Reviewer, Test Engineer, etc. But no final role whose only job is to ask:

**Did the work actually satisfy the mission?**

Not “did tests pass?”
Not “does the code look good?”
But: **was the original intent fulfilled without scope bleed?**

Add this either as a Section B stance or a closing protocol. I prefer **not** making it a stance, because every branch needs verification. Make it a universal closing gate.

```md
## Universal Closing Gate: Verification Judge

Every routed prompt ends with a verification pass.

The agent must answer:

1. What was the requested outcome?
2. What changed?
3. What did not change?
4. What evidence proves the outcome?
5. What tests, commands, screenshots, or reports support the claim?
6. What remains risky or unproven?
7. Did the branch stay inside the selected expert and stance?

If proof is missing, the branch is not complete. Do not claim success from intention.
```

This is teeth. Without this, the Experts can still produce confident garbage.

## 3. Fill Importer Engineer now

The file already admits Importer Engineer is the missing domain. Do not leave that parked for long. Importers are central to SoulPrint because the whole product depends on importing memory cleanly.

Draft it as a real expert:

```md
### Importer Engineer

**Lens.** Provider-specific ingestion into the canonical ledger. Importers translate messy external exports into stable, inspectable SoulPrint records without making the importer itself canonical. The importer is a bridge, not the source of truth.

**Owns.** ChatGPT export importers, Claude export importers, markdown importers, future provider importers, source metadata mapping, duplicate detection policy, import summaries, skipped/imported counts, source-conversation IDs, malformed export handling, and importer-specific regression tests.

**Stack docs.**
- Python `json`: https://docs.python.org/3/library/json.html
- Python `pathlib`: https://docs.python.org/3/library/pathlib.html
- SQLite: https://www.sqlite.org/docs.html

**Project canon.**
- `DECISIONS.md`: canonical ledger rules, duplicate import policy, source/source_conversation_id contract.
- `.claude/rules/python-patterns.md`: storage two-lane pattern.
- `.claude/rules/soulprint-testing.md`: importer regression-test style.
- Existing importer docs or README paths once created.

**Learned patterns.**
- Add after first importer branch produces reusable handling rules.

**Triggers.**
- "Add Claude export import."
- "Import this new provider format."
- "Fix duplicate detection during import."
- "The importer skipped too much."
- "Map external conversation IDs into canonical records."
- "Add malformed export handling."

**Out of scope.**
- Schema changes required by importers: Data and Storage Engineer.
- UI route for upload/import review: Flask App Engineer.
- Test harness mechanics: Test Engineer.
- Intelligence over imported data: Intelligence/Answering Engineer.
```

This should exist. Otherwise importer work will keep smearing across Data, Flask, and Test.

## 4. Add Release/Ops Engineer

You have CI under Test Engineer and marketing deploy under Marketing Site Engineer, but you do not have a clear owner for **release discipline, environment contracts, dependency hygiene, packaging, and operational scripts**.

This matters if SoulPrint grows past hobby scale.

Suggested expert:

```md
### Release/Ops Engineer

**Lens.** The project must run cleanly outside the author’s machine. Setup, environment variables, scripts, dependency boundaries, CI entrypoints, release notes, and deployment instructions must be boring, repeatable, and documented.

**Owns.** Setup scripts, `.env.example`, dependency pins, local run commands, smoke-test commands, release checklist, CI command consistency, packaging boundaries, deployment docs, and environment-specific failure handling.

**Triggers.**
- "The setup instructions are broken."
- "Fresh clone does not run."
- "Add a release checklist."
- "Pin or upgrade dependencies."
- "Make CI and local commands match."
- "Prepare this for a tagged release."

**Out of scope.**
- Test harness design: Test Engineer.
- Security CVE triage: Security Reviewer.
- Marketing-site deploy mechanics under `site/`: Marketing Site Engineer, unless the issue is project-wide release process.
- Feature implementation.
```

This is the boring adult in the room. Every serious repo needs one.

## 5. Add Docs/Canon Steward

The doctrine depends heavily on canon files, learned patterns, rules, reports, and Template H. But no expert owns **doctrine drift**.

This is dangerous. Over time, `CLAUDE.md`, `DECISIONS.md`, `template-h.md`, `experts.md`, learned patterns, and reports will contradict each other.

Add:

```md
### Docs/Canon Steward

**Lens.** Project memory must remain coherent. Canon files, decisions, learned patterns, expert reports, and templates must not drift into contradiction or duplication. This expert preserves the map, not the territory.

**Owns.** `CLAUDE.md`, `DECISIONS.md`, `template-h.md`, `experts.md`, `ops/learned/`, `ops/experts/`, terminology audits, doctrine portability checks, deprecated-rule removal, and cross-file consistency.

**Triggers.**
- "Update the doctrine after this branch."
- "These docs contradict each other."
- "Promote this report observation into learned patterns."
- "Audit Template H against Experts."
- "Prepare this routing system for another project."
- "Remove stale canon."

**Out of scope.**
- Writing marketing copy: Brand Guardian or Community-Voice Writer.
- Product strategy decisions.
- Feature implementation.
- Test, security, or schema ownership.
```

This one is important for your larger vision because your Experts are meant to become portable across SoulPrint, Akademos, Thraenix, and future systems. Without a Canon Steward, the doctrine rots.

## 6. Add a “Proof Required” field to every expert

Each expert has Lens, Owns, Stack docs, Canon, Learned patterns, Triggers, Out of scope.

Add one more field:

```md
**Proof required.**
- What evidence must the agent produce before claiming success?
```

Examples:

For Code Quality Engineer:

```md
**Proof required.**
- Quality report path.
- Coverage before/after.
- Complexity or CRAP-score before/after.
- Tests run.
- Threshold change, if any.
```

For Security Reviewer:

```md
**Proof required.**
- Alert or rule named.
- Sanitizer shape shown.
- CodeQL or relevant check result.
- Why the fix matches analyzer-recognized shape.
```

For Intelligence/Answering Engineer:

```md
**Proof required.**
- Stable source IDs cited.
- Trace file path or trace object.
- Provider boundary respected.
- Token/input budget described before provider call.
```

This turns each expert from a “role” into a **standard of evidence**.

## 7. Add a conflict protocol

The file says overlap means Out of Scope needs sharpening. Good. But it needs a procedure.

Add:

```md
## Conflict Protocol

If two experts appear valid:

1. Identify the primary artifact being changed.
2. Route to the expert who owns that artifact.
3. Name the adjacent expert as a boundary, not a co-owner.
4. If both artifacts must change, split into two prompts.
5. The first prompt may create a handoff note for the second prompt.

Never solve routing conflict by selecting multiple Section A experts.
```

This protects the whole system from “council soup.”

## 8. Add expert retirement / promotion rules

This matters if you keep expanding. Otherwise the roster becomes a graveyard of noble titles.

Add:

```md
## Expert Lifecycle

A new expert may be added only when:
- At least three real branches do not route cleanly to existing experts.
- The repeated ambiguity causes measurable friction.
- The proposed expert owns a stable artifact category.
- Its Out of Scope can name at least two neighbors.

An expert should be retired or merged when:
- It has zero use after 20 routed reports.
- Its reports consistently overlap another expert.
- Its owned artifacts no longer exist.
- It cannot produce unique proof requirements.
```

This is how the system stays alive instead of becoming decorative bureaucracy.

## 9. Add example routing cases

This file would become much more usable with 8–12 concrete examples.

Example:

```md
## Routing Examples

Task: "Add Claude export import."
Section A: Importer Engineer.
Section B: Senior Engineer.
Not Data and Storage Engineer unless schema changes are required.

Task: "The Ask answer cites sources but the trace browser does not show them."
Section A: Intelligence/Answering Engineer.
Section B: Senior Engineer.
Not Flask App Engineer unless the route/template is broken.

Task: "The import review page feels too crowded."
Section A: Flask App Engineer.
Section B: Lead Product Designer.
Not UX Strategist unless the multi-step import path itself is changing.

Task: "Write a Reddit post explaining SoulPrint."
Section A: Marketing Site Engineer only if it changes the site. Otherwise no Section A branch.
Section B: Community-Voice Writer.
```

Examples reduce hallucinated routing by giving the agent precedent.

## 10. Add “No Expert Needed” cases

Not every task deserves the doctrine. That should be explicit.

```md
## No Expert Needed

Do not invoke this routing doctrine for:
- Tiny typo fixes.
- One-line documentation corrections.
- Direct user questions that do not produce a repo artifact.
- Exploratory conversation before a branch exists.
- Personal planning outside the project repo.

If no artifact changes, do not force Section A routing.
```

This prevents the system from becoming heavy. A good doctrine knows when to stay silent.

## My recommended priority order

Do these first:

1. **Router Gate**
2. **Proof Required field**
3. **Verification Judge**
4. **Fill Importer Engineer**
5. **Docs/Canon Steward**
6. **Conflict Protocol**
7. **Release/Ops Engineer**
8. **Examples**
9. **Expert lifecycle rules**
10. **No Expert Needed cases**

The core diagnosis:

**The file already has identity. Now it needs enforcement.**

Right now it can guide a good agent.
After these additions, it can restrain a bad one.



-----------------------------------------------------------

With experts + template-h:




You were right to make me read them together. My earlier advice was too broad in one place: **Template H already carries a lot of the enforcement layer I thought was missing.** It already has authority order, context preflight, mandatory reads, verified facts, assumptions, stop conditions, tests, git instructions, session continuity, and generated-prompt review gates. So the missing layer is narrower now. 

The real gap is not “more structure.”
You already have structure.

The gap is:

**routing selection pressure before Template H is filled.**

`experts.md` says pick one Section A expert and one Section B stance, then read only their attached context. Template H repeats that reading order and tells the prompt to name the picks near the Mandatory Reads block. That is good. But neither file fully forces the drafter to justify *why* that expert/stance was chosen over its neighbors.  

## What I would still add

### 1. Add a short “Routing Justification” block

This belongs in **Template H**, right after the Expert and stance routing section or inside the skeleton near Mandatory Reads.

Not long. Just enough to prevent lazy routing.

```md
## ROUTING

Section A expert: <expert>.
Section B stance: <stance>.

Why this expert:
- The primary artifact changed is `<path/category>`, owned by <expert>.

Why not adjacent experts:
- Not <neighbor expert>, because <boundary>.
- Not <neighbor expert>, because <boundary>.

If this justification cannot be written cleanly, split the branch.
```

This is the missing pressure point.

Right now the agent can say:

> Section A expert: Flask App Engineer.

But it does not have to prove why it is **not** Data and Storage Engineer, Test Engineer, or Intelligence/Answering Engineer.

That proof matters.

### 2. Add “Proof required” to each expert

Template H already has **Tests and Verification**, but that is generic. Each expert needs its own evidence standard.

For example, Code Quality Engineer should not “prove” work the same way Brand Guardian or Data and Storage Engineer does.

Add this field to every Section A expert:

```md
**Proof required.**
- <expert-specific evidence before success can be claimed>
```

Examples:

```md
### Code Quality Engineer

**Proof required.**
- Targeted quality report path.
- Coverage before/after, if coverage changed.
- Complexity or CRAP-score before/after, if applicable.
- Targeted tests run.
- Full-suite result or explicit reason it was not run.
```

```md
### Data and Storage Engineer

**Proof required.**
- Schema behavior on fresh database.
- Schema behavior on existing database.
- Migration/idempotent guard evidence.
- FTS or query behavior tested, if touched.
- Canonical-versus-derived boundary preserved.
```

```md
### Security Reviewer

**Proof required.**
- The alert/rule named.
- The sink/source pattern identified.
- The fix shape matches CodeQL-recognized canonical form.
- Relevant security check or test result included.
```

This makes the Experts operational, not decorative.

### 3. Fill Importer Engineer

This one should not stay parked.

Because SoulPrint’s whole origin depends on ingestion: ChatGPT exports, Claude exports, markdown files, future provider formats, duplicate detection, source IDs, malformed inputs, skipped/imported counts.

Right now importer work spills across Data, Flask, and Test. The file itself admits this. That is a real architectural smell. 

I would add:

```md
### Importer Engineer

**Lens.** Provider-specific ingestion into the canonical ledger. Importers translate messy external exports into stable, inspectable SoulPrint records. The importer is a bridge, not the source of truth.

**Owns.** ChatGPT export importers, Claude export importers, markdown importers, future provider importers, source metadata mapping, duplicate detection policy, imported/skipped counts, source-conversation IDs, malformed export handling, and importer regression tests.

**Stack docs.**
- Python `json`: https://docs.python.org/3/library/json.html
- Python `pathlib`: https://docs.python.org/3/library/pathlib.html
- SQLite: https://www.sqlite.org/docs.html

**Project canon.**
- `DECISIONS.md`: canonical ledger rules and duplicate import policy.
- `.claude/rules/python-patterns.md`: storage two-lane pattern.
- `.claude/rules/soulprint-testing.md`: importer regression-test style.

**Triggers.**
- "Add Claude export import."
- "Import this new provider format."
- "Fix duplicate detection during import."
- "The importer skipped too much."
- "Map external conversation IDs into canonical records."
- "Handle malformed exports."

**Proof required.**
- Good import fixture.
- Malformed import fixture, if relevant.
- Duplicate import behavior proven.
- Imported/skipped counts verified.
- Stable source/source_conversation_id behavior proven.

**Out of scope.**
- Schema changes required by importers: Data and Storage Engineer.
- Upload/review UI: Flask App Engineer.
- Test harness mechanics: Test Engineer.
- Intelligence over imported data: Intelligence/Answering Engineer.
```

This is the cleanest missing expert.

### 4. Add Docs/Canon Steward, but keep it dangerous and narrow

I still think this is needed, but not as a “documentation writer.” That would become mush.

It should exist only for **doctrine integrity**: contradictions between `CLAUDE.md`, `DECISIONS.md`, `template-h.md`, `experts.md`, `ops/learned/`, and `ops/experts/`.

```md
### Docs/Canon Steward

**Lens.** Project memory must remain coherent. Canon files, decisions, learned patterns, expert reports, and templates must not drift into contradiction, duplication, or stale instruction.

**Owns.** `CLAUDE.md`, `DECISIONS.md`, `template-h.md`, `context/experts.md`, `ops/learned/`, `ops/experts/`, terminology audits, doctrine portability checks, deprecated-rule removal, and cross-file consistency.

**Triggers.**
- "These docs contradict each other."
- "Promote this report observation into learned patterns."
- "Audit Template H against Experts."
- "Prepare this routing system for another project."
- "Remove stale canon."
- "The doctrine changed after this branch."

**Proof required.**
- Contradiction named.
- Source files named.
- Replacement rule stated.
- Deprecated language removed or explicitly retained.
- No implementation scope smuggled in.

**Out of scope.**
- Feature implementation.
- Marketing copy.
- Product strategy.
- Test/security/schema ownership.
```

This expert matters because your system is now becoming portable doctrine. Without canon maintenance, it will eventually become a haunted filing cabinet.

### 5. Add routing examples

This is the highest-value low-cost improvement.

Both files are well-written, but still abstract. Add 10 examples to `experts.md`.

Example format:

```md
## Routing Examples

Task: "Add Claude export import."
Section A: Importer Engineer.
Section B: Senior Engineer.
Not Data and Storage Engineer unless schema changes are required.

Task: "The Ask answer cites sources but the trace browser does not show them."
Section A: Intelligence/Answering Engineer.
Section B: Senior Engineer.
Not Flask App Engineer unless the route/template rendering is broken.

Task: "The import review page feels crowded."
Section A: Flask App Engineer.
Section B: Lead Product Designer.
Not UX Strategist unless the multi-step import journey changes.

Task: "Write a Reddit post introducing SoulPrint."
Section A: none, unless a repo artifact is being changed.
Section B: Community-Voice Writer.

Task: "Fresh clone fails because setup docs are stale."
Section A: Docs/Canon Steward or Release/Ops Engineer, if added.
Section B: Senior Engineer.
```

This gives future agents precedent. Precedent beats vibes.

### 6. Maybe add Release/Ops Engineer, but only after pain appears

I would **not** add Release/Ops Engineer yet unless you already have recurring setup, packaging, CI/local mismatch, environment, or deployment problems.

Template H already handles branch, git, tests, and continuity. Test Engineer owns CI reliability. Marketing Site Engineer owns `site/` deploy. So Release/Ops may be premature.

Keep it as a parked candidate:

```md
### Release/Ops Engineer *(candidate, do not add until repeated setup/release pain appears)*
```

Add it only after 2–3 real reports show the same friction.

### 7. Do not add Verification Judge as a separate expert

I retract that part from the previous answer.

Template H already has:

* stop conditions;
* tests and verification;
* git instructions;
* session continuity;
* review protocol for generated prompts;
* expert reports. 

A separate “Verification Judge” expert would duplicate Template H and make the system heavier. Better move verification into:

* `Proof required` per expert;
* Routing Justification;
* Template H review protocol.

Cleaner. Less council fog.

## What is still missing at the system level

The system has three layers now:

**Experts.md** = who/what lens.
**Template H** = how to turn intent into one branch.
**Reports** = empirical feedback loop.

The missing fourth layer is:

**Routing history analysis.**

You already write `ops/experts/report-NN.md`. But after 20–30 reports, someone needs to audit them.

Add this to `experts.md`:

```md
## Expert Report Audit

Every 20 expert reports, run a routing audit.

Review:

1. Which experts were used most?
2. Which experts were never used?
3. Which expert pairings produced clean branches?
4. Which pairings caused scope creep?
5. Which Mandatory Reads were repeatedly useful?
6. Which listed canon links were never read?
7. Which experts need sharper Out of Scope boundaries?
8. Which learned patterns should be promoted into canon?
9. Which expert should be retired, merged, or split?

Output: `ops/experts/audit-NN.md`.
```

This is where the doctrine becomes self-correcting.

Without audits, reports accumulate like bones in a crypt.

With audits, the system learns.

## Final practical verdict

Do **not** bloat Template H. It is already heavy enough and mostly well-formed.

Add only this to Template H:

```md
## ROUTING

Section A expert: <expert>.
Section B stance: <stance>.

Why this expert:
- ...

Why not adjacent experts:
- ...
```

Then improve `experts.md` with:

1. **Proof required** field for every expert.
2. **Filled Importer Engineer.**
3. **Docs/Canon Steward.**
4. **Routing examples.**
5. **Expert report audit every 20 reports.**
6. Optional parked **Release/Ops Engineer**, but not active yet.

That is the clean upgrade.

The doctrine is no longer missing a skeleton.
It is missing ligaments: the small connective rules that stop power from leaking between bones.
