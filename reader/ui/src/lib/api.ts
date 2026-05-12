export const SOULPRINT_API = 'http://127.0.0.1:5000';
export const VOICEFORGE_API = 'http://127.0.0.1:5001';

export interface Note {
  id: number;
  content: string;
  tags: string[];
  is_starred: boolean;
  timestamp: string | null;
  role: string | null;
  provider: string | null;
}

export interface Voice {
  id: string;
  name: string;
  filename: string;
}

export type ChunkStatus = 'pending' | 'generating' | 'ready';
export type JobStatus = 'queued' | 'running' | 'complete' | 'error';

export interface JobChunk {
  chunk_id: string;
  status: ChunkStatus;
  audio_url: string | null;
}

export interface Job {
  job_id: string;
  status: JobStatus;
  voice: string;
  speed: number;
  total_chunks: number;
  current_chunk: number;
  error: string | null;
  chunks: JobChunk[];
}

export interface GenerationStart {
  job_id: string;
  status: 'queued';
  total_chunks: number;
}

export class ServiceError extends Error {
  service: 'soulprint' | 'voiceforge';
  status: number;
  constructor(service: 'soulprint' | 'voiceforge', status: number, message: string) {
    super(message);
    this.name = 'ServiceError';
    this.service = service;
    this.status = status;
  }
}

async function getJson<T>(
  url: string,
  service: 'soulprint' | 'voiceforge',
  init?: RequestInit
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'network failure';
    throw new ServiceError(service, 0, message);
  }
  if (!response.ok) {
    const body = await response.text().catch(() => '');
    let detail = body;
    try {
      const parsed: unknown = body ? JSON.parse(body) : null;
      if (parsed && typeof parsed === 'object' && 'detail' in parsed) {
        const d = (parsed as { detail: unknown }).detail;
        if (typeof d === 'string') detail = d;
      }
    } catch {
      // body wasn't JSON; keep raw text
    }
    throw new ServiceError(service, response.status, detail || response.statusText);
  }
  return (await response.json()) as T;
}

export function fetchNotes(): Promise<Note[]> {
  return getJson<Note[]>(`${SOULPRINT_API}/api/notes`, 'soulprint');
}

export function fetchVoices(): Promise<Voice[]> {
  return getJson<Voice[]>(`${VOICEFORGE_API}/voices`, 'voiceforge');
}

export function startGeneration(
  text: string,
  voice: string,
  speed: number
): Promise<GenerationStart> {
  return getJson<GenerationStart>(`${VOICEFORGE_API}/generate`, 'voiceforge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice, speed })
  });
}

export function pollJob(jobId: string): Promise<Job> {
  return getJson<Job>(`${VOICEFORGE_API}/jobs/${encodeURIComponent(jobId)}`, 'voiceforge');
}
