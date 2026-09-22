const serverBase = process.env.API_BASE_URL ?? "http://127.0.0.1:8000/api";
const browserBase = "/backend";

function baseUrl() {
  return typeof window === "undefined" ? serverBase : browserBase;
}

type ApiErrorBody = {
  error?: { code?: string; message?: string };
  detail?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const raw = await response.text();
    throw new Error(readErrorMessage(raw, response.status));
  }
  return response.json() as Promise<T>;
}

function readErrorMessage(raw: string, status: number): string {
  try {
    const body = JSON.parse(raw) as ApiErrorBody;
    if (body.error?.message) return body.error.message;
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // The body is not JSON; fall through to the raw text.
  }
  return raw || `Request failed: ${status}`;
}

export const api = {
  health: () => request<import("./types").Corpus>("/health"),
  transcripts: () => request<import("./types").TranscriptSummary[]>("/transcripts"),
  transcript: (id: string) =>
    request<import("./types").TranscriptDetail>(`/transcripts/${id}`),
  guide: () => request<import("./types").Guide>("/guide"),
  analyzeGuide: (questionNumber?: number) =>
    request<import("./types").GuideReport>("/analysis/guide", {
      method: "POST",
      body: JSON.stringify(
        questionNumber ? { question_number: questionNumber } : {},
      ),
    }),
  themes: () => request<{ themes: import("./types").Theme[] }>("/analysis/themes"),
  differences: () =>
    request<{ differences: import("./types").Difference[] }>("/analysis/differences"),
  ask: (question: string) =>
    request<import("./types").QAResponse>("/qa", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};

export { transcriptAnchor, transcriptHref as explorerHref } from "./ui";
