"use client";

import { Guide } from "@/components/Guide";
import { PageHeader } from "@/components/PageHeader";
import { api } from "@/lib/api";
import type { Guide as GuideData, GuideQuestionResult } from "@/lib/types";
import { useEffect, useState } from "react";

export default function GuidePage() {
  const [guide, setGuide] = useState<GuideData | null>(null);
  const [results, setResults] = useState<Record<number, GuideQuestionResult>>({});
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loading, setLoading] = useState<number | "all" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .guide()
      .then(setGuide)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function analyze(questionNumber?: number) {
    setLoading(questionNumber ?? "all");
    setError(null);
    try {
      const report = await api.analyzeGuide(questionNumber);
      setResults((current) => {
        const next = { ...current };
        for (const item of report.questions) next[item.number] = item;
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setLoading(null);
    }
  }

  async function toggle(number: number) {
    const next = expanded === number ? null : number;
    setExpanded(next);
    if (next && !results[next]) await analyze(next);
  }

  if (!guide && !error) return <p className="text-muted">Loading interview guide…</p>;
  if (error && !guide) return <p className="text-conflict">{error}</p>;
  if (!guide) return null;

  return (
    <div>
      <PageHeader
        title="Interview Guide"
        subtitle="AI-generated answers grounded in the expert interviews."
        action={
          <button
            type="button"
            onClick={() => void analyze()}
            disabled={loading !== null}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-60"
          >
            {loading === "all" ? "Analyzing…" : "Analyze all questions"}
          </button>
        }
      />
      {error ? <p className="mb-4 text-sm text-conflict">{error}</p> : null}
      <Guide
        questions={guide.questions}
        results={results}
        expanded={expanded}
        loading={loading}
        onToggle={(number) => void toggle(number)}
      />
    </div>
  );
}
