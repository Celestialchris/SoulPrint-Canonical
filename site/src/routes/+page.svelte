<svelte:head>
	<title>SoulPrint: Your AI conversations, home.</title>
	<meta
		name="description"
		content="SoulPrint is a local-first memory archive for AI conversations from ChatGPT, Claude, Claude Code, Gemini, and Grok. Browse, search, continue, and export with provenance intact."
	/>
</svelte:head>

<main>
	<header>
		<h1>SoulPrint: Your AI conversations, home.</h1>
		<p class="lede">
			A local-first memory archive for AI conversations. Imports run into a private SQLite
			ledger on your machine.
		</p>
	</header>

	<section>
		<h2>Supported providers</h2>
		<ul class="providers">
			<li>ChatGPT</li>
			<li>Claude</li>
			<li>Claude Code</li>
			<li>Gemini</li>
			<li>Grok</li>
		</ul>
	</section>

	<section>
		<h2>What it does</h2>
		<ul>
			<li>Browse imported conversations transcript by transcript.</li>
			<li>Search across every provider in one place.</li>
			<li>Continue old threads with paste-ready context.</li>
			<li>Export with provenance intact, including a verifiable Memory Passport.</li>
		</ul>
	</section>

	<section>
		<h2>Trust posture</h2>
		<p>
			Core archive features stay local: import, browse, search, notes, exports, and the
			passport run with no network.
		</p>
		<p>
			Optional intelligence features only contact the LLM provider you have configured, and
			only when you trigger them.
		</p>
	</section>

	<section class="ctas">
		<a class="cta-primary" href="https://github.com/Celestialchris/SoulPrint-Canonical#install"
			>Install from source</a
		>
		<a class="cta-secondary" href="https://github.com/Celestialchris/SoulPrint-Canonical"
			>View on GitHub</a
		>
	</section>

	<footer>
		<p>Apache-2.0. Open source. No accounts, no analytics, no telemetry, no background sync.</p>
	</footer>
</main>

<style>
	:global(html) {
		font-family:
			ui-sans-serif,
			system-ui,
			-apple-system,
			BlinkMacSystemFont,
			'Segoe UI',
			Roboto,
			'Helvetica Neue',
			Arial,
			sans-serif;
		color: #1a1a1a;
		background: #fafaf7;
	}

	:global(body) {
		margin: 0;
	}

	main {
		max-width: 640px;
		margin: 0 auto;
		padding: 4rem 1.5rem 6rem;
		line-height: 1.6;
	}

	h1 {
		font-size: 1.75rem;
		font-weight: 600;
		line-height: 1.25;
		margin: 0 0 0.75rem;
	}

	h2 {
		font-size: 1rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin: 2.25rem 0 0.75rem;
	}

	header .lede {
		font-size: 1.05rem;
		color: #444;
		margin: 0;
	}

	section {
		margin-top: 1.5rem;
	}

	section p {
		margin: 0 0 0.75rem;
	}

	ul {
		margin: 0;
		padding-left: 1.25rem;
	}

	ul.providers {
		list-style: none;
		padding-left: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1rem;
	}

	ul.providers li {
		font-variant-numeric: tabular-nums;
	}

	.ctas {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		margin-top: 2.5rem;
	}

	.cta-primary,
	.cta-secondary {
		display: inline-block;
		padding: 0.6rem 1.1rem;
		text-decoration: none;
		font-size: 0.95rem;
		border: 1px solid #1a1a1a;
		border-radius: 4px;
	}

	.cta-primary {
		background: #1a1a1a;
		color: #fafaf7;
	}

	.cta-secondary {
		background: transparent;
		color: #1a1a1a;
	}

	.cta-primary:hover,
	.cta-secondary:hover {
		opacity: 0.85;
	}

	footer {
		margin-top: 4rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e5e5e0;
		font-size: 0.85rem;
		color: #666;
	}
</style>
