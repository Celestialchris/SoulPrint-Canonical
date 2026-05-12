<script lang="ts">
  import { page } from '$app/stores';
  import Sigil from '$lib/components/Sigil.svelte';
  import Dock from '$lib/components/Dock.svelte';
  import {
    mockNotes,
    mockChunks,
    mockLoadedNote,
    laneColor,
    relativeTime,
    noteTitle
  } from '$lib/mock';

  type PageState = 'empty' | 'loaded' | 'listening';

  function getState(p: typeof $page): PageState {
    const s = p.url.searchParams.get('state');
    if (s === 'loaded' || s === 'listening') return s;
    return 'empty';
  }

  // Map page state to dock state
  function dockState(s: PageState): 'idle' | 'ready' | 'playing' {
    if (s === 'loaded') return 'ready';
    if (s === 'listening') return 'playing';
    return 'idle';
  }
</script>

<div class="reader-page">
  <main class="reader-content">

    <!-- ═══════════════════ EMPTY STATE ═══════════════════ -->
    {#if getState($page) === 'empty'}
      <div class="content-empty">

        <div class="sigil-container">
          <div class="sigil-entrance">
            <Sigil size={64} />
          </div>
        </div>

        <h1 class="display-heading" style="text-align: center;">
          Paste something, or pick a note.
        </h1>
        <p class="subtitle" style="text-align: center;">
          Select a note from your archive, paste text, or upload a file. Pick a voice and listen.
        </p>

        <textarea
          class="paste-area"
          placeholder="Paste text here to read aloud…"
          rows="5"
        ></textarea>

        <!-- Decorative HR -->
        <div class="decorative-rule">
          <div class="rule-line"></div>
          <div class="rule-sigil">
            <Sigil size={16} />
          </div>
          <div class="rule-line"></div>
        </div>

        <!-- Note list -->
        <ul class="note-list" aria-label="Recent notes">
          {#each mockNotes as note (note.id)}
            <li class="note-row">
              <div class="note-lane-mark" style="background: {laneColor(note.provider)};"></div>
              <div class="note-body">
                <p class="note-title">{noteTitle(note.content)}</p>
                <p class="note-meta">{relativeTime(note.timestamp)}</p>
              </div>
            </li>
          {/each}
        </ul>

      </div>

    <!-- ═══════════════════ LOADED STATE ═══════════════════ -->
    {:else if getState($page) === 'loaded'}
      <div class="content-loaded">

        <p class="eyebrow">From Note</p>
        <h1 class="display-heading">{mockLoadedNote.title}</h1>

        <div class="header-meta">
          <span class="subtitle">
            {mockLoadedNote.chunkCount} sections · ~{mockLoadedNote.estimatedMinutes} min
          </span>
          <div class="header-chips">
            <span class="chip">{mockLoadedNote.voice}</span>
            <span class="chip">1.0×</span>
          </div>
        </div>

        <!-- Decorative HR -->
        <div class="decorative-rule">
          <div class="rule-line"></div>
          <div class="rule-sigil">
            <Sigil size={16} />
          </div>
          <div class="rule-line"></div>
        </div>

        <!-- Chunk list — all ready in loaded state -->
        <ul class="chunk-list" aria-label="Reading sections">
          {#each mockChunks as chunk (chunk.chunk_id)}
            <li data-state="ready">
              <div class="chunk-row">
                <div class="chunk-gutter">
                  <div class="chunk-number">{chunk.index}</div>
                </div>
                <p class="chunk-text">{chunk.text}</p>
              </div>
            </li>
          {/each}
        </ul>

        <button class="cta-read-aloud" type="button">Read aloud</button>

      </div>

    <!-- ═══════════════════ LISTENING STATE ═══════════════════ -->
    {:else}
      <div class="content-loaded">

        <p class="eyebrow">Listening</p>
        <h1 class="display-heading">{mockLoadedNote.title}</h1>

        <div class="header-meta">
          <span class="subtitle">
            Section 3 of 6 · nagato_ref · 1.0×
          </span>
          <div class="header-chips">
            <span class="chip">nagato_ref</span>
            <span class="chip">1.0×</span>
          </div>
        </div>

        <!-- Decorative HR -->
        <div class="decorative-rule">
          <div class="rule-line"></div>
          <div class="rule-sigil">
            <Sigil size={16} />
          </div>
          <div class="rule-line"></div>
        </div>

        <!-- Chunk list — varied states in listening mode -->
        <ul class="chunk-list" aria-label="Reading sections">
          {#each mockChunks as chunk (chunk.chunk_id)}
            <li data-state={chunk.status}>
              <div class="chunk-row">
                <div class="chunk-gutter">
                  <div class="chunk-number">{chunk.index}</div>
                </div>
                <p class="chunk-text">{chunk.text}</p>
              </div>
            </li>

            <!-- Generating notice appears after the generating chunk -->
            {#if chunk.status === 'generating'}
              <li aria-live="polite">
                <p class="generating-notice">
                  Section {chunk.index} is generating. Playback continues automatically.
                </p>
              </li>
            {/if}
          {/each}
        </ul>

      </div>
    {/if}

  </main>

  <div class="reader-dock">
    {#if getState($page) === 'empty'}
      <Dock state="idle" />
    {:else if getState($page) === 'loaded'}
      <Dock
        state="ready"
        progress={0}
        current={0}
        total={mockLoadedNote.chunkCount}
        voice={mockLoadedNote.voice}
        speed={1.0}
      />
    {:else}
      <Dock
        state="playing"
        progress={42}
        current={3}
        total={6}
        voice="nagato_ref"
        speed={1.0}
        previewText="The architecture was correct..."
        previewMeta="section 3 · paragraph"
      />
    {/if}
  </div>
</div>
