import {
  fetchNotes,
  fetchVoices,
  pollJob,
  startGeneration,
  VOICEFORGE_API,
  type Job,
  type JobChunk,
  type Note,
  type Voice
} from './api';

export type PageState = 'empty' | 'loaded' | 'listening';

export interface ReaderState {
  notes: Note[];
  voices: Voice[];
  selectedNote: Note | null;
  selectedVoice: string;
  speed: number;

  job: Job | null;
  chunks: JobChunk[];

  currentChunkIndex: number;
  isPlaying: boolean;
  audioDuration: number;
  audioCurrentTime: number;
  audioSrc: string;

  isLoadingNotes: boolean;
  isLoadingVoices: boolean;
  notesError: string | null;
  voicesError: string | null;
  generationError: string | null;

  readonly pageState: PageState;
  readonly overallProgress: number;
  readonly readyChunkCount: number;

  loadInitial(): Promise<void>;
  selectNote(note: Note): void;
  setVoice(filename: string): void;
  setSpeed(value: number): void;
  startReading(): Promise<void>;
  togglePlayPause(): void;
  skipForward(): void;
  skipBack(): void;
  resetJob(): void;
  updateAudioTime(time: number, duration: number): void;
  onChunkEnded(): void;
  registerAudio(el: HTMLAudioElement | null): void;
  cleanup(): void;
}

const POLL_INTERVAL_MS = 1000;

