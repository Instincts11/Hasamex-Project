"use client";

import {
  CitationMarks,
  EvidenceCitations,
  groupEvidenceSources,
} from "@/components/EvidenceCitations";
import type { Difference } from "@/lib/types";
import { useMemo, useState } from "react";

function kindLabel(difference: Difference) {
  const markets = difference.positions.map((item) => item.market);
  if (markets.length <= 1) return { label: "Single-expert observation", tone: "single" };
  const scopes = difference.positions.map((item) => item.scope).filter(Boolean);
  if (scopes.length) return { label: "Different estimates / scope", tone: "partial" };
  return { label: "Different emphasis", tone: "partial" };
}

export function DifferenceCard({
  difference,
  expanded,
  onToggle,
}: {
  difference: Difference;
  expanded: boolean;
  onToggle: () => void;
}) {
  const kind = kindLabel(difference);
  const evidence = useMemo(
    () => difference.positions.flatMap((position) => position.evidence),
    [difference.positions],
  );
  const sources = useMemo(() => groupEvidenceSources(evidence), [evidence]);
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
        className="flex w-full items-start justify-between gap-4 px-6 py-5 text-left hover:bg-surface-hover max-[600px]:flex-col max-[600px]:items-start max-[600px]:gap-3 max-[600px]:px-4 max-[600px]:py-4"
      >
        <div>
          <h3 className="text-lg font-semibold tracking-tight">{difference.topic}</h3>
          {!expanded ? (
            <p className="mt-2 text-sm text-muted">Expand to view the analysis and sources.</p>
          ) : null}
        </div>
        <span
          className={`coverage-pill inline-flex shrink-0 items-center rounded-full px-2.5 py-1 text-xs font-medium ${
            kind.tone === "single"
              ? "bg-conflict-soft text-conflict"
              : "bg-caution-soft text-caution"
          }`}
        >
          {kind.label}
        </span>
      </button>
      {expanded ? (
        <div className="border-t border-line px-6 py-5">
          <div className="grid gap-5">
            <p className="text-sm leading-relaxed text-ink-secondary">
              {difference.summary}
              <CitationMarks sources={sources} activeKey={selectedKey} onSelect={selectSource} />
            </p>
            <EvidenceCitations
              evidence={evidence}
              activeKey={selectedKey}
              onSelect={selectSource}
            />
          </div>
        </div>
      ) : null}
    </section>
  );
}
