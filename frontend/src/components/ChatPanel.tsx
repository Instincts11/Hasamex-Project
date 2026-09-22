"use client";

import {
  CitationMarks,
  EvidenceCitations,
  groupEvidenceSources,
} from "@/components/EvidenceCitations";
import { api } from "@/lib/api";
import type { QAResponse } from "@/lib/types";
import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useMemo, useRef, useState, useEffect } from "react";

const SUGGESTIONS = [
  "What are the main barriers to adoption?",
  "How do purchase timelines differ across markets?",
  "What role does training play?",
  "What are the experts' growth expectations?",
  "Where do experts disagree?",
  "What factors influence ROI?",
];

function ChatPanelInner() {
  const searchParams = useSearchParams();
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<{ question: string; result: QAResponse }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const seeded = useRef(false);

  async function ask(nextQuestion: string) {
    const trimmed = nextQuestion.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.ask(trimmed);
      setTurns((current) => [...current, { question: trimmed, result }]);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const incoming = searchParams.get("q");
    if (!incoming || seeded.current) return;
    seeded.current = true;
    void ask(incoming);
  }, [searchParams]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void ask(question);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col pb-24">
      {!turns.length ? (
        <div className="card px-6 py-10 text-center">
          <p className="text-[11px] font-semibold tracking-[0.18em] text-accent">ASK THE CALLS</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-tight">Ask the expert calls anything.</h3>
          <p className="mx-auto mt-2 max-w-lg text-sm text-ink-secondary">
            Answers are grounded in the provided transcripts. Quotes are retrieved, never generated.
          </p>
          <div className="mt-6 grid gap-2 text-left sm:grid-cols-2">
            {SUGGESTIONS.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => void ask(item)}
                disabled={loading}
                className="rounded-xl border border-line bg-bg px-4 py-3 text-sm text-ink-secondary hover:border-accent hover:text-ink disabled:opacity-60"
              >
                “{item}”
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 space-y-6 pb-4">
          {turns.map((turn, index) => (
            <article key={`${turn.question}-${index}`} className="space-y-4">
              <div className="rounded-xl bg-bg-subtle px-5 py-4">
                <p className="text-[11px] font-semibold tracking-[0.16em] text-muted">USER QUESTION</p>
                <p className="mt-1 font-medium">{turn.question}</p>
              </div>
              <AskTurn result={turn.result} />
            </article>
          ))}
        </div>
      )}

      <form onSubmit={onSubmit} className="ask-composer">
        <div className="card flex items-center gap-2 p-2">
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask anything about the expert calls..."
            disabled={loading}
            className="flex-1 rounded-lg bg-transparent px-3 py-3 text-sm outline-none placeholder:text-muted"
          />
          <button
            type="submit"
            disabled={loading}
            aria-label={loading ? "Analyzing" : "Send"}
            className="send-btn"
          >
            <img src="/send_icon.png" alt="" />
          </button>
        </div>
        {error ? <p className="mt-2 text-sm text-conflict">{error}</p> : null}
      </form>
    </div>
  );
}

function AskTurn({ result }: { result: QAResponse }) {
  const sources = useMemo(() => groupEvidenceSources(result.evidence), [result.evidence]);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const selectedKey = sources.some((source) => source.key === activeKey) ? activeKey : null;

  function selectSource(key: string) {
    setActiveKey((current) => (current === key ? null : key));
  }

  return (
    <>
      <div className="card p-5">
        <p className="text-[11px] font-semibold tracking-[0.16em] text-accent">AI ANSWER</p>
        <p className="mt-2 leading-relaxed text-ink-secondary">
          {result.answer}
          <CitationMarks sources={sources} activeKey={selectedKey} onSelect={selectSource} />
        </p>
      </div>
      {result.evidence.length ? (
        <EvidenceCitations
          evidence={result.evidence}
          activeKey={selectedKey}
          onSelect={selectSource}
        />
      ) : (
        <p className="text-sm text-caution">
          No transcript quotes were attached. The model was not allowed to invent a source.
        </p>
      )}
    </>
  );
}

export function ChatPanel() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <Suspense fallback={<p className="text-sm text-muted">Loading Ask the Calls…</p>}>
        <ChatPanelInner />
      </Suspense>
    </div>
  );
}
