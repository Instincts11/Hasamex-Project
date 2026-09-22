import { CountryIcon } from "@/components/CountryIcon";
import { Icon } from "@/components/Icon";
import { transcriptHref } from "@/lib/ui";
import type { TranscriptSummary } from "@/lib/types";
import Link from "next/link";

export function ExpertCard({
  transcript,
  quote,
  timestamp,
  onOpen,
  selected,
}: {
  transcript: TranscriptSummary;
  quote?: string;
  timestamp?: string;
  onOpen?: () => void;
  selected?: boolean;
}) {
  const body = (
    <>
      <div className="h-1 bg-accent" />
      <div className="flex flex-1 flex-col p-5">
        <p className="flex items-center gap-2 text-[11px] font-semibold tracking-[0.16em] text-muted">
          <CountryIcon market={transcript.market} />
          {transcript.market.toUpperCase()}
        </p>
        <h3 className="mt-2 text-lg font-semibold tracking-tight">{transcript.expert}</h3>
        <p className="expert-card-role text-sm text-muted">{transcript.role}</p>
        {quote ? (
          <p className="expert-card-quote mt-4 text-sm leading-relaxed text-ink-secondary">“{quote}”</p>
        ) : null}
        <div className="expert-card-meta mt-auto flex items-center justify-between gap-3 pt-4 text-xs text-muted">
          <span className="inline-flex items-center gap-1.5">
            <Icon name="file" className="expert-card-icon h-3.5 w-3.5" />
            Transcript ready
          </span>
          <span>
            {transcript.evidence_count} evidence · {transcript.segment_count} turns
          </span>
        </div>
        {onOpen ? (
          <span className="expert-card-action mt-4 inline-flex items-center gap-1 text-sm font-medium text-accent">
            {selected ? "Hide transcript" : "View transcript"}
            <Icon name={selected ? "close" : "arrow"} className="expert-card-icon h-3.5 w-3.5" />
          </span>
        ) : (
          <Link
            href={transcriptHref(transcript.transcript_id, timestamp)}
            className="expert-card-action mt-4 inline-flex items-center gap-1 text-sm font-medium text-accent hover:text-accent-hover"
          >
            View transcript
            <Icon name="arrow" className="expert-card-icon h-3.5 w-3.5" />
          </Link>
        )}
      </div>
    </>
  );

  const selectedClass = selected
    ? "ring-2 ring-accent shadow-[0_0_0_4px_var(--accent-ring)]"
    : "";

  if (onOpen) {
    return (
      <button
        type="button"
        onClick={onOpen}
        className={`card flex h-full min-w-0 w-full flex-col overflow-hidden text-left ${selectedClass}`}
      >
        {body}
      </button>
    );
  }

  return <article className="card flex h-full min-w-0 w-full flex-col overflow-hidden">{body}</article>;
}
