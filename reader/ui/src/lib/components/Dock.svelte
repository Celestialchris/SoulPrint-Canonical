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

<div class="dock" data-playing={state === 'playing'}>
  {#if state === 'idle'}
    <p class="dock-idle-text">Nothing loaded</p>
  {:else}
    <div class="dock-row">
      <div class="dock-zone-left">
        <div class="dock-transport">
          <button class="dock-btn" aria-label="Skip back">⏮</button>
          <button class="dock-btn primary play-pause {state === 'playing' ? 'active' : ''}" aria-label={state === 'playing' ? 'Pause' : 'Play'}>
            {state === 'playing' ? '❚❚' : '▶'}
          </button>
          <button class="dock-btn" aria-label="Skip forward">⏭</button>
        </div>
      </div>

      <div class="dock-zone-center">
        <div class="dock-groove-wrap">
          <div class="dock-groove">
            <div class="dock-fill" style="width: {progress}%"></div>
          </div>
        </div>
        <div class="dock-info">
          {#if state === 'playing'}
            {current} of {total} · {voice} · {speed.toFixed(1)}x
          {:else}
            Ready · {total} sections · {voice} · {speed.toFixed(1)}x
          {/if}
        </div>
      </div>

      <div class="dock-zone-right">
        {#if state === 'playing' && previewText}
          <div class="dock-preview-plate">
            <p class="dock-preview-text">{previewText}</p>
            {#if previewMeta}
              <p class="dock-preview-meta">{previewMeta}</p>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
