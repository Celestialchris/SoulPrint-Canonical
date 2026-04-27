Best path:

docs/specs/frontend-evolution-doctrine.md

Reason: this is not a feature spec yet. It is an architectural north-star. The uploaded note clearly says the path is gradual: keep Flask/Jinja2 now, add clean JSON endpoints later, build SvelteKit on top, then eventually wrap with Tauri while Python remains the local engine and SQLite remains canonical.

Use this as the file:

# Frontend Evolution Doctrine

Status: doctrine draft  
Target path: `docs/specs/frontend-evolution-doctrine.md`  
Scope: architecture and product direction only. No implementation in this document.

## Purpose

SoulPrint currently uses a deliberately simple local-first stack:

```text
Python
Flask
SQLAlchemy
SQLite
Jinja2
HTML/CSS
Markdown docs

That stack is not a mistake. It is the correct foundation for the current product stage because SoulPrint is first a canonical memory ledger, not a frontend experiment.

The purpose of this doctrine is to preserve the long-term interface direction without triggering a premature rewrite.

SoulPrint should eventually gain a richer interactive interface, but the canonical ledger must remain protected. The frontend may become more expressive. It must never become the source of truth.

Core thesis

Jinja2 is good for ledger software.

Jinja2 becomes limiting when SoulPrint wants to feel like a living memory cockpit.

The current stack should be treated as the monastery manuscript layer: stable, readable, local, and difficult to corrupt. The future interface should become the glass cockpit: fluid, interactive, precise, and beautiful.

SQLite remains the altar.

Non-negotiable boundary

The frontend must never become canonical memory.

The source of truth remains:

SQLite ledger
filesystem custody
stable IDs
provenance metadata
export manifests
raw transcripts

The frontend may:

view
search
filter
inspect
annotate through controlled endpoints
trigger exports
trigger imports
trigger local actions

The frontend must not:

own canonical state independently
rewrite provenance
silently mutate transcripts
invent attachment relationships
store primary memory outside the ledger
replace export manifests
bypass backend validation

The blade must not rewrite the scripture.

Current-stage doctrine

For the current stage, keep:

Flask
Jinja2
disciplined CSS
SQLite
SQLAlchemy
server-rendered reliability

This remains best for:

export pages
settings pages
simple forms
server-rendered transcript views
documentation-like views
low-JavaScript fallback pages
admin-style screens
license and local runtime pages

Jinja2 should not be blamed for problems caused by loose template structure, stale copy, weak interaction design, or insufficient API boundaries.

The current UI can still be improved substantially without introducing a frontend framework.

Future-stage doctrine

When SoulPrint needs richer interaction, the preferred frontend direction is:

SvelteKit + TypeScript

Preferred desktop shell:

Tauri

Preferred backend posture:

Flask now.
FastAPI only later if API boundaries become central enough to justify migration.

Preferred styling posture:

strict design tokens
disciplined CSS
no random Tailwind soup

Preferred search posture:

SQLite FTS5 now.
Tantivy/Rust only later if archive size and search requirements justify it.
Why SvelteKit over React

React is powerful, but it often introduces ceremony: hooks, state libraries, component architecture debates, build tooling decisions, styling systems, and framework gravity.

SoulPrint does not need corporate frontend architecture. It needs a beautiful local cockpit for memory.

SvelteKit is preferred because it is direct:

write the interface
bind the state
ship the thing

This fits SoulPrint’s local-first temperament better than a heavy client architecture.

Evolution path

This doctrine rejects a rewrite-first approach.

The clean path is gradual.

Phase 1: Keep Flask and Jinja2

Goal:

finish product coherence
keep current UI stable
improve page structure
keep exports and forms reliable

What stays:

Jinja2 templates
Flask routes
server-rendered pages
current Python engine
SQLite canonical ledger

What improves:

copy truth
template discipline
CSS token discipline
page coherence
export clarity
search result usability
attachment UX within current constraints
Phase 2: Add clean JSON endpoints

Goal:

make the ledger safely accessible through explicit backend boundaries

This phase does not introduce Svelte yet.

It prepares the ground.

Potential endpoint families:

/api/conversations
/api/conversations/<id>
/api/conversations/<id>/messages
/api/conversations/<id>/attachments
/api/search
/api/federated
/api/continuity/<id>
/api/export
/api/archive/health

Rules:

API responses must preserve stable IDs.
API responses must preserve provenance.
API responses must not expose absolute local paths unless explicitly intended.
API writes must go through existing backend validation.
API shape must be documented before a Svelte client depends on it.
Phase 3: Build the SvelteKit cockpit

Goal:

create a fluid interface over the existing canonical ledger

SvelteKit should first target the surfaces that benefit most from interactivity:

live search
transcript explorer
attachment viewer
drag-and-drop upload
provider filters
timeline navigation
minimap
resizable panes
keyboard shortcuts
provenance inspector
answer evidence panel
continuity/open-loop dashboard

Jinja2 remains available for:

fallback pages
exports
settings
low-JavaScript surfaces
simple admin-like views

This is not a deletion of Flask/Jinja2. It is a layered interface upgrade.

Phase 4: Wrap with Tauri

Goal:

make SoulPrint feel like a native local memory instrument

Final local app shape:

Python engine
SQLite ledger
filesystem custody
SvelteKit interface
Tauri desktop shell

Python remains the local engine.

SQLite remains canonical memory.

Svelte becomes the glass cockpit.

Tauri becomes the vessel.

Where Jinja2 should continue to win

Jinja2 remains appropriate for:

markdown export views
import confirmation pages
settings pages
license status pages
archive health pages
simple forms
plain transcript rendering
low-JavaScript fallback views
documentation-like internal pages

These surfaces benefit from predictability more than fluidity.

Where SvelteKit should eventually win

SvelteKit is the better tool for:

live search
message-level filtering
provider switching
drag-and-drop attachments
attachment preview panels
timeline navigation
minimap interaction
resizable transcript panes
keyboard shortcuts
smooth transitions
local desktop polish
multi-pane provenance inspection
answer evidence exploration
project/workspace navigation

These surfaces benefit from persistent client state and fast interaction.

API boundary rules

Before any frontend migration, SoulPrint needs clean API contracts.

Every API endpoint must answer:

What canonical object does this expose?
What stable ID does it return?
What provenance does it preserve?
What derived data does it include?
What writes are allowed?
What validation protects the ledger?
What export or manifest contract depends on it?

No Svelte component should be allowed to infer canonical rules that belong in Python.

Design system rules

The future frontend must inherit SoulPrint’s design doctrine, not replace it with framework defaults.

Rules:

preserve Quiet Archive visual direction unless explicitly superseded
use strict design tokens
prefer calm archival surfaces over dashboard noise
make provenance visible
make local custody visible
avoid decorative complexity
avoid generic SaaS aesthetics

The product should feel like a memory instrument, not a metrics toy.

Migration triggers

Do not introduce SvelteKit merely because it is nicer.

Valid triggers:

Jinja2 blocks a specific interaction that matters to the product.
The transcript explorer needs persistent client-side state.
Search needs live filtering, keyboard traversal, and result inspection.
Attachments need drag/drop, preview, placement, and message-level context.
Answer audit needs expandable evidence navigation.
The desktop shell becomes a real distribution target.

Invalid triggers:

frontend boredom
visual novelty
framework fashion
premature rewrite instinct
desire to look modern without a product reason
Non-goals

This doctrine does not authorize:

rewriting the current app in Svelte
replacing Flask immediately
moving canonical state into browser storage
adding a vector database
activating mem0 as canonical memory
introducing cloud sync
rewriting the design system
adding frontend dependencies to the current branch
shipping a Tauri shell before the local web app is coherent
Implementation posture

When this doctrine becomes actionable, work should happen in small branches.

Recommended future branch sequence:

docs/frontend-evolution-doctrine
api/conversation-read-endpoints
api/search-read-endpoints
api/attachment-read-endpoints
prototype/svelte-transcript-explorer
prototype/svelte-search-panel
desktop/tauri-spike

Each branch should be reversible.

No branch should mix doctrine, API extraction, frontend framework setup, and desktop packaging.

Acceptance criteria for first API phase

The first real implementation phase succeeds when:

existing Jinja2 UI still works
existing tests still pass
API endpoints expose read-only canonical data
stable IDs are present in every response
provenance survives every response
no frontend framework is introduced yet
no runtime behavior changes outside the API surface
Acceptance criteria for first Svelte prototype

The first Svelte prototype succeeds when:

it consumes existing API endpoints
it does not mutate canonical state directly
it improves one specific surface
it can be removed without damaging the Flask app
it demonstrates real UX value over Jinja2

The first candidate surface should be one of:

transcript explorer
live search
attachment viewer
answer evidence inspector
Final architecture target

The long-term target is:

Core truth:
Python + SQLite + SQLAlchemy

Backend/API:
Flask now
FastAPI later only if needed

Frontend:
SvelteKit + TypeScript

Desktop:
Tauri

Styling:
strict design tokens

Search:
SQLite FTS5 now
Tantivy/Rust only if justified by scale

Exports:
Markdown + JSON + manifests

This gives SoulPrint a beautiful interface without sacrificing the ledger.