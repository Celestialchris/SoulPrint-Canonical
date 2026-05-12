<script lang="ts">
  interface Props {
    state: 'idle' | 'ready' | 'playing';
    progress?: number;
    current?: number;
    total?: number;
    voice?: string;
    speed?: number;
    previewText?: string;
    previewMeta?: string;
  }

  let {
    state,
    progress = 0,
    current = 0,
    total = 0,
    voice = '',
    speed = 1.0,
    previewText = '',
    previewMeta = ''
  }: Props = $props();
</script>

<div class="dock">
  {#if state === 'idle'}
    <p class="dock-idle-text">Nothing loaded</p>
  {:else}
    <div class="dock-transport">
      <button class="dock-btn" aria-label="Skip back">⏮</button>
      <button class="dock-btn primary {state === 'playing' ? 'active' : ''}" aria-label={state === 'playing' ? 'Pause' : 'Play'}>
        {state === 'playing' ? '❚❚' : '▶'}
      </button>
      <button class="dock-btn" aria-label="Skip forward">⏭</button>
    </div>

    <div class="dock-groove-wrap">
      <div class="dock-groove">
        <div class="dock-fill" style="width: {progress}%"></div>
      </div>
    </div>

    <div class="dock-info">
      <span class="dock-info-left">
        {#if state === 'playing'}
          {current} of {total}
        {:else}
          Ready · {total} sections
        {/if}
      </span>
      <span class="dock-info-right">
        {voice} · {speed.toFixed(1)}x
      </span>
    </div>

    {#if state === 'playing' && previewText}
      <div class="dock-preview">
        <p class="dock-preview-text">{previewText}</p>
        {#if previewMeta}
          <p class="dock-preview-meta">{previewMeta}</p>
        {/if}
      </div>
    {/if}
  {/if}
</div>
