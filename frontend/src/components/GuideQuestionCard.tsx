"use client";

import {
  CitationMarks,
  EvidenceCitations,
  groupEvidenceSources,
} from "@/components/EvidenceCitations";
import { EvidenceCoverage } from "@/components/EvidenceCoverage";
import type { GuideQuestionResult } from "@/lib/types";
import { useMemo, useState } from "react";

export function GuideQuestionCard({
  questionNumber,
  questionText,
  result,
  loading,
  expanded,
  onToggle,
}: {
  questionNumber: number;
  questionText: string;
  result?: GuideQuestionResult;
  loading?: boolean;
  expanded: boolean;
  onToggle: () => void;
}) {
  const sources = useMemo(
    () => (result ? groupEvidenceSources(result.evidence) : []),
    [result],
  );
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const selectedKey = sources.some((source) => source.key === activeKey) ? activeKey : null;

  function selectSource(key: string) {
    setActiveKey((current) => (current === key ? null : key));
    if (!expanded) onToggle();
  }

  return (
    <section className="card overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        disabled={loading}
        className="flex w-full items-start justify-between gap-4 px-6 py-5 text-left hover:bg-surface-hover disabled:opacity-60 max-[600px]:flex-col max-[600px]:items-start max-[600px]:gap-3 max-[600px]:px-4 max-[600px]:py-4"
      >
        <div>
          <p className="text-[11px] font-semibold tracking-[0.16em] text-muted">Q{questionNumber}</p>
          <h3 className="mt-1 text-base font-semibold tracking-tight md:text-lg">{questionText}</h3>
          {!result ? (
            <p className="mt-3 text-sm text-muted">
              {loading ? "Retrieving grounded evidence…" : "Expand to generate a grounded answer."}
            </p>
          ) : !expanded ? (
            <p className="mt-3 text-sm text-muted">Answer ready — expand to view sources.</p>
          ) : null}
        </div>
        {result ? (
          <EvidenceCoverage covered={result.experts_covered} total={result.experts_total} />
        ) : null}
      </button>
      {expanded ? (
        <div className="border-t border-line px-6 py-5">
          {loading && !result ? <p className="text-sm text-muted">Analyzing across all three calls…</p> : null}
          {result ? (
            <div className="grid gap-5">
              <p className="text-sm leading-relaxed text-ink-secondary">
                {result.answer}
                <CitationMarks sources={sources} activeKey={selectedKey} onSelect={selectSource} />
              </p>
              <EvidenceCitations
                evidence={result.evidence}
                activeKey={selectedKey}
                onSelect={selectSource}
              />
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