export function createReaderState(): ReaderState {
  // Backing state — all reactive via $state runes.
  let notes = $state<Note[]>([]);
  let voices = $state<Voice[]>([]);
  let selectedNote = $state<Note | null>(null);
  let selectedVoice = $state<string>('');
  let speed = $state<number>(1.0);

  let job = $state<Job | null>(null);
  let chunks = $state<JobChunk[]>([]);

  let currentChunkIndex = $state<number>(0);
  let isPlaying = $state<boolean>(false);
  let audioDuration = $state<number>(0);
  let audioCurrentTime = $state<number>(0);
  let audioSrc = $state<string>('');

  let isLoadingNotes = $state<boolean>(false);
  let isLoadingVoices = $state<boolean>(false);
  let notesError = $state<string | null>(null);
  let voicesError = $state<string | null>(null);
  let generationError = $state<string | null>(null);

  // Internal, non-reactive bookkeeping.
  let pollHandle: ReturnType<typeof setInterval> | null = null;
  let audioEl: HTMLAudioElement | null = null;
  let pendingAutoPlay = false; // set when onChunkEnded waits for next chunk to become ready
  // Identity of the job whose responses we still want to apply. Cleared on
  // selectNote/resetJob so an in-flight pollJob() that resolves after a switch
  // cannot overwrite the now-current job's state.
  let activeJobId: string | null = null;
  // One-shot latch for chunk-0 auto-play. Polls keep arriving while a user is
  // paused; without this latch, every successful poll would see "first chunk
  // ready, nothing playing" and restart playback from the top.
  let hasAutoStarted = false;

  // Derived values.
  const pageStateDerived = $derived<PageState>(
    selectedNote === null ? 'empty' : job === null ? 'loaded' : 'listening'
  );
  const readyChunkCountDerived = $derived(
    chunks.filter((c) => c.status === 'ready').length
  );
  const overallProgressDerived = $derived<number>(
    chunks.length === 0 ? 0 : Math.round((readyChunkCountDerived / chunks.length) * 100)
  );

  function stopPolling(): void {
    if (pollHandle !== null) {
      clearInterval(pollHandle);
      pollHandle = null;
    }
  }

  function resolveAudioUrl(chunk: JobChunk): string {
    if (!chunk.audio_url) return '';
    return `${VOICEFORGE_API}${chunk.audio_url}`;
  }

  function loadChunkIntoAudio(index: number): void {
    const chunk = chunks[index];
    if (!chunk || chunk.status !== 'ready' || !chunk.audio_url) return;
    audioSrc = resolveAudioUrl(chunk);
    // The <audio> element picks up the new src via Svelte binding;
    // we trigger play() once the consumer has flushed the DOM.
    queueMicrotask(() => {
      if (audioEl && audioSrc) {
        audioEl.play().catch(() => {
          // Autoplay can be blocked until first user gesture.
          isPlaying = false;
        });
      }
    });
    isPlaying = true;
  }

  function tryAutoStart(): void {
    if (hasAutoStarted) return;
    if (chunks.length === 0) return;
    if (isPlaying) return;
    const first = chunks[0];
    if (first.status === 'ready') {
      hasAutoStarted = true;
      currentChunkIndex = 0;
      loadChunkIntoAudio(0);
    }
  }

  function resumeIfPendingAutoPlay(): void {
    if (!pendingAutoPlay) return;
    const chunk = chunks[currentChunkIndex];
    if (chunk && chunk.status === 'ready') {
      pendingAutoPlay = false;
      loadChunkIntoAudio(currentChunkIndex);
    }
  }

  async function pollOnce(jobId: string): Promise<void> {
    try {
      const next = await pollJob(jobId);
      if (jobId !== activeJobId) return; // user switched notes or reset; drop stale response
      job = next;
      chunks = next.chunks;
      if (next.status === 'error') {
        generationError = next.error ?? 'generation failed';
      }
      tryAutoStart();
      resumeIfPendingAutoPlay();
      if (next.status === 'complete' || next.status === 'error') {
        stopPolling();
      }
    } catch (err: unknown) {
      if (jobId !== activeJobId) return; // same stale guard for error responses
      const message = err instanceof Error ? err.message : 'poll failed';
      generationError = message;
      stopPolling();
    }
  }

  return {
    get notes() { return notes; },
    get voices() { return voices; },
    get selectedNote() { return selectedNote; },
    get selectedVoice() { return selectedVoice; },
    get speed() { return speed; },
    get job() { return job; },
    get chunks() { return chunks; },
    get currentChunkIndex() { return currentChunkIndex; },
    get isPlaying() { return isPlaying; },
    get audioDuration() { return audioDuration; },
    get audioCurrentTime() { return audioCurrentTime; },
    get audioSrc() { return audioSrc; },
    get isLoadingNotes() { return isLoadingNotes; },
    get isLoadingVoices() { return isLoadingVoices; },
    get notesError() { return notesError; },
    get voicesError() { return voicesError; },
    get generationError() { return generationError; },
    get pageState() { return pageStateDerived; },
    get overallProgress() { return overallProgressDerived; },
    get readyChunkCount() { return readyChunkCountDerived; },

    async loadInitial(): Promise<void> {
      isLoadingNotes = true;
      isLoadingVoices = true;
      notesError = null;
      voicesError = null;
      const [notesResult, voicesResult] = await Promise.allSettled([
        fetchNotes(),
        fetchVoices()
      ]);
      if (notesResult.status === 'fulfilled') {
        notes = notesResult.value;
      } else {
        const err = notesResult.reason;
        notesError = err instanceof Error ? err.message : 'failed to load notes';
      }
      if (voicesResult.status === 'fulfilled') {
        voices = voicesResult.value;
        if (voices.length > 0 && !selectedVoice) {
          selectedVoice = voices[0].filename;
        }
      } else {
        const err = voicesResult.reason;
        voicesError = err instanceof Error ? err.message : 'failed to load voices';
      }
      isLoadingNotes = false;
      isLoadingVoices = false;
    },

    selectNote(note: Note): void {
      // Switching notes resets any in-flight job state.
      stopPolling();
      activeJobId = null;
      hasAutoStarted = false;
      selectedNote = note;
      job = null;
      chunks = [];
      currentChunkIndex = 0;
      audioSrc = '';
      audioCurrentTime = 0;
      audioDuration = 0;
      isPlaying = false;
      generationError = null;
      pendingAutoPlay = false;
      if (audioEl) {
        audioEl.pause();
      }
    },

    setVoice(filename: string): void {
      selectedVoice = filename;
    },

    setSpeed(value: number): void {
      speed = value;
    },

    async startReading(): Promise<void> {
      // Cancel any prior in-flight generation up front, before any async work,
      // so a second click cleanly replaces the first instead of racing it.
      stopPolling();
      activeJobId = null;
      hasAutoStarted = false;
      if (!selectedNote) return;
      if (!selectedVoice) {
        generationError = 'no voice selected';
        return;
      }
      generationError = null;
      try {
        const start = await startGeneration(selectedNote.content, selectedVoice, speed);
        // Seed an empty job snapshot so pageState flips to 'listening' before the first poll.
        chunks = Array.from({ length: start.total_chunks }, (_, i) => ({
          chunk_id: `c${String(i + 1).padStart(3, '0')}`,
          status: 'pending',
          audio_url: null
        }));
        job = {
          job_id: start.job_id,
          status: start.status,
          voice: selectedVoice,
          speed,
          total_chunks: start.total_chunks,
          current_chunk: 0,
          error: null,
          chunks
        };
        currentChunkIndex = 0;
        // Mark this job as the only one whose poll responses are still welcome.
        activeJobId = start.job_id;
        // Begin polling immediately, then on interval.
        const jobId = start.job_id;
        await pollOnce(jobId);
        if (pollHandle === null) {
          pollHandle = setInterval(() => {
            void pollOnce(jobId);
          }, POLL_INTERVAL_MS);
        }
      } catch (err: unknown) {
        generationError = err instanceof Error ? err.message : 'failed to start generation';
      }
    },

    togglePlayPause(): void {
      if (!audioEl) return;
      if (isPlaying) {
        audioEl.pause();
        isPlaying = false;
      } else {
        // Resume current chunk, or kick off the first ready chunk.
        if (audioSrc) {
          audioEl.play().catch(() => {
            isPlaying = false;
          });
          isPlaying = true;
        } else {
          tryAutoStart();
        }
      }
    },

    skipForward(): void {
      const next = chunks.findIndex(
        (c, i) => i > currentChunkIndex && c.status === 'ready'
      );
      if (next === -1) return;
      currentChunkIndex = next;
      loadChunkIntoAudio(next);
    },

    skipBack(): void {
      // Find the highest-index ready chunk strictly below currentChunkIndex.
      let prev = -1;
      for (let i = 0; i < currentChunkIndex; i++) {
        if (chunks[i].status === 'ready') prev = i;
      }
      if (prev === -1) return;
      currentChunkIndex = prev;
      loadChunkIntoAudio(prev);
    },

    resetJob(): void {
      stopPolling();
      activeJobId = null;
      hasAutoStarted = false;
      job = null;
      chunks = [];
      currentChunkIndex = 0;
      audioSrc = '';
      audioCurrentTime = 0;
      audioDuration = 0;
      isPlaying = false;
      generationError = null;
      pendingAutoPlay = false;
      if (audioEl) {
        audioEl.pause();
      }
    },

    updateAudioTime(time: number, duration: number): void {
      audioCurrentTime = time;
      if (!Number.isNaN(duration) && duration > 0) {
        audioDuration = duration;
      }
    },

    onChunkEnded(): void {
      const nextIndex = currentChunkIndex + 1;
      if (nextIndex >= chunks.length) {
        // No more chunks to advance to — playback is done regardless of
        // whether the next poll has observed status === 'complete' yet.
        isPlaying = false;
        audioSrc = '';
        return;
      }
      const next = chunks[nextIndex];
      currentChunkIndex = nextIndex;
      if (next.status === 'ready') {
        loadChunkIntoAudio(nextIndex);
      } else {
        // Park here. resumeIfPendingAutoPlay() will start playback when the chunk becomes ready.
        pendingAutoPlay = true;
        isPlaying = false;
      }
    },

    registerAudio(el: HTMLAudioElement | null): void {
      audioEl = el;
    },

    cleanup(): void {
      stopPolling();
      if (audioEl) {
        audioEl.pause();
      }
      audioEl = null;
    }
  };
}
