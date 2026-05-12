<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import Sigil from '$lib/components/Sigil.svelte';
  import Dock from '$lib/components/Dock.svelte';
  import { createReaderState, type PageState } from '$lib/stores.svelte';
  import type { Note } from '$lib/api';

  const reader = createReaderState();

  let audioEl = $state<HTMLAudioElement | null>(null);
  let pasteText = $state('');

  onMount(() => {
    void reader.loadInitial();
  });

  onDestroy(() => {
    reader.cleanup();
  });

  // Hand the live <audio> element to the store once mounted.
  $effect(() => {
    reader.registerAudio(audioEl);
  });

  function dockState(s: PageState): 'idle' | 'ready' | 'playing' {
    if (s === 'loaded') return 'ready';
    if (s === 'listening') return 'playing';
    return 'idle';
  }

  function noteTitle(content: string): string {
    return content.split('\n')[0].slice(0, 80);
  }

  function laneColor(provider: string | null): string {
    const map: Record<string, string> = {
      chatgpt: 'var(--lane-chatgpt)',
      claude: 'var(--lane-claude)',
      claude_code: 'var(--lane-claude)',
      gemini: 'var(--lane-gemini)',
      grok: 'var(--lane-grok)'
    };
    return map[provider ?? ''] ?? 'rgba(24,22,20,0.18)';
  }

  function relativeTime(iso: string | null): string {
    if (!iso) return '';
    const diff = Date.now() - new Date(iso).getTime();
    if (Number.isNaN(diff)) return '';
    const days = Math.floor(diff / 86400000);
    if (days <= 0) return 'today';
    if (days === 1) return 'yesterday';
    if (days < 30) return `${days}d ago`;
    const months = Math.floor(days / 30);
    return `${months}mo ago`;
  }

  function voiceLabel(filename: string): string {
    return filename.replace(/\.wav$/i, '');
  }

  function chunkDataState(index: number, status: string): string {
    if (status === 'generating' || status === 'pending') return status;
    // status === 'ready'
    if (index === reader.currentChunkIndex) return 'active';
    return 'ready';
  }

  function handleAudioEnded(): void {
    reader.onChunkEnded();
  }

  function handleAudioTimeUpdate(): void {
    if (!audioEl) return;
    reader.updateAudioTime(audioEl.currentTime, audioEl.duration);
  }

  function selectNote(note: Note): void {
    reader.selectNote(note);
  }

  function startReading(): void {
    void reader.startReading();
  }

  function tryAgain(): void {
    reader.resetJob();
  }

  function pickFromPaste(): void {
    const trimmed = pasteText.trim();
    if (!trimmed) return;
    // Synthesize a transient note so the existing flow handles paste-to-read.
    const synthetic: Note = {
      id: -1,
      content: trimmed,
      tags: [],
      is_starred: false,
      timestamp: new Date().toISOString(),
      role: null,
      provider: null
    };
    reader.selectNote(synthetic);
  }

  // Derived UI helpers
  const dockProgress = $derived(
    reader.audioDuration > 0
      ? Math.min(100, (reader.audioCurrentTime / reader.audioDuration) * 100)
      : reader.chunks.length > 0
        ? (reader.currentChunkIndex / reader.chunks.length) * 100
        : 0
  );
  const totalChunks = $derived(reader.chunks.length || reader.job?.total_chunks || 0);
  const previewTitle = $derived(
    reader.selectedNote ? noteTitle(reader.selectedNote.content) : ''
  );
  const previewMeta = $derived(
    totalChunks > 0
      ? `section ${reader.currentChunkIndex + 1} of ${totalChunks}`
      : ''
  );

  const hasFatalError = $derived(reader.notesError !== null || reader.voicesError !== null);
</script>

