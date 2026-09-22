import { evidenceHref, marketMeta } from "@/lib/ui";
import type { Evidence } from "@/lib/types";
import Link from "next/link";

export function CitationBadge({ evidence }: { evidence: Evidence }) {
  const meta = marketMeta(evidence.market);
  return (
    <Link
      href={evidenceHref(evidence)}
      className="inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-2.5 py-1 text-xs font-medium text-accent hover:bg-accent/10"
    >
      <span>{meta.flag}</span>
      {meta.code} · {evidence.timestamp}
    </Link>
  );
}
