# Session: UI Visual Directions

## Goal
Create three premium visual directions for SoulPrint before implementation without implying a frontend rewrite or changing backend truth.

## What changed
- Added the canonical static exploration pack at `docs/design/soulprint-visual-directions/`
- Kept the artifact HTML and CSS only so it can translate cleanly into Flask templates later
- Included paired landing hero and search-home mockups for Quiet Archive, Soft Intelligence, and Modern Study
- Split the prototype into shared tokens, shared styles, and a small preview script for easier Flask-portable reuse

## Constraints honored
- warm-light default
- search as the default home and center of gravity
- provider identity visible for ChatGPT, Claude, Gemini, and Grok
- SoulPrint brand accent separate from provider colors
- no dashboard-first composition
- no schema, importer, retrieval, or backend changes

## Recommendation
- rank Quiet Archive first
- use Soft Intelligence warmth selectively
- borrow Modern Study rigor where search needs stronger editorial structure

## Next step
- choose one direction and translate it into the live Flask templates incrementally, starting with the search home rather than a broad surface rewrite
