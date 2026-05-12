<script lang="ts">
  interface Props {
    size?: number;
  }
  let { size = 64 }: Props = $props();
</script>

<!--
  Archive compass + memory fingerprint.
  Outer ring, four cardinal tick marks, concentric inner grooves, north diamond.
  Uses currentColor — inherits text color of container.
-->
<svg
  width={size}
  height={size}
  viewBox="0 0 100 100"
  xmlns="http://www.w3.org/2000/svg"
  aria-hidden="true"
  fill="none"
>
  <!-- Outer ring -->
  <circle cx="50" cy="50" r="44" stroke="currentColor" stroke-width="1.5" />

  <!-- Cardinal tick marks crossing the ring (N, S, E, W) -->
  <line x1="50" y1="10" x2="50" y2="2"  stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
  <line x1="50" y1="90" x2="50" y2="98" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
  <line x1="10" y1="50" x2="2"  y2="50" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
  <line x1="90" y1="50" x2="98" y2="50" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />

  <!-- Inner memory grooves (concentric arcs suggesting a fingerprint record) -->
  <circle cx="50" cy="50" r="34" stroke="currentColor" stroke-width="1.0" opacity="0.55" />
  <circle cx="50" cy="50" r="26" stroke="currentColor" stroke-width="1.0" opacity="0.45" />
  <circle cx="50" cy="50" r="18" stroke="currentColor" stroke-width="1.0" opacity="0.35" />
  <circle cx="50" cy="50" r="10" stroke="currentColor" stroke-width="1.0" opacity="0.25" />

  <!-- Diamond at north cardinal point -->
  <polygon points="50,0 53.5,3 50,6 46.5,3" fill="currentColor" />
</svg>
