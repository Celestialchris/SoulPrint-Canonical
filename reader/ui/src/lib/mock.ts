export const mockNotes = [
  {
    id: 42,
    content: "The architecture was correct. The implementation drifted...",
    tags: ["polyglot", "planning"],
    is_starred: false,
    timestamp: "2026-05-11T14:30:00Z",
    role: "assistant",
    provider: "chatgpt"
  },
  {
    id: 38,
    content: "Reader architecture decisions and the three-service split...",
    tags: ["reader", "architecture"],
    is_starred: true,
    timestamp: "2026-05-09T10:15:00Z",
    role: "assistant",
    provider: "claude"
  },
  {
    id: 31,
    content: "Gemini export format notes and provider normalization...",
    tags: ["gemini", "import"],
    is_starred: false,
    timestamp: "2026-05-07T08:00:00Z",
    role: "assistant",
    provider: "gemini"
  }
];

export const mockVoices = [
  { id: "nagato_ref.wav", name: "Nagato Ref", filename: "nagato_ref.wav" }
];

export const mockChunks = [
  {
    chunk_id: "c001", index: 1, kind: "paragraph", status: "ready",
    text: "I understand. Let’s slow this down. The important thing is not to panic."
  },
  {
    chunk_id: "c002", index: 2, kind: "paragraph", status: "ready",
    text: "We rebuild from the nearest stable point. Every system has one. The question is whether you can find it before the damage propagates further than your ability to recover."
  },
  {
    chunk_id: "c003", index: 3, kind: "paragraph", status: "active",
    text: "The architecture was correct. The implementation drifted. Those are different problems with different fixes."
  },
  {
    chunk_id: "c004", index: 4, kind: "paragraph", status: "generating",
    text: "Start with what you can verify. The test suite. The schema. The last known-good commit. Work forward from solid ground, not backward from the failure."
  },
  {
    chunk_id: "c005", index: 5, kind: "paragraph", status: "pending",
    text: "Document what you find. Not for anyone else. For the version of you that will be here at 2am wondering what you already checked."
  },
  {
    chunk_id: "c006", index: 6, kind: "paragraph", status: "pending",
    text: "This is recoverable. Almost everything is, if you stay methodical."
  }
];

export const mockLoadedNote = {
  id: 42,
  title: "SoulPrint polyglot plan notes",
  chunkCount: 6,
  estimatedMinutes: 4,
  voice: "nagato_ref"
};

export function laneColor(provider: string): string {
  const map: Record<string, string> = {
    chatgpt: "var(--lane-chatgpt)",
    claude:  "var(--lane-claude)",
    gemini:  "var(--lane-gemini)",
    grok:    "var(--lane-grok)"
  };
  return map[provider] ?? "rgba(24,22,20,0.18)";
}

export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

export function noteTitle(content: string): string {
  return content.split("\n")[0].slice(0, 80);
}
