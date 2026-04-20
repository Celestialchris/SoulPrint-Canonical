# User — Chris

## Background

Philosophy and psychology background, no formal CS training. Comfortable with abstraction, systems thinking, and cross-domain reasoning. Bilingual Romanian/English. Romanian is fine for casual exchanges; stay in English for code, prompts, commits, and anything that might get pasted elsewhere.

## How I Work

I direct AI coding agents (Claude Code, Cursor) rather than writing code directly. My bottleneck is translating strong product intuitions into specs precise enough for agents to execute on. I think in product and UX terms, not implementation terms.

When I ask "why," I usually want the architectural reasoning, not a code walkthrough. When I ask "how," I want the specific steps or the specific file.

## Preferences

- Small reversible changes over big clever ones. Always.
- Check before proposing. Before suggesting work, check whether it already shipped. When uncertain, ask. Do not re-propose completed tasks.
- Flag uncertainty explicitly. "I think X, but I haven't verified Y" beats confident guesses. Name the specific part you're uncertain about.
- Show tradeoffs. Before recommending an approach, state 1-2 alternatives you considered and why you dismissed them.
- No em dashes in public copy (README, landing page, Reddit posts). They're an AI tell.
- No "lessons learned" lists or numbered takeaways unless I explicitly ask.
- Length follows the problem. 3 sentences if that's right. 5 paragraphs if needed. Never pad.

## Prompts for Claude Code

When I ask you to write a prompt destined for Claude Code, use Template H structure:
1. Mandatory read block at the top (explicit file list + "do NOT explore the codebase")
2. Objective
3. Starting state
4. Target state
5. Step-by-step tasks
6. Scope lock with DO NOT EDIT list
7. Stop conditions
8. Git instructions

Before writing the prompt, flag any assumption you're making about the codebase that might be wrong. See `prompts/` for working examples (cp2, 3b).

## Content for Communities

For content aimed at a specific community (Reddit, Hacker News, etc.), research the community's current tone before writing. If you can't research first, say so and offer to research before writing. Don't guess tonal calibration.

## Environment

- Windows 11, WSL (Kali Linux)
- RTX 4070 Ti Super (16 GB VRAM), ~32 GB system RAM
- Python 3.12, SQLite, local-first stack
- Ollama for local LLM inference (Gemma 4 default)
- Claude Code for agentic development
