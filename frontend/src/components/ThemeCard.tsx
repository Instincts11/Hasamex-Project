"use client";

import {
  CitationMarks,
  EvidenceCitations,
  groupEvidenceSources,
} from "@/components/EvidenceCitations";
import { EvidenceCoverage } from "@/components/EvidenceCoverage";
import type { Theme } from "@/lib/types";
import { useMemo, useState } from "react";

export function ThemeCard({
  theme,
  expanded,
  onToggle,
}: {
  theme: Theme;
  expanded: boolean;
  onToggle: () => void;
}) {
  const evidence = useMemo(
    () => [...theme.supporting, ...theme.conflicting],
    [theme.conflicting, theme.supporting],
  );
  const sources = useMemo(() => groupEvidenceSources(evidence), [evidence]);
  const conflictingIds = useMemo(
    () => theme.conflicting.map((item) => item.evidence_id),
    [theme.conflicting],
  );
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const selectedKey = sources.some((source) => source.key === activeKey) ? activeKey : null;
  const covered = theme.single_expert
    ? 1
    : new Set(theme.supporting.map((item) => item.market)).size || 1;

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
          <h3 className="text-lg font-semibold tracking-tight">{theme.name}</h3>
          {!expanded ? (
            <p className="mt-2 text-sm text-muted">Expand to view the theme and sources.</p>
          ) : null}
        </div>
        <EvidenceCoverage
          covered={theme.single_expert ? 1 : covered}
          total={3}
          singleExpert={theme.single_expert}
        />
      </button>
      {expanded ? (
        <div className="border-t border-line px-6 py-5">
          <div className="grid gap-5">
            <p className="text-sm leading-relaxed text-ink-secondary">
              {theme.summary}
              <CitationMarks sources={sources} activeKey={selectedKey} onSelect={selectSource} />
            </p>
            <EvidenceCitations
              evidence={evidence}
              activeKey={selectedKey}
              onSelect={selectSource}
              conflictingIds={conflictingIds}
            />
          </div>
        </div>
      ) : null}
    </section>
  );
}