<div class="reader-page">
  <main class="reader-content">

    {#if reader.isLoadingNotes || reader.isLoadingVoices}
      <div class="content-empty">
        <div class="sigil-container">
          <div class="sigil-entrance">
            <Sigil size={80} />
          </div>
        </div>
        <h1 class="display-heading" style="text-align: center;">Connecting…</h1>
        <p class="subtitle" style="text-align: center;">
          Loading notes and voices from your local services.
        </p>
      </div>

    {:else if hasFatalError}
      <div class="content-empty">
        <div class="sigil-container">
          <div class="sigil-entrance">
            <Sigil size={80} />
          </div>
        </div>
        <h1 class="display-heading" style="text-align: center;">Service not reachable</h1>
        {#if reader.notesError}
          <p class="subtitle" style="text-align: center;">
            SoulPrint is not running (expected at localhost:5000)
          </p>
        {/if}
        {#if reader.voicesError}
          <p class="subtitle" style="text-align: center;">
            VoiceForge is not running (expected at localhost:5001)
          </p>
        {/if}
      </div>

    <!-- ═══════════════════ EMPTY STATE ═══════════════════ -->
    {:else if reader.pageState === 'empty'}
      <div class="content-empty">

        <div class="sigil-container">
          <div class="sigil-entrance">
            <Sigil size={80} />
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
          bind:value={pasteText}
          onblur={pickFromPaste}
        ></textarea>

        {#if reader.voices.length > 0}
          <label class="voice-select-label">
            <span class="eyebrow">Voice</span>
            <select
              class="voice-select"
              value={reader.selectedVoice}
              onchange={(e) => reader.setVoice((e.currentTarget as HTMLSelectElement).value)}
            >
              {#each reader.voices as v (v.filename)}
                <option value={v.filename}>{v.name}</option>
              {/each}
            </select>
          </label>
        {/if}

        <div class="decorative-rule">
          <div class="rule-line"></div>
          <div class="rule-sigil">
            <Sigil size={18} />
          </div>
          <div class="rule-line"></div>
        </div>

        <ul class="note-list" aria-label="Recent notes">
          {#each reader.notes as note (note.id)}
            <li class="note-row">
              <button
                type="button"
                class="note-row-button"
                onclick={() => selectNote(note)}
              >
                <div class="note-lane-mark" style="background: {laneColor(note.provider)};"></div>
                <div class="note-body">
                  <p class="note-title">{noteTitle(note.content)}</p>
                  <p class="note-meta">{relativeTime(note.timestamp)}</p>
                </div>
              </button>
            </li>
          {/each}
        </ul>

      </div>

    <!-- ═══════════════════ LOADED STATE ═══════════════════ -->
    {:else if reader.pageState === 'loaded' && reader.selectedNote}
      <div class="content-loaded">

        <p class="eyebrow">From Note</p>
        <h1 class="display-heading">{noteTitle(reader.selectedNote.content)}</h1>

        <div class="header-meta">
          <span class="subtitle">
            ~{Math.max(1, Math.round(reader.selectedNote.content.length / 900))} min
          </span>
          <div class="header-chips">
            <span class="chip">{voiceLabel(reader.selectedVoice)}</span>
            <span class="chip">{reader.speed.toFixed(1)}×</span>
          </div>
        </div>

        <div class="decorative-rule">
          <div class="rule-line"></div>
          <div class="rule-sigil">
            <Sigil size={18} />
          </div>
          <div class="rule-line"></div>
        </div>

        <article class="note-preview">
          <p class="chunk-text">{reader.selectedNote.content}</p>
        </article>

        <button class="cta-read-aloud" type="button" onclick={startReading}>
          Read aloud
        </button>

      </div>

    <!-- ═══════════════════ LISTENING STATE ═══════════════════ -->
    {:else if reader.pageState === 'listening' && reader.selectedNote}
      <div class="content-loaded">

        <p class="eyebrow">Listening</p>
        <h1 class="display-heading">{noteTitle(reader.selectedNote.content)}</h1>

        <div class="header-meta">
          <span class="subtitle">
            Section {Math.min(reader.currentChunkIndex + 1, totalChunks)} of {totalChunks}
            · {voiceLabel(reader.selectedVoice)}
            · {reader.speed.toFixed(1)}×
          </span>
          <div class="header-chips">
            <span class="chip">{voiceLabel(reader.selectedVoice)}</span>
            <span class="chip">{reader.speed.toFixed(1)}×</span>
          </div>
        </div>

        <div class="decorative-rule">
          <div class="rule-line"></div>
          <div class="rule-sigil">
            <Sigil size={18} />
          </div>
          <div class="rule-line"></div>
        </div>

        {#if reader.generationError}
          <div class="generation-error" role="alert">
            <p class="subtitle">{reader.generationError}</p>
            <button class="cta-read-aloud" type="button" onclick={tryAgain}>Try again</button>
          </div>
        {:else}
          <ul class="chunk-list" aria-label="Reading sections">
            {#each reader.chunks as chunk, i (chunk.chunk_id)}
              <li data-state={chunkDataState(i, chunk.status)}>
                <div class="chunk-row">
                  <div class="chunk-gutter">
                    <div class="chunk-number">{i + 1}</div>
                  </div>
                  <p class="chunk-text">
                    Section {i + 1}
                  </p>
                </div>
              </li>

              {#if chunk.status === 'generating'}
                <li aria-live="polite">
                  <p class="generating-notice">
                    Section {i + 1} is generating. Playback continues automatically.
                  </p>
                </li>
              {/if}
            {/each}
          </ul>
        {/if}

      </div>
    {/if}

    <audio
      bind:this={audioEl}
      src={reader.audioSrc}
      onended={handleAudioEnded}
      ontimeupdate={handleAudioTimeUpdate}
      preload="auto"
      style="display: none;"
    ></audio>

  </main>

  <div class="reader-dock">
    {#if reader.pageState === 'empty'}
      <Dock state="idle" />
    {:else if reader.pageState === 'loaded'}
      <Dock
        state="ready"
        progress={0}
        current={0}
        total={totalChunks}
        voice={voiceLabel(reader.selectedVoice)}
        speed={reader.speed}
      />
    {:else}
      <Dock
        state={dockState(reader.pageState)}
        progress={dockProgress}
        current={reader.currentChunkIndex + 1}
        total={totalChunks}
        voice={voiceLabel(reader.selectedVoice)}
        speed={reader.speed}
        previewText={previewTitle}
        previewMeta={previewMeta}
        onPlayPause={() => reader.togglePlayPause()}
        onSkipForward={() => reader.skipForward()}
        onSkipBack={() => reader.skipBack()}
      />
    {/if}
  </div>
</div>
