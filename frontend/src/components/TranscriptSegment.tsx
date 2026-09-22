import type { Segment } from "@/lib/types";

export function TranscriptSegment({
  segment,
  active,
  onSelect,
}: {
  segment: Segment;
  active?: boolean;
  onSelect?: () => void;
}) {
  const interviewer = segment.speaker === "Interviewer";
  return (
    <button
      type="button"
      id={segment.timestamp ? `ts-${segment.timestamp.replaceAll(":", "-")}` : segment.segment_id}
      onClick={onSelect}
      className={`w-full scroll-mt-28 rounded-xl border px-4 py-3 text-left transition ${
        active
          ? "segment-active"
          : interviewer
            ? "border-transparent bg-transparent"
            : "border-line bg-surface hover:border-line-strong"
      }`}
    >
      <div className="flex items-baseline justify-between gap-3 text-xs">
        <span className={interviewer ? "text-muted" : "font-medium text-ink"}>{segment.speaker}</span>
        <span className="font-mono text-muted">{segment.timestamp_display}</span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{segment.text}</p>
    </button>
  );
}
