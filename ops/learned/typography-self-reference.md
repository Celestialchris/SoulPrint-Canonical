# Typography Self-Reference

## Pattern: typography rules can trap their own documentation

**From:** April 27, 2026, Branch 1 docs cleanup (`docs/public-docs-truth-cleanup`, commit `b6cf619`).

**Pattern**

When a docs branch enforces a rule against a specific glyph, do not
reproduce that glyph in the session log, the commit message, the
prompt, or the learned-pattern file itself. Describe it semantically.

The rule SoulPrint enforces: no long horizontal dash glyph, Unicode
U+2014, anywhere in public-facing copy. Branch 1 removed several
instances. The session log needed to describe the removal. Quoting the
literal character would have recreated the problem. The safe wording
is semantic: "the long-dash separator was converted to a colon."

**Why**

A learned-pattern file or session log that quotes the literal glyph
silently reintroduces the artifact it claims to remove. A future audit
grep across the repo for the forbidden glyph will hit the very file
that documents the rule.

**Where**

- Public-copy sweeps that target a specific glyph, smart quotes,
  ellipsis characters, or trademark symbols.
- Session logs and `ops/learned/` files for docs cleanup branches
  involving typography.
- README, landing page, manifesto, or any document where tone is part
  of the deliverable.

**Practical form**

Three substitutions that work without typing the forbidden glyph:

1. Name the change semantically: "the long-dash separator was converted
   to a colon"; "smart quotes were replaced with straight quotes."
2. Reference by Unicode code point if precision is needed: "U+2014 was
   removed from the four files."
3. Quote the surrounding text without the glyph: write "between word
   and word" instead of pasting the line that contained the dash.

**Verification**

After any docs cleanup branch involving a glyph rule, run a literal
grep for the glyph across all files touched in the branch, including
the new session log and any new `ops/learned/` files. The grep should
return zero matches.
