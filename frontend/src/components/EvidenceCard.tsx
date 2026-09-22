import { Icon } from "@/components/Icon";
import { evidenceHref, marketMeta } from "@/lib/ui";
import type { Evidence } from "@/lib/types";
import Link from "next/link";

export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  const meta = marketMeta(evidence.market);
  return (
    <article className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold tracking-[0.14em] text-muted">
            {meta.flag} {evidence.market.toUpperCase()}
          </p>
          <p className="mt-1 text-sm font-medium text-ink">
            {evidence.expert}
            <span className="font-normal text-muted"> · {evidence.role}</span>
          </p>
        </div>
        <p className="font-mono text-xs text-muted">{evidence.timestamp}</p>
      </div>
      <blockquote className="quote mt-3 text-sm leading-relaxed">“{evidence.quote}”</blockquote>
      <Link
        href={evidenceHref(evidence)}
        className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-accent hover:text-accent-hover"
      >
        Open transcript
        <Icon name="arrow" className="h-3.5 w-3.5" />
      </Link>
    </article>
  );
}
