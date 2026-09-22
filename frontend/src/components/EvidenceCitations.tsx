"use client";

import { CountryIcon } from "@/components/CountryIcon";
import { Icon } from "@/components/Icon";
import { evidenceHref, marketMeta } from "@/lib/ui";
import type { Evidence } from "@/lib/types";
import Link from "next/link";
import { useMemo } from "react";

const MARKET_ORDER = ["France", "Germany", "United Kingdom"];

export type EvidenceSource = {
  key: string;
  index: number;
  market: string;
  expert: string;
  role: string;
  items: Evidence[];
};

export function groupEvidenceSources(evidence: Evidence[]): EvidenceSource[] {
  const byMarket = new Map<string, Evidence[]>();
  for (const item of evidence) {
    const current = byMarket.get(item.market) ?? [];
    current.push(item);
    byMarket.set(item.market, current);
  }
  const markets = [
    ...MARKET_ORDER.filter((market) => byMarket.has(market)),
    ...[...byMarket.keys()].filter((market) => !MARKET_ORDER.includes(market)),
  ];
  return markets.map((market, index) => {
    const items = byMarket.get(market) ?? [];
    return {
      key: market,
      index: index + 1,
      market,
      expert: items[0]?.expert ?? market,
      role: items[0]?.role ?? "",
      items,
    };
  });
}

export function CitationMarks({
  sources,
  activeKey,
  onSelect,
}: {
  sources: EvidenceSource[];
  activeKey: string | null;
  onSelect: (key: string) => void;
}) {
  if (!sources.length) return null;
  return (
    <span className="ml-1 inline-flex items-center gap-1 align-middle">
      {sources.map((source) => {
        const selected = activeKey === source.key;
        return (
          <button
            key={source.key}
            type="button"
            aria-pressed={selected}
            aria-label={`Show ${source.expert} quote`}
            onClick={(event) => {
              event.stopPropagation();
              onSelect(source.key);
            }}
            className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[11px] font-semibold leading-none ${
              selected
                ? "bg-accent text-white"
                : "bg-accent-soft text-accent hover:bg-accent/15"
            }`}
          >
            {source.index}
          </button>
        );
      })}
    </span>
  );
}

export function EvidenceCitations({
  evidence,
  activeKey,
  onSelect,
  conflictingIds = [],
}: {
  evidence: Evidence[];
  activeKey: string | null;
  onSelect: (key: string) => void;
  conflictingIds?: string[];
}) {
  const sources = useMemo(() => groupEvidenceSources(evidence), [evidence]);
  const active = sources.find((source) => source.key === activeKey) ?? null;
  const conflictSet = useMemo(() => new Set(conflictingIds), [conflictingIds]);

  if (!sources.length) {
    return <p className="text-sm text-caution">No transcript quotes were attached.</p>;
  }

  return (
    <div className="grid gap-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Sources</p>
      <div className="flex flex-wrap gap-2">
        {sources.map((source) => {
          const selected = activeKey === source.key;
          const meta = marketMeta(source.market);
          return (
            <button
              key={source.key}
              type="button"
              aria-pressed={selected}
              onClick={() => onSelect(source.key)}
              className={`source-pill inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition ${
                selected
                  ? "border-accent bg-accent-soft text-ink"
                  : "border-line bg-bg text-ink-secondary hover:border-accent hover:text-ink"
              }`}
            >
              <span
                className={`source-pill-index inline-flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-semibold ${
                  selected ? "bg-accent text-white" : "bg-line text-ink-secondary"
                }`}
              >
                {source.index}
              </span>
              <CountryIcon market={source.market} className="source-pill-flag h-3.5 w-5" />
              <span className="font-medium">{meta.code}</span>
              <span className="hidden text-muted sm:inline">{source.expert}</span>
            </button>
          );
        })}
      </div>
      {active ? (
        <div className="grid gap-3">
          {active.items.map((item) => (
            <article key={item.evidence_id} className="rounded-xl border border-line bg-bg p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold tracking-[0.14em] text-muted">
                    {marketMeta(item.market).flag} {item.market.toUpperCase()}
                  </p>
                  <p className="mt-1 text-sm font-medium text-ink">
                    {item.expert}
                    <span className="font-normal text-muted"> · {item.role}</span>
                  </p>
                  {conflictSet.has(item.evidence_id) ? (
                    <p className="mt-1 text-xs font-medium text-conflict">Conflicting evidence</p>
                  ) : null}
                </div>
                <p className="font-mono text-xs text-muted">{item.timestamp}</p>
              </div>
              <blockquote className="quote mt-3 text-sm leading-relaxed">“{item.quote}”</blockquote>
              <Link
                href={evidenceHref(item)}
                className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-accent hover:text-accent-hover"
              >
                Open transcript
                <Icon name="arrow" className="h-3.5 w-3.5" />
              </Link>
            </article>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted">Select a source to view that expert’s original quote.</p>
      )}
    </div>
  );
}
